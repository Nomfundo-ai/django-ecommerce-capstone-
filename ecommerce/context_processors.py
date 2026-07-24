def cart_summary(request):
    """
    Makes the number of items currently in the session cart available to
    every template (used for the "Cart (3)" link in the nav bar), without
    every view having to pass it in explicitly.
    """
    cart = request.session.get("cart", {})
    item_count = sum(int(qty) for qty in cart.values()) if cart else 0
    return {"cart_item_count": item_count}
