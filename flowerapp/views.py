import datetime
from typing import Union
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
from django.conf import settings
from django.db import models
from django.db.models import Sum, Count, F, Case, When, Value, Avg, Min
from django.db.models.functions import Concat
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone

from .forms import ConsultationForm
from .forms import CustomEventForm
from .forms import OrderForm
from .models import Bouquet
from .models import Consultation
from .models import DeliveryWindow
from .models import Event
from .models import FlowerShop
from .models import Order


def redirect_with_success_alert(view_name: str, **kwargs) -> HttpResponse:
    """Set cookie success_alert_style and redirect to page with params in kwargs."""
    response = redirect(view_name, **kwargs)
    expires_seconds = 3
    expires = timezone.now() + timezone.timedelta(seconds=expires_seconds)
    response.set_cookie('success_alert_style', 'block', expires=expires)
    return response


class TimedeltaWrapper:
    """Wrapper for datetime.timedelta which can return hours and minutes (reminded from hours).

    If td is None return "---"
    Wrapper needs for django template
    """

    def __init__(self, td: Union[datetime.timedelta, None]):
        self.td = td

    @property
    def hours(self):
        if self.td:
            return self.td.seconds // 3600
        return '---'

    @property
    def minutes60(self):
        if self.td:
            return (self.td.seconds // 60) % 60
        return '---'


def index(request: WSGIRequest) -> HttpResponse:
    success_alert_style = request.COOKIES.get('success_alert_style', 'none')

    bouquets = Bouquet.objects.filter(is_recommended=True)
    flower_shops = FlowerShop.objects.all()
    context = {
        'bouquets': bouquets,
        'flower_shops': flower_shops,
        'success_alert_style': success_alert_style,
        'form': ConsultationForm(class_name='consultation__form_input')
    }
    if request.method == 'POST':
        context['form'] = ConsultationForm(request.POST, class_name='consultation__form_input')
        if context['form'].is_valid():
            context['form'].save()
            return redirect_with_success_alert('index')

    return render(request, 'index.html', context)


def card(request: WSGIRequest, bouquet_id: int) -> HttpResponse:
    success_alert_style = request.COOKIES.get('success_alert_style', 'none')
    bouquets = Bouquet.objects.prefetch_related('items', 'items__item')
    selected_bouquet = bouquets.get(id=bouquet_id)

    context = {
        'bouquet': selected_bouquet,
        'success_alert_style': success_alert_style,
        'form': ConsultationForm(class_name='consultation__form_input'),
    }
    if request.method == 'POST':
        context['form'] = ConsultationForm(request.POST, class_name='consultation__form_input')
        if context['form'].is_valid():
            context['form'].save()
            return redirect_with_success_alert('card', bouquet_id=bouquet_id)
    return render(request, 'card.html', context)


def catalog(request: WSGIRequest) -> HttpResponse:
    success_alert_style = request.COOKIES.get('success_alert_style', 'none')
    bouquets = Bouquet.objects.all()
    count_items = len(bouquets)
    context = {
        'bouquets': bouquets,
        'count_items': count_items,
        'success_alert_style': success_alert_style,
        'form': ConsultationForm(class_name='consultation__form_input'),
    }
    if request.method == 'POST':
        context['form'] = ConsultationForm(request.POST, class_name='consultation__form_input')
        if context['form'].is_valid():
            context['form'].save()
            return redirect_with_success_alert('catalog')
    return render(request, 'catalog.html', context)


def consultation(request: WSGIRequest) -> HttpResponse:
    context = {'form': ConsultationForm(class_name='singUpConsultation__form_input')}

    if request.method == 'POST':
        context['form'] = ConsultationForm(request.POST, class_name='singUpConsultation__form_input')
        if context['form'].is_valid():
            context['form'].save()
            return redirect_with_success_alert('index')
    return render(request, 'consultation.html', context)


def order(request: WSGIRequest, bouquet_id: int) -> HttpResponse:
    link_pay = settings.LINK_PAY

    selected_bouquet = Bouquet.objects.get(id=bouquet_id)
    price_order = float(selected_bouquet.price)
    link_order = f'{link_pay}{price_order}'

    context = {
        'link_order': link_order,
        'bouquet': selected_bouquet,
        'form': OrderForm(),
    }

    if request.method == 'POST':
        context['form'] = OrderForm(request.POST)
        if context['form'].is_valid():
            cleaned_inputs = context['form'].cleaned_data
            delivery_window = DeliveryWindow.objects.get(id=int(cleaned_inputs['delivery_window']))

            new_order = Order.objects.create(
                bouquet=selected_bouquet,
                price=price_order,
                client_name=cleaned_inputs['client_name'],
                phone=cleaned_inputs['phone'],
                delivery_address=cleaned_inputs['delivery_address'],
                delivery_window=delivery_window,
                paid=True
            )
            new_order.save()

            response = redirect(link_order)
            return response

    return render(request, 'order.html', context)


def quiz(request: WSGIRequest) -> HttpResponse:
    event = request.GET.get('event', None)
    price = request.GET.get('price', None)
    custom = request.GET.get('custom', 'false').lower() == 'true'

    step = 2 if event else 1
    context = {'events': Event.objects.all(), 'step': step, 'event': event, 'custom': custom}

    if step == 2 and custom:
        context['form'] = CustomEventForm()
        context['anchor'] = '#consultation'

    if event and price:
        price_from = price.split('-')[0]
        price_to = price.split('-')[-1]

        if not custom:
            query_string = urlencode({'event': event, 'price_from': price_from, 'price_to': price_to})
            return redirect(reverse('result') + '?' + query_string)

        context['form'] = CustomEventForm(request.GET)
        context['anchor'] = '#consultation'
        if context['form'].is_valid():
            for name, value in context['form'].cleaned_data.items():
                context[name] = str(value)
        else:
            return render(request, 'quiz.html', context)
        budget = f'От {price_from} до {price_to}'
        consultation_obj = Consultation(
            client_name=context['client_name'],
            phone=context['phone'],
            event=context['event'],
            budget=budget,
        )
        consultation_obj.save()
        return redirect_with_success_alert('index')

    return render(request, 'quiz.html', context)


def result(request: WSGIRequest) -> HttpResponse:
    event = request.GET.get('event', None)
    price_from = request.GET.get('price_from', None)
    price_to = request.GET.get('price_to', None)

    context = {'bouquet': Bouquet.objects.get_recommended_bouquet(event, price_from, price_to)}
    return render(request, 'result.html', context)


@login_required
def stats(request: WSGIRequest) -> HttpResponse:
    period = request.GET.get('period', 'all')
    bouquet = request.GET.get('bouquet', 'any')
    orders = Order.objects.exclude(status=Order.Status.cancelled)
    consultations = Consultation.objects.all()
    top_n = 5

    filter_params = {}

    if period in Order.DashboardFilterPeriod.names:
        filter_params.update(**Order.dashboard_period_filters[period])

    # these stats should compute without bouquet filter
    consultations = consultations.filter(**filter_params)
    top_clients = orders.filter(**filter_params).get_top_n_clients(top_n)
    top_bouquets = orders.filter(**filter_params).get_top_n_bouquets(top_n)

    if bouquet != 'any':
        try:
            int(bouquet)
            bouquet = Bouquet.objects.get(id=int(bouquet))
            filter_params['bouquet'] = bouquet
        except (ValueError, Bouquet.DoesNotExist):
            pass

    orders = orders.filter(**filter_params)

    try:
        most_popular_window = orders.select_related('delivery_window').values('delivery_window__name').annotate(
            num=Count('delivery_window__name')
        ).order_by('-num')[0]['delivery_window__name']
    except IndexError:
        most_popular_window = 'Не определено'

    orders_dt_aggregated = orders.get_order_points_avg()
    by_hours_distribution = orders.get_by_hours_distribution()
    by_time_distribution = orders.get_by_time_distribution(period)

    period_choices = [
        {'name': name, 'value': value}
        for name, value
        in zip(Order.DashboardFilterPeriod.names, Order.DashboardFilterPeriod.values)
    ]

    context = {
        'period_choices': period_choices,
        'bouquets': Bouquet.objects.all(),
        'orders_sum': orders.aggregate(orders_sum=Sum('price'))['orders_sum'],
        'orders_count': orders.count(),
        'unique_clients_count': orders.values_list('phone', flat=True).distinct().count(),
        'consultations_count': consultations.count(),
        'order_to_delivery_avg_time': TimedeltaWrapper(orders_dt_aggregated['order_to_delivery_avg_time']),
        'order_to_compose_avg_time': TimedeltaWrapper(orders_dt_aggregated['order_to_compose_avg_time']),
        'compose_to_delivery_avg_time': TimedeltaWrapper(orders_dt_aggregated['compose_to_delivery_avg_time']),
        'most_popular_window': most_popular_window,
        'by_hours_distribution': by_hours_distribution,
        'by_time_distribution': by_time_distribution,
        'top_bouquets': top_bouquets,
        'top_clients': top_clients
    }
    return render(request, 'stats.html', context)
