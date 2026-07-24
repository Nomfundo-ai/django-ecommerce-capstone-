from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_default_groups(sender, **kwargs):
    """
    Set up the 'Vendors' and 'Buyers' groups with sensible default
    permissions the first time migrations run, so that new installs of
    this project have working authorisation out of the box.

    Vendors get full add/change/delete/view permissions on Store and
    Product (their inventory). Buyers get view permission on products and
    add permission on reviews. Permissions are only a flag - views still
    check request.user.has_perm(...) before allowing an action, and
    ownership is always re-checked (a vendor may only edit their own
    stores/products).
    """
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType

    from .models import Product, Review, Store

    store_ct = ContentType.objects.get_for_model(Store)
    product_ct = ContentType.objects.get_for_model(Product)
    review_ct = ContentType.objects.get_for_model(Review)

    vendors, _ = Group.objects.get_or_create(name="Vendors")
    vendor_permissions = Permission.objects.filter(content_type__in=[store_ct, product_ct])
    vendors.permissions.set(vendor_permissions)

    buyers, _ = Group.objects.get_or_create(name="Buyers")
    buyer_permissions = Permission.objects.filter(
        content_type=product_ct, codename__startswith="view"
    ) | Permission.objects.filter(content_type=review_ct, codename__startswith="add")
    buyers.permissions.set(buyer_permissions)


class EcommerceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ecommerce"

    def ready(self):
        post_migrate.connect(create_default_groups, sender=self)

        # Create the Tweet singleton (see functions/tweet.py) up front, but
        # only when we are actually about to serve requests - never during
        # `makemigrations`, `migrate`, `test`, `collectstatic`, etc., and
        # only once under runserver's auto-reloader (which starts a watcher
        # process in addition to the real server process).
        import os
        import sys

        is_runserver = "runserver" in sys.argv
        reloader_is_main_process = os.environ.get("RUN_MAIN") == "true"
        running_without_reloader = "--noreload" in sys.argv

        if is_runserver and (reloader_is_main_process or running_without_reloader):
            from .functions.tweet import Tweet

            Tweet()
