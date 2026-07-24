# Planning for Failure

| Scenario | System behaviour |
|---|---|
| User submits invalid registration data (duplicate username, mismatched passwords, weak password) | Form re-renders with field-level and form-level error messages; no user is created; Django's `AUTH_PASSWORD_VALIDATORS` reject common/short/numeric-only passwords. |
| Login credentials are wrong | `authenticate()` returns `None`; the login form re-renders with a generic "Incorrect username or password" error (deliberately generic, so it does not reveal whether the username exists). |
| A vendor tries to edit/delete a store or product they do not own | The view raises `PermissionDenied`, which Django turns into an HTTP 403 page, even though the vendor holds the underlying `change_store`/`delete_store` permission. |
| A logged-out (anonymous) user tries to reach a `@login_required` view (e.g. add to cart, checkout, my stores) | Django redirects them to `/login/?next=<original-url>`, and login sends them back to where they were headed. |
| Buyer or vendor group permission is missing for an action (e.g. someone in the Buyers group tries to create a store) | `@permission_required(..., raise_exception=True)` returns HTTP 403 rather than silently failing or crashing. |
| Buyer checks out with an empty cart | Checkout redirects back to product browsing with a warning message instead of creating an empty order. |
| Buyer orders more of a product than is in stock | Stock is floored at zero rather than going negative (`max(0, product.stock - quantity)`); this is flagged in the code as a point that a production system would extend with a hard stock check before allowing checkout. |
| A product is deleted after being purchased | `OrderItem` stores a **snapshot** of the product's name and price at the time of purchase (and uses `on_delete=SET_NULL` for the product link), so historic orders and invoices remain readable even if the underlying `Product` row is later removed. |
| A password-reset link is old, already used, or tampered with | The raw token is hashed and looked up; the view distinguishes "not found" (invalid/tampered) from "found but expired" (deleted on the spot) and shows one unified "invalid or expired" message either way, then routes the user back to request a fresh link. |
| Invoice email fails to send (e.g. bad SMTP credentials in production) | Development/marking uses the console/file email backend so this failure mode does not block testing; for a real deployment this is the one place a future iteration would add a try/except and a retry or admin alert, noted in `README.md`. |
| Someone submits a review for a product without being logged in | `@login_required` on `add_review` redirects them to log in first; there is no way to submit a review as an anonymous visitor. |
| A user tries to view another buyer's order by guessing the order ID in the URL | `order_detail` checks `order.buyer == request.user` and raises `PermissionDenied` if not, rather than trusting the URL. |

## General approach

Wherever an action changes money-relevant state (stock levels, order
totals), it is wrapped in `transaction.atomic()` (see `checkout()` in
`views.py`) so that a failure partway through creating order line items
cannot leave the database in a half-updated state (e.g. stock reduced but
no order recorded).
