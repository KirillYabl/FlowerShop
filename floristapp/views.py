from django import forms
from django.contrib.auth import authenticate, login, views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from flowerapp.models import Bouquet, FlowerShop, Order


class Login(forms.Form):
    username = forms.CharField(
        label='Логин',
        max_length=75,
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Укажите имя пользователя'
            }
        )
    )
    password = forms.CharField(
        label='Пароль',
        max_length=75,
        required=True,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Введите пароль'
            }
        )
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(
            request,
            'florist_login.html',
            context={'form': form}
        )

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect('floristapp:orders')
                return redirect('start_page')

        context={'form': form, 'ivalid': True}
        return render(request,'florist_login.html', context=context)


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('floristapp:login')


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

    context={
        'bouquets_availability': bouquets_availability,
        'shops_addresses': shops_addresses,
    }
    return render(request, template_name='bouquets-availability.html', context=context)


@user_passes_test(is_florist, login_url='login')
def view_orders(request):
    orders = (
        Order.objects
            .exclude(status__in=[Order.Status.delivered, Order.Status.cancelled])
            .order_by('-status', 'id')
    )
    context = {'orders': [serialize_order(order) for order in orders]} 
    return render(request, template_name='orders.html', context=context)


def serialize_order(order):
    return {
        'id': order.id,
        'status': order.status,
        'client_name': order.client_name,
        'phone': order.phone,
        'delivery_address': order.delivery_address,
        'comment': order.comment,
        'price': order.price,
    }
