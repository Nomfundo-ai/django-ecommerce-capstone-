"""
Django settings for ecommerce_project.

This project implements Part 1 of the Django eCommerce practical task:
authentication, user groups/permissions, sessions (shopping cart),
database migration, and password-reset-via-email.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# In a real deployment this should be read from an environment variable.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-change-this-key-before-deploying-to-production",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "ecommerce.apps.EcommerceConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ecommerce_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "ecommerce.context_processors.cart_summary",
            ],
        },
    },
]

WSGI_APPLICATION = "ecommerce_project.wsgi.application"


# ---------------------------------------------------------------------------
# Database
#
# The task requires a relational database engine such as MariaDB/MySQL
# instead of the default SQLite database. Because the exact server
# credentials are specific to each developer's machine, the engine is
# controlled with the DJANGO_DB_ENGINE environment variable so the same
# settings file works both for local development (sqlite) and for the
# MariaDB server the task asks us to use.
#
# To use MariaDB, set the following environment variables before running
# manage.py (see README.md for full instructions):
#   DJANGO_DB_ENGINE=mysql
#   DJANGO_DB_NAME=eCommerceDB
#   DJANGO_DB_USER=your_username
#   DJANGO_DB_PASSWORD=your_password
#   DJANGO_DB_HOST=localhost
#   DJANGO_DB_PORT=3306
# ---------------------------------------------------------------------------
if os.environ.get("DJANGO_DB_ENGINE") == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("DJANGO_DB_NAME", "eCommerceDB"),
            "USER": os.environ.get("DJANGO_DB_USER", "root"),
            "PASSWORD": os.environ.get("DJANGO_DB_PASSWORD", ""),
            "HOST": os.environ.get("DJANGO_DB_HOST", "localhost"),
            "PORT": os.environ.get("DJANGO_DB_PORT", "3306"),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Johannesburg"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Authentication / sessions
# ---------------------------------------------------------------------------
LOGIN_URL = "ecommerce:login"
LOGIN_REDIRECT_URL = "ecommerce:home"
LOGOUT_REDIRECT_URL = "ecommerce:home"

# Cart / session cookies stay alive for 2 weeks of inactivity by default.
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14
SESSION_SAVE_EVERY_REQUEST = True

# ---------------------------------------------------------------------------
# Email (used for order invoices and password-reset links)
#
# Defaults to the console backend so emails can be seen during development
# and marking without needing a real mailbox. Switch to the SMTP backend
# (e.g. Gmail) for a real deployment - see README.md.
# ---------------------------------------------------------------------------
EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("DJANGO_EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("DJANGO_EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("DJANGO_EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.environ.get("DJANGO_EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("DJANGO_EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DJANGO_DEFAULT_FROM_EMAIL", "no-reply@ecommerce.example.com")

# Base URL used to build password-reset links inside emails.
SITE_DOMAIN = os.environ.get("DJANGO_SITE_DOMAIN", "http://127.0.0.1:8000")

# How long a password reset link stays valid for.
PASSWORD_RESET_TIMEOUT_MINUTES = 5

# ---------------------------------------------------------------------------
# Media (store logos, product images)
# ---------------------------------------------------------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# Django REST Framework
#
# DEFAULT_RENDERER_CLASSES includes both JSON and XML (via
# djangorestframework-xml) so a client controls the representation format
# with a standard Accept header (or a ?format=xml query string), matching
# the "representational formats" section of the task material.
# BasicAuthentication is enabled for Postman-style testing; SessionAuthentication
# lets an already-logged-in browser session call the same endpoints.
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework_xml.renderers.XMLRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework_xml.parsers.XMLParser",
    ],
}

# ---------------------------------------------------------------------------
# X (Twitter) API credentials
#
# Read from the environment rather than hard-coded, unlike the raw example
# in the task material - an API key/secret should never be committed to
# source control. Tweeting is automatically disabled (see
# ecommerce/functions/tweet.py) if these are left blank.
# ---------------------------------------------------------------------------
TWITTER_CONSUMER_KEY = os.environ.get("TWITTER_CONSUMER_KEY", "")
TWITTER_CONSUMER_SECRET = os.environ.get("TWITTER_CONSUMER_SECRET", "")

