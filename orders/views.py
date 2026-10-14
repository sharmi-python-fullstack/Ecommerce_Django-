from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from cart.models import Cart, CartItem
from .models import Order, OrderItem, Address, Coupon


def get_cart(request):
    session_id = request.session.session_key
    if not session_id:
        return None
    return Cart.objects.filter(session_id=session_id).first()


def calculate_totals(cart, coupon=None):
    items_total = cart.total_price if cart else 0
    delivery_charge = 30 if items_total > 0 else 0
    handling_charge = 10 if items_total > 0 else 0
    discount = 0
    if coupon and items_total >= coupon.min_order_amount:
        if coupon.discount_percent > 0:
            discount = (items_total * coupon.discount_percent) / 100
        elif coupon.discount_amount > 0:
            discount = coupon.discount_amount
        if discount > items_total:
            discount = items_total
    grand_total = items_total + delivery_charge + handling_charge - discount
    return {
        'items_total': items_total,
        'delivery_charge': delivery_charge,
        'handling_charge': handling_charge,
        'discount': discount,
        'grand_total': grand_total,
    }


PAYMENT_METHODS = [
    ('Google Pay', 'Google Pay'),
    ('Cred UPI', 'Cred UPI'),
    ('Amazon Pay UPI', 'Amazon Pay UPI'),
    ('PhonePe', 'PhonePe'),
    ('Paytm UPI', 'Paytm UPI'),
    ('BHIM UPI', 'BHIM UPI'),
    ('Credit Card', 'Credit Card'),
    ('Debit Card', 'Debit Card'),
    ('Net Banking', 'Net Banking'),
    ('Cash on Delivery', 'Cash on Delivery'),
]


def checkout(request):
    cart = get_cart(request)
    if not cart or not cart.items.exists():
        messages.info(request, 'Your cart is empty. Add some products first!')
        return redirect('cart:cart_detail')

    coupon_code = request.POST.get('coupon_code', '').strip()
    coupon = None
    if coupon_code:
        coupon = Coupon.objects.filter(code=coupon_code, is_active=True).first()
        if not coupon:
            messages.error(request, 'Invalid coupon code.')
        else:
            now = timezone.now()
            if (coupon.valid_from and now < coupon.valid_from) or (coupon.valid_to and now > coupon.valid_to):
                messages.error(request, 'This coupon is expired.')
                coupon = None

    totals = calculate_totals(cart, coupon)
    cart_items = cart.items.select_related('product').all()

    if request.method == 'POST' and 'place_order' in request.POST:
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address_line = request.POST.get('address_line', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        payment_method = request.POST.get('payment_method', '').strip()

        if not all([full_name, phone, address_line, city, state, pincode]):
            messages.error(request, 'Please fill in all address fields.')
        elif not payment_method:
            messages.error(request, 'Please select a payment method.')
        else:
            address = Address.objects.create(
                full_name=full_name, phone=phone, address_line=address_line,
                city=city, state=state, pincode=pincode,
            )
            order = Order.objects.create(
                cart=cart, address=address,
                items_total=totals['items_total'],
                delivery_charge=totals['delivery_charge'],
                handling_charge=totals['handling_charge'],
                coupon=coupon,
                discount=totals['discount'],
                grand_total=totals['grand_total'],
                payment_method=payment_method,
                payment_status='Paid',
                status='Placed',
            )
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product_name=item.product.name,
                    product_price=item.product.price,
                    quantity=item.quantity,
                    subtotal=item.subtotal,
                )
            cart.items.all().delete()
            return redirect('orders:order_success', order_id=order.id)

    coupons = Coupon.objects.filter(is_active=True)
    context = {
        'cart_items': cart_items,
        'coupons': coupons,
        'applied_coupon': coupon,
        'payment_methods': PAYMENT_METHODS,
        **totals,
    }
    return render(request, 'orders/checkout.html', context)


def order_success(request, order_id):
    order = Order.objects.filter(id=order_id).first()
    if not order:
        return redirect('products:home')
    order_items = order.items.all()
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'orders/order_success.html', context)
