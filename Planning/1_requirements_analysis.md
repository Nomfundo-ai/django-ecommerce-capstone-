# Requirements Analysis - GrabMore eCommerce (Part 1)

## Users of the system

| User type | Description | Key needs |
|---|---|---|
| **Visitor (anonymous)** | Anyone browsing without an account | Browse products, view reviews, register |
| **Buyer** | A registered user who shops | Browse/search products, add items to a cart across multiple stores, check out, receive an emailed invoice, leave reviews, reset a forgotten password |
| **Vendor** | A registered user who sells | Create/edit/delete one or more stores, add/edit/delete/view their own products, reset a forgotten password |
| **Site administrator (superuser)** | Manages the platform | Use Django's built-in admin panel to inspect/manage users, groups, stores, products, orders and reviews |

## Functional requirements

1. A visitor can register as either a **Vendor** or a **Buyer**, choosing the
   account type at sign-up. Registration assigns the account to the matching
   Django `Group` (`Vendors` / `Buyers`), which carries the default
   permissions for that role.
2. A registered user can log in and log out. Sessions persist the user's
   identity and, for buyers, their in-progress shopping cart.
3. A vendor can create, view, edit and delete their own store(s), and add,
   view, edit and delete products that belong to their store(s). A vendor
   must not be able to modify another vendor's store or products, even if
   they hold the `Vendors` permission set (ownership is checked in addition
   to the permission flag).
4. A buyer can browse all products from all stores, search by name, add
   items from **different stores** to a single cart, and remove items from
   the cart.
5. On checkout, the system must: reduce stock for each purchased product,
   record the order and its line items, clear the buyer's cart, and email
   the buyer an invoice.
6. A buyer can leave a review on any product. If the reviewing buyer has a
   past order containing that product, the review is stored as **verified**;
   otherwise it is stored as **unverified**. Both types of review are shown,
   clearly labelled.
7. A user who forgets their password can request a reset link by email. The
   link embeds a single-use, time-limited token; following it lets the user
   set a new password. Expired or already-used tokens are rejected.
8. The system must use a relational database server (MariaDB/MySQL) rather
   than the SQLite default, and all model changes must go through Django's
   migration framework (`makemigrations` / `migrate`).
9. Access to vendor-only and buyer-only actions must be restricted using
   Django's authentication (`login_required`) and permission
   (`has_perm` / `permission_required`) system - not just hidden in the UI.

## Non-functional requirements

- Passwords are never stored or displayed in plain text; Django's built-in
  password hashing is used throughout.
- Every write action that modifies data (store/product changes, cart
  changes, checkout, review submission, password change) requires a POST
  request protected by Django's CSRF token.
- The UI should be usable without JavaScript, since the underlying task is
  about the Django backend, not a rich frontend.
