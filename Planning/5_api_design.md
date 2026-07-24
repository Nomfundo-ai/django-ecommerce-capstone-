# API Design Plan (Part 2)

## Serialisation choices

Three models are exposed through the API, using `rest_framework.serializers.ModelSerializer`
"helper classes" exactly as described in the task material:

- **`StoreSerializer`** - `id, vendor, vendor_username, name, description, logo, created_at`.
  `vendor`/`vendor_username` are **read-only**: the owning vendor is always
  taken from `request.user` in the view, never trusted from the request
  body. This is a deliberate change from the raw material's
  `request.data['vendor']` comparison - trusting a client-supplied vendor
  ID (even just to compare it) is unnecessary risk when the authenticated
  user is already known.
- **`ProductSerializer`** - `id, store, store_name, name, description, price, stock, image, created_at`.
  `store`/`store_name` are read-only for the same reason: the store comes
  from the URL (`/api/stores/<store_id>/products/`), not the body.
- **`ReviewSerializer`** - fully read-only; reviews are only ever created
  through the website (where the verified/unverified check happens), not
  through the API.

Both **JSON and XML** representations are supported for every endpoint
(`djangorestframework-xml`'s `XMLRenderer` alongside DRF's default
`JSONRenderer`), so a client picks the format with a standard `Accept`
header or a `?format=xml` query string - matching the "representational
formats" section of the task material.

## Endpoints

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/api/stores/` | Public | List every store; `?vendor=<id>` filters to one vendor's stores |
| POST | `/api/stores/` | Authenticated vendor | Create a store owned by the authenticated user |
| GET | `/api/stores/<store_id>/products/` | Public | List a store's products |
| POST | `/api/stores/<store_id>/products/` | Authenticated vendor, must own the store | Add a product to that store |
| GET | `/api/products/` | Public | List every product; `?store=<id>` filters to one store |
| GET | `/api/products/<product_id>/reviews/` | Public | List a product's reviews |

This satisfies both practical-task-1 requirements: vendors can create
stores, add products, and retrieve reviews through the API (with
authentication enforced before any write); and both buyers and vendors can
retrieve the stores under a given vendor and the products of a given
store, without needing to log in just to browse.

## Authentication & permissions

- `BasicAuthentication` is enabled (as the task material uses, for easy
  Postman testing) alongside `SessionAuthentication` (so an already
  logged-in browser session can call the same endpoints without a second
  login).
- Every write endpoint checks, in order: (1) `request.user.is_authenticated`
  -> `401` if not; (2) the correct Django permission
  (`has_perm('ecommerce.add_store')` / `add_product`) -> `403` if missing;
  (3) for products, that `store.vendor == request.user` -> `403` if not
  the owner. This mirrors the two-layer permission-plus-ownership pattern
  used by the equivalent website views (see
  `Planning/3_access_control_and_security.md`).
- GET endpoints are intentionally public (`AllowAny`) - browsing products
  and stores is not sensitive data, and the task explicitly asks that both
  buyers *and* vendors (i.e. anyone) can retrieve this information.

## Sequence diagrams

Two sequence diagrams are included in `Planning/diagrams/`:

- **`api_get_products_sequence.svg`** - a straightforward read: Postman ->
  API view -> Database -> Serializer -> back to Postman as JSON/XML.
- **`api_post_store_tweet_sequence.svg`** - the more interesting write
  path: Postman -> API view -> authentication/permission check -> database
  save -> the `Tweet` singleton -> the X (Twitter) API, before the
  `201 Created` response reaches the client. This traces the same flow as
  the `create_new_store` sequence diagram in the task material, adapted to
  the API endpoint instead of the website form view.

## Testing with Postman

1. `GET http://127.0.0.1:8000/api/stores/` - no auth needed; returns every
   store as JSON by default (add an `Accept: application/xml` header to
   get XML instead).
2. `POST http://127.0.0.1:8000/api/stores/` - set the **Auth** tab to
   *Basic Auth* with a vendor's username/password, and the **Body** tab to
   *raw* / *JSON* with `{"name": "...", "description": "..."}`. A `201`
   response confirms creation (and the vendor field is filled in
   automatically from the authenticated user).
3. `POST http://127.0.0.1:8000/api/stores/<id>/products/` - same Basic
   Auth vendor, body `{"name": "...", "description": "...", "price": "9.99", "stock": 5}`.
   Trying this with a *different* vendor's credentials against a store you
   don't own returns `403 {"detail": "You do not own this store."}`.
