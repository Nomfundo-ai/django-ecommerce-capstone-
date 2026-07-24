# GrabMore eCommerce - Django Task (Part 1 + Part 2)

A Django implementation of:

- **Part 1**: authentication/authorisation, sessions (shopping cart),
  permissions & groups, database migration, and forgot-password.
- **Part 2**: a RESTful web API (JSON + XML) built with Django REST
  Framework, and third-party integration with the X (Twitter) API to
  announce new stores/products.

## What's included

- **Accounts**: registration as a Vendor or Buyer, login, logout.
- **Groups & permissions**: `Vendors` and `Buyers` groups are created
  automatically on first migration, with default permissions (see
  `Planning/3_access_control_and_security.md`).
- **Stores & products**: vendors can create/edit/delete their own stores
  and products; ownership is enforced on top of Django permissions.
- **Browsing**: anyone can browse and search products across all stores.
- **Cart**: session-based, supports items from multiple vendors at once.
- **Checkout**: creates an `Order` + `OrderItem`s, reduces stock, clears
  the cart, and emails the buyer an invoice.
- **Reviews**: buyers can review any product; a review is automatically
  marked *verified* if the reviewer has a past order containing that
  product, otherwise *unverified*.
- **Forgot password**: email-a-reset-link flow using single-use,
  time-limited tokens (5 minutes by default), following the
  `ResetToken` design from the task material.
- **Database migrations**: standard Django `makemigrations` / `migrate`,
  configurable to run against MariaDB/MySQL (see below) or SQLite.
- **RESTful web API** (`/api/...`): list/create stores, list/create a
  store's products, list all products, and list a product's reviews -
  every endpoint supports both **JSON and XML** responses, with
  authentication + permission + ownership checks on every write.
- **X (Twitter) integration**: a new store or product (created via the
  website *or* the API) automatically posts an announcement tweet,
  including the store logo or product image if one was uploaded. This is
  fully optional - the site works normally with no Twitter credentials
  configured at all.

## Project layout

```
manage.py
ecommerce_project/       # settings, root urls
ecommerce/                 # the eCommerce app
  models.py                  # Store, Product, Order, OrderItem, Review, ResetToken
  views.py / urls.py         # the website (HTML) views
  api_views.py / api_urls.py / serializers.py   # the RESTful JSON/XML API
  functions/tweet.py         # the X (Twitter) API singleton
  templates/ecommerce/       # HTML templates
static/style.css          # shared stylesheet
media/                     # uploaded store logos / product images (created at runtime)
Planning/                  # written planning docs (Part 1 steps 1-4, Part 2 steps 5-6)
Practical_Task_2/           # Part 1's research answers (requests / JSON-XML / REST)
requirements.txt
```

## Getting started

1. Create and activate a virtual environment, then install dependencies:

   ```bash
   python -m venv venv
   source venv/bin/activate          # venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

   `mysqlclient` needs MySQL/MariaDB client development headers to build
   (e.g. `libmariadb-dev` on Debian/Ubuntu, `mariadb-connector-c` via
   Homebrew on macOS). If you just want to try the project quickly without
   installing those headers, skip `mysqlclient` for now - the project runs
   on SQLite by default (see below) with no extra setup.

2. **Database.** By default the project uses SQLite (`db.sqlite3`), so it
   runs with zero extra configuration. To use MariaDB/MySQL as the task
   requires, create a database and set these environment variables before
   running `manage.py`:

   ```bash
   export DJANGO_DB_ENGINE=mysql
   export DJANGO_DB_NAME=eCommerceDB
   export DJANGO_DB_USER=your_username
   export DJANGO_DB_PASSWORD=your_password
   export DJANGO_DB_HOST=localhost
   export DJANGO_DB_PORT=3306
   ```

3. Run migrations (this also creates the `Vendors`/`Buyers` groups and
   their permissions automatically):

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. (Optional) Create an admin superuser to use `/admin/`:

   ```bash
   python manage.py createsuperuser
   ```

5. Run the development server:

   ```bash
   python manage.py runserver
   ```

   Visit `http://127.0.0.1:8000/`.

## Email

By default, `DJANGO_EMAIL_BACKEND` is the console backend, so invoice and
password-reset emails are printed to the terminal running `runserver` -
convenient for testing without a real mailbox. To send real emails via
Gmail's SMTP server, set:

```bash
export DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
export DJANGO_EMAIL_HOST_USER=your_app_email@gmail.com
export DJANGO_EMAIL_HOST_PASSWORD=your_app_password
export DJANGO_DEFAULT_FROM_EMAIL=your_app_email@gmail.com
```

## Testing the flow manually

1. Register a **Vendor** account, create a store, and add a product to it.
2. Log out, register a **Buyer** account.
3. Browse to the product, add it to the cart, and check out - watch the
   console for the invoice email.
4. From the product page, leave a review - since you purchased the
   product, it is automatically marked as **verified**.
5. Try "Forgot your password?" from the login page - the reset link is
   printed to the console (or emailed, if SMTP is configured).

This exact flow was used to smoke-test every part of the app during
development (registration, permissions, store/product CRUD, cart,
checkout with stock deduction and invoice email, verified vs. unverified
reviews, and the full password-reset round trip).

## Using the API

Every endpoint lives under `/api/` and supports both JSON and XML (see
`Planning/5_api_design.md` for the full endpoint table and Postman
walkthrough). Quick examples with `curl`:

```bash
# Public: list every store (JSON)
curl http://127.0.0.1:8000/api/stores/

# Public: the same, as XML
curl -H "Accept: application/xml" http://127.0.0.1:8000/api/stores/

# Authenticated: create a store as a vendor (Basic Auth)
curl -u vendor1:yourpassword -X POST http://127.0.0.1:8000/api/stores/ \
     -d "name=API Store" -d "description=Created via curl"

# Public: a store's products, filtered
curl http://127.0.0.1:8000/api/stores/1/products/
```

## X (Twitter) announcements

Optional - see `Planning/6_third_party_api_integration.md` for the full
design and reasoning. To enable it:

```bash
export TWITTER_CONSUMER_KEY=your_key
export TWITTER_CONSUMER_SECRET=your_secret
python manage.py runserver
```

The first time the server starts, it prints an authorisation URL to the
terminal; visit it, log in, and paste the PIN back into the terminal. From
then on, every new store or product (created via the website or the API)
tweets an announcement automatically, with the store's logo or the
product's image attached if one was uploaded. Leaving the environment
variables unset disables tweeting with no other effect on the site.

## Notes / things a production deployment would add

- `DJANGO_SECRET_KEY` should be set to a real, random secret via an
  environment variable rather than the placeholder in `settings.py`.
- `DEBUG` should be `False` and `ALLOWED_HOSTS` set to the real domain.
  Note that `media/` is only served by Django itself while `DEBUG=True`;
  a production deployment needs a real static/media file server (e.g.
  nginx or a cloud storage backend) for uploaded logos/images.
- Checkout currently floors stock at zero rather than rejecting an order
  that exceeds available stock outright - a production version would
  validate this before allowing checkout to proceed.
- The X (Twitter) OAuth1 "paste the PIN" flow is inherently a one-time,
  interactive, per-process setup step (see
  `Planning/6_third_party_api_integration.md`); a production deployment
  would instead persist the access token/secret once obtained (e.g. in a
  small database table or secret store) so new server processes don't
  need a human at a terminal to re-authenticate.
