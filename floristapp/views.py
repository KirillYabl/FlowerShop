from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, render

from flowerapp.models import Bouquet, FlowerShop, Order


def is_florist(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_florist, login_url='login')
def view_availability(request):
    flower_shops = FlowerShop.objects.order_by('address')
    shops_addresses = [
        flower_shop.address[11:].strip() if flower_shop.address.startswith('Красноярск,') else flower_shop.address
        for flower_shop in flower_shops
    ]

    bouquets = list(Bouquet.objects.prefetch_related('catalog_items').order_by('name'))
    bouquets_availability = []
    for bouquet in bouquets:
        availability = {item.flower_shop_id: item.availability for item in bouquet.catalog_items.all()}
        ordered_availability = [availability.get(flower_shop.id, False) for flower_shop in flower_shops]
        bouquets_availability.append((bouquet, ordered_availability))

    context = {
        'bouquets_availability': bouquets_availability,
        'shops_addresses': shops_addresses,
    }
    return render(request, template_name='bouquets-availability.html', context=context)


@user_passes_test(is_florist, login_url='login')
def view_orders(request):
    orders = (
        Order.objects
        .select_related('bouquet')
        .filter(status__in=[Order.Status.created, Order.Status.composing, Order.Status.composed])
    )
    sorted_orders = sorted(
        orders,
        key=lambda x: ([Order.Status.created, Order.Status.composing, Order.Status.composed].index(x.status), x.id)
    )
    context = {'orders': [serialize_order(order) for order in sorted_orders]}
    return render(request, template_name='orders.html', context=context)


def serialize_order(order):
    return {
        'id': order.id,
        'status': order.status,
        'bouquet_name': order.bouquet.name,
        'client_name': order.client_name,
        'phone': order.phone,
        'delivery_address': order.delivery_address,
        'delivery_window': order.delivery_window,
        'comment': order.comment,
        'price': order.price,
    }


def change_status(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    if order.status == Order.Status.created:
        order.status = Order.Status.composing
    elif order.status == Order.Status.composing:
        order.status = Order.Status.composed
    order.save(update_fields=['status'])

    return view_orders(request)
