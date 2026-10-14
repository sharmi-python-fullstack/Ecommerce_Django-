from .models import Cart


def cart_processor(request):
    cart = None
    cart_count = 0
    session_id = request.session.session_key
    if session_id:
        cart = Cart.objects.filter(session_id=session_id).first()
        if cart:
            cart_count = cart.total_items
    return {
        'cart': cart,
        'cart_count': cart_count,
    }
