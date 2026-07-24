from django.contrib import admin

from .models import Order, OrderItem, Product, ResetToken, Review, Store


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor", "created_at")
    search_fields = ("name", "vendor__username")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "price", "stock", "created_at")
    list_filter = ("store",)
    search_fields = ("name",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "buyer", "total", "created_at")
    inlines = [OrderItemInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "verified", "created_at")
    list_filter = ("verified", "rating")


@admin.register(ResetToken)
class ResetTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "expiry_date", "used")
