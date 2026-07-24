"""
Helper functions kept separate from views.py so the request/response
handling in views.py stays easy to read. Mirrors the helper-function style
used throughout the task material (e.g. change_user_password,
generate_reset_url, build_email).
"""

import secrets
from datetime import timedelta
from hashlib import sha1

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils import timezone

from .models import Product, ResetToken
from .functions.tweet import Tweet


def announce_store(store):
    """
    Post a tweet announcing a new store. Never raises - a Twitter outage,
    missing credentials, or a declined authorisation must never stop a
    vendor from successfully creating a store.
    """
    text = f"New store open on GrabMore!\n{store.name}\n\n{store.description}"
    try:
        Tweet().make_tweet(text, image_field=store.logo if store.logo else None)
    except Exception as exc:  # noqa: BLE001
        print(f"[Tweet] Skipped store announcement due to an error: {exc}")


def announce_product(product):
    """Post a tweet announcing a new product, following the same fail-safe approach as announce_store()."""
    text = f"New product at {product.store.name}!\n{product.name}\n\n{product.description}"
    try:
        Tweet().make_tweet(text, image_field=product.image if product.image else None)
    except Exception as exc:  # noqa: BLE001
        print(f"[Tweet] Skipped product announcement due to an error: {exc}")


def change_user_password(username, new_password):
    """Set a new password for the given username."""
    user = User.objects.get(username=username)
    user.set_password(new_password)
    user.save()


def generate_reset_url(user, request):
    """
    Create a ResetToken for the user (valid for
    settings.PASSWORD_RESET_TIMEOUT_MINUTES) and return the absolute URL
    the user must click to reset their password.
    """
    token = secrets.token_urlsafe(16)
    expiry_date = timezone.now() + timedelta(minutes=settings.PASSWORD_RESET_TIMEOUT_MINUTES)
    ResetToken.objects.create(
        user=user,
        token=sha1(token.encode()).hexdigest(),
        expiry_date=expiry_date,
    )
    path = reverse("ecommerce:password_reset_confirm", args=[token])
    return request.build_absolute_uri(path)


def build_password_reset_email(user, reset_url):
    subject = "Password Reset"
    body = (
        f"Hi {user.username},\n\n"
        f"Here is your link to reset your password:\n{reset_url}\n\n"
        f"This link will expire in {settings.PASSWORD_RESET_TIMEOUT_MINUTES} minutes. "
        "If you did not request a password reset, you can safely ignore this email."
    )
    return EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email])


def build_invoice_email(order):
    """Build (but do not send) an EmailMessage containing an order invoice."""
    lines = [f"Hi {order.buyer.username},", "", "Thank you for your order! Here is your invoice:", ""]
    for item in order.items.all():
        lines.append(f"  {item.quantity} x {item.product_name} @ R{item.price} = R{item.line_total}")
    lines += ["", f"Order total: R{order.total}", "", f"Order reference: #{order.pk}"]
    body = "\n".join(lines)
    subject = f"Your invoice for order #{order.pk}"
    return EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [order.buyer.email])


# ---------------------------------------------------------------------------
# Session cart helpers
#
# The cart is stored in request.session as {"cart": {"<product_id>": qty}}
# so that it survives across requests (and across a login, per Django's
# session behaviour) without needing a database table.
# ---------------------------------------------------------------------------

def get_cart(request):
    return request.session.get("cart", {})


def add_to_cart(request, product_id, quantity):
    cart = request.session.get("cart", {})
    product_id = str(product_id)
    current_quantity = int(cart.get(product_id, 0))
    cart[product_id] = current_quantity + int(quantity)
    request.session["cart"] = cart
    request.session.modified = True


def remove_from_cart(request, product_id):
    cart = request.session.get("cart", {})
    cart.pop(str(product_id), None)
    request.session["cart"] = cart
    request.session.modified = True


def clear_cart(request):
    request.session["cart"] = {}
    request.session.modified = True


def get_cart_items(request):
    """Return a list of {product, quantity, line_total} for template rendering."""
    cart = get_cart(request)
    items = []
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.select_related("store").get(pk=product_id)
        except Product.DoesNotExist:
            continue
        quantity = int(quantity)
        items.append(
            {
                "product": product,
                "quantity": quantity,
                "line_total": product.price * quantity,
            }
        )
    return items
