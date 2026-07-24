from django.urls import path

from . import api_views

app_name = "ecommerce_api"

urlpatterns = [
    path("stores/", api_views.store_list_create, name="store_list_create"),
    path(
        "stores/<int:store_id>/products/",
        api_views.store_product_list_create,
        name="store_product_list_create",
    ),
    path("products/", api_views.product_list, name="product_list"),
    path("products/<int:product_id>/reviews/", api_views.product_reviews, name="product_reviews"),
]
