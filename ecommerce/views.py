"""
View functions for the eCommerce application.

Covers four areas: user registration and authentication; vendor management
of stores and products; buyer browsing, reviews, cart and checkout; and the
forgotten-password reset flow.

Vendor and buyer capabilities are separated using Django's permission
framework, with ownership checks applied on top so that a vendor can only
modify their own stores and products.
"""

from hashlib import sha1

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import (
    LoginForm,
    PasswordResetRequestForm,
    ProductForm,
    RegisterForm,
    ReviewForm,
    SetNewPasswordForm,
    StoreForm,
)
from .models import Order, OrderItem, Product, ResetToken, Review, Store
from .utils import (
    add_to_cart,
    announce_product,
    announce_store,
    build_invoice_email,
    build_password_reset_email,
    change_user_password,
    clear_cart,
    generate_reset_url,
    get_cart,
    get_cart_items,
    remove_from_cart,
)


# ---------------------------------------------------------------------------
# Home / registration / authentication
# ---------------------------------------------------------------------------

def home(request):
    """Render the landing page with the eight most recently added products."""
    latest_products = Product.objects.select_related("store").order_by("-created_at")[:8]
    return render(request, "ecommerce/home.html", {"latest_products": latest_products})


def register_user(request):
    """
    Register a new buyer or vendor account.

    Creates the user via ``create_user()`` so the password is hashed, assigns
    them to the Group matching their chosen account type, and logs them in.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: The registration form, or a redirect home on success.
    """
    if request.user.is_authenticated:
        return redirect("ecommerce:home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            # RegisterForm is a plain Form (not a ModelForm) because the
            # password has to go through create_user() so Django hashes it,
            # rather than being saved as plain text by a ModelForm.
            from django.contrib.auth.models import User

            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
                email=form.cleaned_data["email"],
            )
            group_name = form.cleaned_data["account_type"]
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
            user.save()

            login(request, user)
            messages.success(request, "Welcome! Your account has been created.")
            return redirect("ecommerce:home")
    else:
        form = RegisterForm()
    return render(request, "ecommerce/register.html", {"form": form})


def login_user(request):
    """
    Authenticate a user and start a session.

    Honours a ``next`` parameter so users are returned to the page they were
    trying to reach before being asked to log in.
    """
    if request.user.is_authenticated:
        return redirect("ecommerce:home")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user is not None:
                login(request, user)
                next_url = request.POST.get("next") or request.GET.get("next")
                return redirect(next_url or "ecommerce:home")
            form.add_error(None, "Incorrect username or password.")
    else:
        form = LoginForm()
    return render(request, "ecommerce/login.html", {"form": form})


