"""
A thin, defensive wrapper around the X (Twitter) API v2, used to announce
new stores and new products.

This follows the same three-legged OAuth1 flow (request token -> user
authorises -> access token) shown in the task material, but with a few
deliberate changes so it is safe to run inside a web application rather
than a one-off script:

- Credentials are read from Django settings (which in turn read them from
  environment variables) instead of being hard-coded.
- Every network call is wrapped so a Twitter outage, a missing/invalid
  key, or a declined authorisation can never raise an exception into a
  view and break store/product creation for the user - it is only ever
  logged to the console.
- authenticate() silently disables tweeting (rather than blocking forever
  on input()) whenever it is not safe or not possible to prompt for a PIN
  - e.g. missing credentials, or a non-interactive process such as the
  Django test runner or `manage.py migrate`. See apps.py for the
  additional guard that decides *when* authenticate() is even attempted.
"""

import json
import sys

from django.conf import settings

try:
    from requests_oauthlib import OAuth1Session
except ImportError:  # pragma: no cover - requests-oauthlib should always be installed
    OAuth1Session = None

REQUEST_TOKEN_URL = (
    "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
)
AUTHORIZATION_URL = "https://api.twitter.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://api.twitter.com/oauth/access_token"
TWEET_URL = "https://api.twitter.com/2/tweets"
MEDIA_UPLOAD_URL = "https://upload.twitter.com/1.1/media/upload.json"


class Tweet:
    """
    Singleton (see __new__) wrapper that holds a single authenticated
    OAuth1Session for the lifetime of the running process.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print("[Tweet] Creating the Tweet singleton.")
            instance = super(Tweet, cls).__new__(cls)
            instance.oauth = None
            instance.authenticate()
            cls._instance = instance
        return cls._instance

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def authenticate(self):
        consumer_key = getattr(settings, "TWITTER_CONSUMER_KEY", "")
        consumer_secret = getattr(settings, "TWITTER_CONSUMER_SECRET", "")

        if not consumer_key or not consumer_secret:
            print("[Tweet] No Twitter API credentials configured - tweeting is disabled.")
            return

        if OAuth1Session is None:
            print("[Tweet] requests-oauthlib is not installed - tweeting is disabled.")
            return

        if not sys.stdin.isatty():
            # We cannot prompt for a PIN from a non-interactive process (a
            # test run, a management command, a background worker, etc.),
            # so tweeting is simply left disabled for that run.
            print("[Tweet] Non-interactive process detected - tweeting is disabled for this run.")
            return

        oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)
        try:
            fetch_response = oauth.fetch_request_token(REQUEST_TOKEN_URL)
        except Exception as exc:  # noqa: BLE001 - never let auth crash the app
            print(f"[Tweet] Could not fetch a request token - tweeting is disabled ({exc}).")
            return

        resource_owner_key = fetch_response.get("oauth_token")
        resource_owner_secret = fetch_response.get("oauth_token_secret")
        print(f"[Tweet] Got OAuth token: {resource_owner_key}")

        authorization_url = oauth.authorization_url(AUTHORIZATION_URL)
        print(f"[Tweet] Please go here and authorise: {authorization_url}")
        verifier = input("[Tweet] Paste the PIN here (or press Enter to skip tweeting): ").strip()
        if not verifier:
            print("[Tweet] No PIN supplied - tweeting is disabled for this run.")
            return

        oauth = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=resource_owner_key,
            resource_owner_secret=resource_owner_secret,
            verifier=verifier,
        )
        try:
            oauth_tokens = oauth.fetch_access_token(ACCESS_TOKEN_URL)
        except Exception as exc:  # noqa: BLE001
            print(f"[Tweet] Could not fetch an access token - tweeting is disabled ({exc}).")
            return

        access_token = oauth_tokens["oauth_token"]
        access_token_secret = oauth_tokens["oauth_token_secret"]

        self.oauth = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
        )
        print("[Tweet] Twitter authentication complete - tweeting is enabled.")

    # ------------------------------------------------------------------
    # Posting
    # ------------------------------------------------------------------
    def upload_media(self, image_field):
        """
        Upload an ImageFieldFile (a Store.logo or Product.image) to
        Twitter's v1.1 media endpoint and return its media_id_string, or
        None if there is no image, the upload fails, or we are not
        authenticated. A missing/failed image upload never raises - the
        caller falls back to a text-only tweet.
        """
        if not self.oauth or not image_field:
            return None
        try:
            image_field.open("rb")
            image_bytes = image_field.read()
            image_field.close()
            response = self.oauth.post(MEDIA_UPLOAD_URL, files={"media": image_bytes})
        except Exception as exc:  # noqa: BLE001
            print(f"[Tweet] Media upload error: {exc}")
            return None

        if response.status_code != 200:
            print(f"[Tweet] Media upload failed: {response.status_code} {response.text}")
            return None
        return response.json().get("media_id_string")

    def make_tweet(self, text, image_field=None):
        """
        Post a tweet with the given text and, if provided, one attached
        image. Always returns quietly (logging instead of raising) if
        tweeting is unavailable, so a Twitter problem never breaks store
        or product creation for the person using the site.
        """
        if not self.oauth:
            print("[Tweet] Skipped tweet - Twitter is not authenticated.")
            return None

        tweet = {"text": text}
        media_id = self.upload_media(image_field)
        if media_id:
            tweet["media"] = {"media_ids": [media_id]}

        try:
            response = self.oauth.post(TWEET_URL, json=tweet)
        except Exception as exc:  # noqa: BLE001
            print(f"[Tweet] Could not reach Twitter: {exc}")
            return None

        if response.status_code != 201:
            print(f"[Tweet] Request returned an error: {response.status_code} {response.text}")
            return None

        json_response = response.json()
        print(json.dumps(json_response, indent=4, sort_keys=True))
        return json_response
