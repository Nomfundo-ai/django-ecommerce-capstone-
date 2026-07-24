from rest_framework import serializers

from .models import Product, Review, Store


class StoreSerializer(serializers.ModelSerializer):
    """
    Serialises a Store for the API.

    vendor/vendor_username are read-only: the vendor is always taken from
    the authenticated request user in the view rather than trusted from
    the request body, so a vendor can never create a store "on behalf of"
    another user by tampering with the payload.
    """

    vendor = serializers.ReadOnlyField(source="vendor.id")
    vendor_username = serializers.ReadOnlyField(source="vendor.username")

    class Meta:
        model = Store
        fields = ["id", "vendor", "vendor_username", "name", "description", "logo", "created_at"]
        read_only_fields = ["id", "vendor", "vendor_username", "created_at"]


class ProductSerializer(serializers.ModelSerializer):
    """
    Serialises a Product for the API. store/store_name are read-only for
    the same reason vendor is read-only on StoreSerializer - the store is
    taken from the URL and ownership is checked in the view.
    """

    store_name = serializers.ReadOnlyField(source="store.name")

    class Meta:
        model = Product
        fields = ["id", "store", "store_name", "name", "description", "price", "stock", "image", "created_at"]
        read_only_fields = ["id", "store", "store_name", "created_at"]


class ReviewSerializer(serializers.ModelSerializer):
    """Read-only serialiser for reviews - reviews are only ever created via the website, not the API."""

    username = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Review
        fields = ["id", "product", "username", "rating", "comment", "verified", "created_at"]
        read_only_fields = fields
