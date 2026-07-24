# Access Control & Data Security Plan

## Groups and permissions

Two Django `Group`s are created automatically the first time migrations run
(see `ecommerce/apps.py`, hooked to the `post_migrate` signal):

- **Vendors** - `add_store`, `change_store`, `delete_store`, `view_store`,
  `add_product`, `change_product`, `delete_product`, `view_product`
- **Buyers** - `view_product`, `add_review`

A new account is added to the matching group at registration time based on
the `account_type` field the user chose, mirroring
`user.groups.add(user_group)` from the task material.

## Two layers of restriction

Django permissions are a *flag*, not an automatic restriction - the task
material stresses this - so every vendor view enforces **two** checks:

1. `@login_required` + `@permission_required("ecommerce.<action>_<model>")`
   - confirms the user is authenticated and that their role (group) is
   allowed to perform this kind of action at all.
2. An explicit **ownership check** (`store.vendor == request.user`) before
   any store or product is read/changed/deleted - so one vendor can never
   edit or delete another vendor's data, even though both belong to the
   `Vendors` group with identical permissions. Attempting this raises
   `PermissionDenied` (HTTP 403).

Buyer-only actions (adding a review, checking out, adding to cart) are
behind `@login_required` and, for reviews, `@permission_required`.
Product **browsing** is intentionally left open to anonymous visitors, since
letting people window-shop without an account is normal for an eCommerce
site and does not expose any sensitive data.

## Session security

- `django.contrib.sessions.middleware.SessionMiddleware` is enabled.
- The shopping cart lives entirely in `request.session["cart"]`
  (product_id -> quantity), so it survives across requests and, per the
  task material, across the anonymous-to-logged-in transition, without a
  database table.
- Logging out clears the session (Django's built-in `logout()` behaviour),
  which also empties the cart - this is a deliberate, expected trade-off:
  a shared/public computer should not retain a previous user's cart.
- Password-reset "which user, which token" state is also kept in the
  session only for the short hop between confirming a token and submitting
  the new password, and is deleted immediately after use.

## Password & token security

- Django's `User.objects.create_user()` / `set_password()` are used
  everywhere, so passwords are always stored using Django's PBKDF2 hash -
  plaintext passwords are never written to the database.
- Password-reset tokens are generated with Python's `secrets` module
  (cryptographically secure), then **hashed with SHA-1 before being stored**
  in the `ResetToken` table - the raw token only ever exists in the emailed
  URL, not in the database, mirroring the technique shown in the task
  material.
- Tokens expire after `PASSWORD_RESET_TIMEOUT_MINUTES` (5 minutes by
  default) and are deleted once expired or once successfully used, so a
  token can never be replayed.
- The "forgot password" endpoint always shows the same confirmation
  message whether or not the submitted email matches an account, to avoid
  leaking which addresses are registered.

## CSRF & forms

Every state-changing request (register, login, store/product CRUD, cart
add/remove, checkout, review, password change) is a POST request rendered
through Django's `{% csrf_token %}`, so Django's CSRF middleware protects
all of them by default.

## Database credentials

Database and email credentials are read from environment variables rather
than hard-coded in `settings.py` (see `README.md`), so real
passwords/API keys never need to be committed to source control.