@login_required
def logout_user(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("ecommerce:home")


# ---------------------------------------------------------------------------
# Vendor: store management
# ---------------------------------------------------------------------------

@login_required
def my_stores(request):
    stores = Store.objects.filter(vendor=request.user)
    return render(request, "ecommerce/store_list.html", {"stores": stores})


@login_required
@permission_required("ecommerce.add_store", raise_exception=True)
def store_create(request):
    if request.method == "POST":
        form = StoreForm(request.POST, request.FILES)
        if form.is_valid():
            store = form.save(commit=False)
            store.vendor = request.user
            store.save()
            announce_store(store)
            messages.success(request, f"Store '{store.name}' created.")
            return redirect("ecommerce:my_stores")
    else:
        form = StoreForm()
    return render(request, "ecommerce/store_form.html", {"form": form, "action": "Create"})


def _get_owned_store(request, store_id):
    """
    Fetch a store, ensuring the requesting user owns it.

    Args:
        request (HttpRequest): The incoming request.
        store_id (int): Primary key of the store.

    Returns:
        Store: The requested store.

    Raises:
        Http404: If no store with that primary key exists.
        PermissionDenied: If the store belongs to a different vendor.
    """
    store = get_object_or_404(Store, pk=store_id)
    if store.vendor != request.user:
        raise PermissionDenied("You do not own this store.")
    return store


@login_required
@permission_required("ecommerce.change_store", raise_exception=True)
def store_edit(request, store_id):
    store = _get_owned_store(request, store_id)
    if request.method == "POST":
        form = StoreForm(request.POST, request.FILES, instance=store)
        if form.is_valid():
            form.save()
            messages.success(request, "Store updated.")
            return redirect("ecommerce:my_stores")
    else:
        form = StoreForm(instance=store)
    return render(request, "ecommerce/store_form.html", {"form": form, "action": "Edit"})


@login_required
@permission_required("ecommerce.delete_store", raise_exception=True)
def store_delete(request, store_id):
    store = _get_owned_store(request, store_id)
    if request.method == "POST":
        store.delete()
        messages.success(request, "Store deleted.")
        return redirect("ecommerce:my_stores")
    return render(request, "ecommerce/store_confirm_delete.html", {"store": store})


# ---------------------------------------------------------------------------
# Vendor: product management
# ---------------------------------------------------------------------------

@login_required
@permission_required("ecommerce.view_product", raise_exception=True)
def store_products(request, store_id):
    store = _get_owned_store(request, store_id)
    products = store.products.all()
    return render(request, "ecommerce/product_list.html", {"store": store, "products": products})


@login_required
@permission_required("ecommerce.add_product", raise_exception=True)
def product_create(request, store_id):
    store = _get_owned_store(request, store_id)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.store = store
            product.save()
            announce_product(product)
            messages.success(request, f"Product '{product.name}' added.")
            return redirect("ecommerce:store_products", store_id=store.id)
    else:
        form = ProductForm()
    return render(request, "ecommerce/product_form.html", {"form": form, "store": store, "action": "Add"})


def _get_owned_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if product.store.vendor != request.user:
        raise PermissionDenied("You do not own this product.")
    return product


@login_required
@permission_required("ecommerce.change_product", raise_exception=True)
def product_edit(request, product_id):
    product = _get_owned_product(request, product_id)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated.")
            return redirect("ecommerce:store_products", store_id=product.store.id)
    else:
        form = ProductForm(instance=product)
    return render(
        request, "ecommerce/product_form.html", {"form": form, "store": product.store, "action": "Edit"}
    )


@login_required
@permission_required("ecommerce.delete_product", raise_exception=True)
def product_delete(request, product_id):
    product = _get_owned_product(request, product_id)
    store_id = product.store.id
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted.")
        return redirect("ecommerce:store_products", store_id=store_id)
    return render(request, "ecommerce/product_confirm_delete.html", {"product": product})


# ---------------------------------------------------------------------------
# Buyer: browsing products, viewing a product + reviews
# ---------------------------------------------------------------------------

def product_browse(request):
    products = Product.objects.select_related("store").all()
    query = request.GET.get("q")
    if query:
        products = products.filter(name__icontains=query)
    return render(request, "ecommerce/product_browse.html", {"products": products, "query": query or ""})


def product_detail(request, product_id):
    product = get_object_or_404(Product.objects.select_related("store"), pk=product_id)
    reviews = product.reviews.select_related("user").all()
    review_form = ReviewForm()
    return render(
        request,
        "ecommerce/product_detail.html",
        {"product": product, "reviews": reviews, "review_form": review_form},
    )


@login_required
@permission_required("ecommerce.add_review", raise_exception=True)
def add_review(request, product_id):
    """
    Save a buyer's review of a product.

    The review is flagged as verified only when the reviewing user has an
    existing order containing this product; otherwise it is stored as
    unverified.
    """
    product = get_object_or_404(Product, pk=product_id)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            has_purchased = OrderItem.objects.filter(
                order__buyer=request.user, product=product
            ).exists()
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.verified = has_purchased
            review.save()
            messages.success(
                request,
                "Review submitted as verified (you purchased this product)."
                if has_purchased
                else "Review submitted as unverified (no purchase found for this product).",
            )
    return redirect("ecommerce:product_detail", product_id=product.id)


# ---------------------------------------------------------------------------
# Cart (session-based) and checkout
# ---------------------------------------------------------------------------

def cart_view(request):
    items = get_cart_items(request)
    total = sum(item["line_total"] for item in items)
    return render(request, "ecommerce/cart.html", {"items": items, "total": total})


@login_required
def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    quantity = request.POST.get("quantity", 1)
    try:
        quantity = max(1, int(quantity))
    except (TypeError, ValueError):
        quantity = 1
    add_to_cart(request, product.id, quantity)
    messages.success(request, f"Added {quantity} x {product.name} to your cart.")
    return redirect("ecommerce:product_detail", product_id=product.id)


@login_required
def cart_remove(request, product_id):
    remove_from_cart(request, product_id)
    messages.info(request, "Item removed from your cart.")
    return redirect("ecommerce:cart_view")


@login_required
def checkout(request):
    """
    Convert the session cart into a persisted Order.

    Runs inside a database transaction so that the order, its line items and
    the stock adjustments either all succeed or all roll back. Quantities are
    capped at available stock, prices and names are snapshotted onto each
    OrderItem, the cart is cleared, and an invoice email is sent.

    Returns:
        HttpResponse: The checkout page, or a redirect to the new order.
    """
    items = get_cart_items(request)
    if not items:
        messages.warning(request, "Your cart is empty.")
        return redirect("ecommerce:product_browse")

    if request.method == "POST":
        with transaction.atomic():
            order = Order.objects.create(buyer=request.user, total=0)
            total = 0
            for entry in items:
                product = entry["product"]
# Never sell more units than the vendor has in stock.
                quantity = min(entry["quantity"], product.stock)
                if quantity < 1:
                    continue
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    quantity=quantity,
                    price=product.price,
                )
                # Reduce stock, but never below zero.
                product.stock = max(0, product.stock - quantity)
                product.save()
                total += product.price * quantity
            order.total = total
            order.save()

        clear_cart(request)

        email = build_invoice_email(order)
        email.send()

        messages.success(request, f"Order #{order.id} placed! An invoice has been emailed to you.")
        return redirect("ecommerce:order_detail", order_id=order.id)

    total = sum(item["line_total"] for item in items)
    return render(request, "ecommerce/checkout.html", {"items": items, "total": total})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if order.buyer != request.user:
        raise PermissionDenied("You do not have access to this order.")
    return render(request, "ecommerce/order_detail.html", {"order": order})


