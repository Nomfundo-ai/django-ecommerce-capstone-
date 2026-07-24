from django.urls import path

from . import views

app_name = "ecommerce"

urlpatterns = [
    path("", views.home, name="home"),

    # Auth
    path("register/", views.register_user, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),

    # Vendor: stores
    path("my-stores/", views.my_stores, name="my_stores"),
    path("stores/new/", views.store_create, name="store_create"),
    path("stores/<int:store_id>/edit/", views.store_edit, name="store_edit"),
    path("stores/<int:store_id>/delete/", views.store_delete, name="store_delete"),

    # Vendor: products
    path("stores/<int:store_id>/products/", views.store_products, name="store_products"),
    path("stores/<int:store_id>/products/new/", views.product_create, name="product_create"),
    path("products/<int:product_id>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:product_id>/delete/", views.product_delete, name="product_delete"),

    # Buyer: browsing + reviews
    path("products/", views.product_browse, name="product_browse"),
    path("products/<int:product_id>/", views.product_detail, name="product_detail"),
    path("products/<int:product_id>/review/", views.add_review, name="add_review"),

    # Cart + checkout
    path("cart/", views.cart_view, name="cart_view"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.my_orders, name="my_orders"),
    path("orders/<int:order_id>/", views.order_detail, name="order_detail"),

    # Password reset
    path("password-reset/", views.password_reset_request, name="password_reset_request"),
    path(
        "reset_password/<str:token>/",
        views.password_reset_confirm,
        name="password_reset_confirm",
    ),
    path("password-reset/change/", views.password_reset_do, name="password_reset_do"),
]
