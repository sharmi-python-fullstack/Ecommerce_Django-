from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Cart, CartItem
from products.models import Product


def get_or_create_cart(request):
    if not request.session.session_key:
        request.session.create()
    session_id = request.session.session_key
    cart, _ = Cart.objects.get_or_create(session_id=session_id)
    return cart


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_or_create_cart(request)
    quantity = int(request.POST.get('quantity', 1))
    if quantity < 1:
        quantity = 1
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if created:
        cart_item.quantity = quantity
    else:
        cart_item.quantity += quantity
    cart_item.save()
    messages.success(request, f'{product.name} added to cart!')
    return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))


def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    quantity = int(request.POST.get('quantity', 1))
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart:cart_detail')


def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    return redirect('cart:cart_detail')


def cart_detail(request):
    cart = get_or_create_cart(request)
    items = cart.items.select_related('product').all()
    items_total = cart.total_price
    delivery_charge = 30 if items_total > 0 else 0
    handling_charge = 10 if items_total > 0 else 0
    grand_total = items_total + delivery_charge + handling_charge
    context = {
        'cart_items': items,
        'items_total': items_total,
        'delivery_charge': delivery_charge,
        'handling_charge': handling_charge,
        'grand_total': grand_total,
    }
    return render(request, 'cart/cart_detail.html', context)
