"""
The RESTful web API for the eCommerce service (Part 2, practical task 1).

Endpoints
---------
GET  /api/stores/                       list all stores (optionally ?vendor=<id>)
POST /api/stores/                       create a store (authenticated vendor)
GET  /api/stores/<store_id>/products/   list a store's products
POST /api/stores/<store_id>/products/   add a product to a store (the owning vendor only)
GET  /api/products/                     list all products (optionally ?store=<id>)
GET  /api/products/<product_id>/reviews/  list a product's reviews

Every endpoint supports both JSON and XML representations (see
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] in settings.py) - request one or
the other with a standard `Accept` header, or a `?format=json` / `?format=xml`
query string.

GET endpoints are open to anyone (buyers and vendors alike, per the task
brief); POST endpoints require authentication (Basic auth or an existing
logged-in session) *and* the correct Django permission *and* - for
products - ownership of the parent store, mirroring the two-layer checks
used by the equivalent website views in views.py.
"""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Product, Store
from .serializers import ProductSerializer, ReviewSerializer, StoreSerializer
from .utils import announce_product, announce_store


@api_view(["GET", "POST"])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([AllowAny])
def store_list_create(request):
    """List every store, or create a new one for the authenticated vendor."""
    if request.method == "GET":
        stores = Store.objects.select_related("vendor").all()
        vendor_id = request.query_params.get("vendor")
        if vendor_id:
            stores = stores.filter(vendor_id=vendor_id)
        serializer = StoreSerializer(stores, many=True, context={"request": request})
        return Response(serializer.data)

    # POST - create a store.
    if not request.user.is_authenticated:
        return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
    if not request.user.has_perm("ecommerce.add_store"):
        return Response(
            {"detail": "You do not have permission to create a store."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = StoreSerializer(data=request.data, context={"request": request})
    if serializer.is_valid():
        store = serializer.save(vendor=request.user)
        announce_store(store)
        return Response(
            StoreSerializer(store, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "POST"])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([AllowAny])
def store_product_list_create(request, store_id):
    """List a store's products, or add a new product to it (the owning vendor only)."""
    store = get_object_or_404(Store, pk=store_id)

    if request.method == "GET":
        products = store.products.all()
        serializer = ProductSerializer(products, many=True, context={"request": request})
        return Response(serializer.data)

    # POST - add a product to this store.
    if not request.user.is_authenticated:
        return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
    if store.vendor != request.user:
        return Response(
            {"detail": "You do not own this store."}, status=status.HTTP_403_FORBIDDEN
        )
    if not request.user.has_perm("ecommerce.add_product"):
        return Response(
            {"detail": "You do not have permission to add products."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = ProductSerializer(data=request.data, context={"request": request})
    if serializer.is_valid():
        product = serializer.save(store=store)
        announce_product(product)
        return Response(
            ProductSerializer(product, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([AllowAny])
def product_list(request):
    """List every product, optionally filtered to a single store with ?store=<id>."""
    products = Product.objects.select_related("store").all()
    store_id = request.query_params.get("store")
    if store_id:
        products = products.filter(store_id=store_id)
    serializer = ProductSerializer(products, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def product_reviews(request, product_id):
    """List every review left for a single product."""
    product = get_object_or_404(Product, pk=product_id)
    reviews = product.reviews.select_related("user").all()
    serializer = ReviewSerializer(reviews, many=True, context={"request": request})
    return Response(serializer.data)
