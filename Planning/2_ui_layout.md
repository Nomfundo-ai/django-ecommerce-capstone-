# UI / User-Interface Layout Plan

## Global layout

Every page shares a single `base.html` template with:

- A top navigation bar containing: site name/home link, "Browse products",
  and, for logged-in users, "My stores" (vendors only, permission-gated),
  "My orders", and a live cart item count ("Cart (3)"). The right side
  shows either "Log in / Register" or the current username and a "Log out"
  button.
- A message area directly under the nav bar that renders Django's `messages`
  framework (success/error/info/warning) so every action (e.g. "Product
  added", "Incorrect password") gives immediate feedback.
- A centred `container` with a max width, so the layout stays readable on
  both desktop and mobile screens.

## Page-by-page flow

1. **Home (`/`)** - a welcome banner plus a grid of the newest products,
   each linking to its detail page. This is the landing page for both new
   visitors and returning users.
2. **Register (`/register/`)** - a single form with username, email,
   password, confirm password, and an account-type radio choice
   (Buyer / Vendor). On success the user is logged straight in and
   redirected home, matching the flow described in the task material.
3. **Log in (`/login/`)** / **Log out** - a minimal username/password form,
   with a link to "Forgot your password?" and to registration.
4. **My stores (`/my-stores/`, vendors only)** - a card grid of the
   vendor's own stores with Edit / Delete / "Manage products" actions, and
   a "+ New store" button.
5. **Store products (`/stores/<id>/products/`)** - a table of the store's
   products with Edit / Delete / View actions and an "+ New product"
   button.
6. **Browse products (`/products/`)** - a searchable grid of every product
   from every store, open to anyone (no login required to browse).
7. **Product detail (`/products/<id>/`)** - full description, price, stock,
   average rating, an "Add to cart" form (quantity selector), and the
   review list with a "Leave a review" form underneath. Verified reviews
   are marked with a green "Verified purchase" badge; others show
   "Unverified".
8. **Cart (`/cart/`)** - a table of everything currently in the session
   cart (which may span several vendors' stores), with per-line "Remove"
   and a "Proceed to checkout" button.
9. **Checkout (`/checkout/`)** - a read-only summary of the cart and total,
   with a single "Place order" button; after submission the buyer lands on
   the order confirmation page and receives an emailed invoice.
10. **My orders / order detail** - a buyer's order history and a per-order
    invoice-style breakdown.
11. **Forgot password flow** - three simple pages: enter email → (email
    sent) → click emailed link → enter and confirm a new password.

## Design intent

The layout deliberately keeps to plain HTML forms and Django's own form
rendering (no JavaScript framework) so that the authentication, permission
and session mechanics required by the task are easy to see directly in the
rendered HTML and in view logic, rather than being hidden behind client-side
code.
