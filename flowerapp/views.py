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
    params = {}

    if event:
        try:
            Event.objects.get(id=event)
            params['events__id__in'] = event
        except Event.DoesNotExist:
            pass

    for price, price_lookup in {price_from: 'gte', price_to: 'lte'}.items():
        if price:
            try:
                float(price)
                params[f'price__{price_lookup}'] = price
            except ValueError:
                pass

    # TODO: move recommendation algorithm in model QuerySet
    recommended_bouquets = Bouquet.objects.filter(**params).order_by('-price').prefetch_related('items', 'items__item')
    all_bouquets = Bouquet.objects.all().order_by('-price').prefetch_related('items', 'items__item')

    # economy 1 query because of lazy QuerySet and lazy python logic if recommended_bouquets exists
    selected_bouquet = recommended_bouquets.first() or all_bouquets.first()

    context = {'bouquet': selected_bouquet}
    return render(request, 'result.html', context)


@login_required
def stats(request: WSGIRequest) -> HttpResponse:
    period = request.GET.get('period', 'all')
    bouquet = request.GET.get('bouquet', 'any')
    orders = Order.objects.exclude(status=Order.Status.cancelled)
    consultations = Consultation.objects.all()

    filter_params = {}

    if period != 'all':
        if period == 'today':
            filter_params['created_at__date'] = timezone.now().date()
        elif period == 'week':
            filter_params['created_at__date__gt'] = timezone.now().date() - timezone.timedelta(days=7)
        elif period == 'month':
            filter_params['created_at__date__gt'] = timezone.now().date() - timezone.timedelta(days=31)
        elif period == 'year':
            filter_params['created_at__date__gt'] = timezone.now().date() - timezone.timedelta(days=365)
        elif period == 'this_month':
            filter_params['created_at__month'] = timezone.now().date().month
            filter_params['created_at__year'] = timezone.now().date().year
        elif period == 'this_year':
            filter_params['created_at__year'] = timezone.now().date().year
        elif period == 'previous_month':
            filter_params[
                'created_at__month'] = timezone.now().date().month - 1 if timezone.now().date().month != 1 else 12
            filter_params['created_at__year'] = timezone.now().date().year if filter_params[
                                                                                  'created_at__month'] != 12 else timezone.now().date().year - 1
        elif period == 'previous_year':
            filter_params['created_at__year'] = timezone.now().date().year - 1

    if filter_params:
        consultations = consultations.filter(**filter_params)
        orders_for_top = orders.filter(**filter_params)
        top_clients = orders_for_top.values('phone').annotate(
            order_sum=Sum('price'), order_cnt=Count('id')).order_by('-order_sum', '-order_cnt')[:5]
        top_bouquets = orders_for_top.select_related('bouquet').values('bouquet__name').annotate(
            orders_cnt=Count('id')).order_by('-orders_cnt')[:5]
    else:
        top_clients = orders.values('phone').annotate(order_sum=Sum('price'), order_cnt=Count('id')).order_by(
            '-order_sum', '-order_cnt')[:5]
        top_bouquets = orders.select_related('bouquet').filter(**filter_params).values('bouquet__name').annotate(
            orders_cnt=Count('id')).order_by('-orders_cnt')[:5]

    if bouquet != 'any':
        try:
            int(bouquet)
            bouquet = Bouquet.objects.get(id=int(bouquet))
            filter_params['bouquet'] = bouquet
        except (ValueError, Bouquet.DoesNotExist):
            pass

    if filter_params:
        orders = orders.filter(**filter_params)

    try:
        delivery_window_id = orders.values('delivery_window').annotate(
            num=Count('delivery_window')).order_by('-num')[0]['delivery_window']
        most_popular_window = DeliveryWindow.objects.get(id=delivery_window_id).name
    except IndexError:
        most_popular_window = 'Не определено'

    orders_dt_aggregated = orders.annotate(
        delivered_date=F('delivered_at__date'),
        composed_date=F('composed_at__date'),
        created_date=F('created_at__date'),
        delivered_time=F('delivered_at__time'),
        composed_time=F('composed_at__time'),
    ).annotate(
        order_to_delivery_time=Case(
            When(delivered_date=F('created_date'), then=F('delivered_at') - F('created_at')),
            When(delivered_date__gt=F('created_date'),
                 then=F('delivered_time') - datetime.time(8, 0, tzinfo=timezone.get_current_timezone())),
        ),
        order_to_compose_time=Case(
            When(composed_date=F('created_date'), then=F('composed_at') - F('created_at')),
            When(composed_date__gt=F('created_date'),
                 then=F('composed_time') - datetime.time(8, 0, tzinfo=timezone.get_current_timezone())),
        ),
        compose_to_delivery_time=Case(
            When(delivered_date=F('composed_date'), then=F('delivered_at') - F('composed_at')),
            When(delivered_date__gt=F('composed_date'),
                 then=F('delivered_time') - datetime.time(8, 0, tzinfo=timezone.get_current_timezone())),
        ),
    ).aggregate(
        order_to_delivery_avg_time=Avg('order_to_delivery_time'),
        order_to_compose_avg_time=Avg('order_to_compose_time'),
        compose_to_delivery_avg_time=Avg('compose_to_delivery_time'),
    )

    by_hours_distribution = list(orders.annotate(hour=F('created_at__hour')).values('hour').annotate(
        num=Count('hour')).order_by('hour'))
    all_count = sum([item['num'] for item in by_hours_distribution])
    by_hours_distribution = [
        {
            'hour': item['hour'],
            'percent': str(round((item['num'] / all_count) * 100, 1)).replace(',', '.')
        }
        for item
        in by_hours_distribution
    ]

    first_order = orders.aggregate(dt=Min('created_at'))['dt']
    if period == 'today':
        by_time_distribution = list(orders.annotate(t=F('created_at__hour')).values('t').annotate(
            num=Count('t')).order_by('t'))
    elif period in ('week', 'month', 'this_month', 'previous_month') or (timezone.now() - first_order).days < 120:
        by_time_distribution = list(orders.annotate(t=F('created_at__date')).values('t').annotate(
            num=Count('t')).order_by('t'))
    elif period in ('year', 'this_year', 'previous_year') or (timezone.now() - first_order).days < 365 * 2:
        by_time_distribution = list(orders.annotate(
            t=Case(
                When(
                    created_at__month__in=[10, 11, 12],
                    then=Concat(
                        F('created_at__year'), Value('.'), F('created_at__month'),
                        output_field=models.CharField()
                    )
                ),
                When(
                    created_at__month__in=[i for i in range(1, 10)],
                    then=Concat(
                        F('created_at__year'), Value('.0'), F('created_at__month'),
                        output_field=models.CharField()
                    )
                )
            )
        ).values('t').annotate(num=Count('t')).order_by('t'))
    else:
        by_time_distribution = list(orders.annotate(t=F('created_at__year')).values('t').annotate(
            num=Count('t')).order_by('t'))

    context = {
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