@login_required
def my_orders(request):
    orders = Order.objects.filter(buyer=request.user)
    return render(request, "ecommerce/order_list.html", {"orders": orders})


# ---------------------------------------------------------------------------
# Forgotten password
# ---------------------------------------------------------------------------

def password_reset_request(request):
    """
    Email a password reset link to a registered address.

    The same confirmation message is shown whether or not the address matches
    an account, so the page cannot be used to discover which emails are
    registered.
    """
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            from django.contrib.auth.models import User

            user = User.objects.filter(email=email).first()
            # Always show the same confirmation message, whether or not the
            # email matched an account, so we do not leak which addresses
            # are registered.
            if user is not None:
                url = generate_reset_url(user, request)
                message = build_password_reset_email(user, url)
                message.send()
            messages.success(
                request, "If that email address is registered, a reset link has been sent."
            )
            return redirect("ecommerce:login")
    else:
        form = PasswordResetRequestForm()
    return render(request, "ecommerce/password_reset_request.html", {"form": form})


def password_reset_confirm(request, token):
    """
    Validate a reset token from an emailed link.

    The token is hashed before lookup, since only the hash is stored. Expired
    tokens are deleted. A valid token is held in the session for the
    subsequent password change step.
    """
    hashed = sha1(token.encode()).hexdigest()
    reset_token = ResetToken.objects.filter(token=hashed, used=False).first()

    valid = False
    if reset_token is not None:
        if reset_token.expiry_date < timezone.now():
            reset_token.delete()
        else:
            valid = True
            request.session["password_reset_user"] = reset_token.user.username
            request.session["password_reset_token"] = token

    if not valid:
        messages.error(request, "This password reset link is invalid or has expired.")
        return redirect("ecommerce:password_reset_request")

    return render(request, "ecommerce/password_reset_confirm.html", {"token": token})


def password_reset_do(request):
    username = request.session.get("password_reset_user")
    token = request.session.get("password_reset_token")
    if not username or not token:
        messages.error(request, "Your password reset session has expired. Please request a new link.")
        return redirect("ecommerce:password_reset_request")

    if request.method == "POST":
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            change_user_password(username, form.cleaned_data["password"])
            ResetToken.objects.filter(token=sha1(token.encode()).hexdigest()).delete()
            del request.session["password_reset_user"]
            del request.session["password_reset_token"]
            messages.success(request, "Your password has been changed. Please log in.")
            return redirect("ecommerce:login")
    else:
        form = SetNewPasswordForm()
    return render(request, "ecommerce/password_reset_do.html", {"form": form})
