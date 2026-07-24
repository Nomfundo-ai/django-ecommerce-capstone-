# Third-Party API Integration Plan (Part 2, practical task 2)

## What was built

A `Tweet` singleton class (`ecommerce/functions/tweet.py`) wraps the X
(Twitter) API v2, following the three-legged OAuth1 flow shown in the task
material (request token -> user authorises via a PIN -> access token). It
is used to post an announcement automatically whenever:

- a vendor creates a **new store** (tweet includes the store name,
  description, and the store's logo image, if one was uploaded), or
- a vendor adds a **new product** to a store (tweet includes the store
  name, product name, description, and the product's image, if one was
  uploaded) -

...whether the store/product was created through the **website form** or
through the **API** (`views.py` and `api_views.py` both call the same
`utils.announce_store()` / `utils.announce_product()` helpers, so the
behaviour is identical either way).

## Deliberate departures from the raw task material, and why

The task material's `authenticate()` calls Python's built-in `input()` to
ask for the OAuth PIN, which is fine for a one-off script but is a poor
fit for a web application:

1. **Blocking a web server on `input()` is dangerous.** If this ran
   unconditionally in `apps.py`'s `ready()`, every single invocation of
   `manage.py` - including `makemigrations`, `migrate`, `test`,
   `collectstatic`, and even Django's `runserver` auto-reload *watcher*
   process - would hang waiting for console input that will never come in
   most of those contexts. `EcommerceConfig.ready()` now only attempts
   Twitter authentication when the command is actually `runserver`, and
   only in the real server process (guarded with `RUN_MAIN`/`--noreload`),
   never during migrations or tests. This was verified directly: running
   `makemigrations`, `migrate`, and the whole test-client smoke test never
   triggered a prompt, while `runserver` does attempt it.
2. **Missing/invalid credentials, no TTY, or a Twitter outage must never
   break the store/product creation flow that the task material's own
   `create_new_store` example otherwise crashes on.** `authenticate()`
   checks for credentials and an interactive terminal before prompting at
   all, and every network call in `Tweet` is wrapped so a failure is
   logged to the console rather than raised. `announce_store()` /
   `announce_product()` in `utils.py` add a second safety net around that.
   This was also verified: creating stores/products via both the website
   and the API succeeds normally (with a logged
   "`[Tweet] ... tweeting is disabled`" message) even with no Twitter
   credentials configured at all.
3. **Credentials are read from environment variables**
   (`TWITTER_CONSUMER_KEY` / `TWITTER_CONSUMER_SECRET` via
   `settings.py`), not hard-coded as constants in the class, so a real key
   and secret never need to be committed to source control.
4. **Image attachments.** The task material's `make_tweet()` only sends
   text. Since practical task 2 requires attaching a store logo or product
   image when one exists, `Tweet.upload_media()` was added: it uploads the
   image bytes to Twitter's `v1.1 media/upload` endpoint first (the `v2`
   tweet endpoint does not accept raw file uploads directly) and attaches
   the resulting `media_id` to the tweet payload. If there is no image, or
   the upload fails for any reason, `make_tweet()` still sends a
   text-only tweet rather than failing the whole announcement.

## Setup (for whoever marks/runs this)

1. Register a developer account at the X developer portal and generate a
   Consumer Key/Secret with **read and write** access.
2. Set them as environment variables before running the server:
   ```bash
   export TWITTER_CONSUMER_KEY=your_key
   export TWITTER_CONSUMER_SECRET=your_secret
   ```
3. Run `python manage.py runserver` from an interactive terminal. The
   first request that triggers `ready()` will print an authorisation URL;
   open it, log in, and paste the PIN back into the terminal. From then on,
   every store/product created for the rest of that server process will be
   tweeted automatically.
4. If you'd rather not set this up, just leave the environment variables
   unset - the site works completely normally, minus the tweets (this is
   confirmed by the automated smoke test in `README.md`).

## Sequence diagram

See `Planning/diagrams/api_post_store_tweet_sequence.svg` for the full
request path, including the `Tweet` singleton and the X API call, for the
`POST /api/stores/` endpoint - the same flow applies to product creation
and to the website's own (non-API) create-store/create-product views.
