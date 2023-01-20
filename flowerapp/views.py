from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone

from .forms import ConsultationForm
from .forms import CustomEventForm
from .models import Bouquet
from .models import Consultation
from .models import Event
from .models import FlowerShop
from .models import BouquetItemsInBouquet

from django.db.models import Prefetch


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
            response = redirect('index')
            expires_seconds = 3
            expires = timezone.now() + timezone.timedelta(seconds=expires_seconds)
            response.set_cookie('success_alert_style', 'block', expires=expires)
            return response

    return render(request, 'index.html', context)


def card(request: WSGIRequest, bouquet_id: int) -> HttpResponse:
    success_alert_style = request.COOKIES.get('success_alert_style', 'none')
    bouquets = Bouquet.objects.prefetch_related(
        Prefetch(
            "items",
            queryset=BouquetItemsInBouquet.objects.filter(bouquet=bouquet_id),
            to_attr="curent_items",
        )
    )
    selected_bouquet = bouquets.get(id=bouquet_id)

    bouquet_items = selected_bouquet.curent_items
    context = {
        'bouquet': selected_bouquet,
        'bouquet_items': bouquet_items,
        'success_alert_style': success_alert_style,
        'form': ConsultationForm(class_name='consultation__form_input'),
    }
    if request.method == 'POST':
        context['form'] = ConsultationForm(request.POST, class_name='consultation__form_input')
        if context['form'].is_valid():
            context['form'].save()
            response = redirect('card', bouquet_id=bouquet_id)
            expires_seconds = 3
            expires = timezone.now() + timezone.timedelta(seconds=expires_seconds)
            response.set_cookie('success_alert_style', 'block', expires=expires)
            return response
    return render(request, 'card.html', context)


def catalog(request: WSGIRequest) -> HttpResponse:
    success_alert_style = request.COOKIES.get('success_alert_style', 'none')
    bouquets = Bouquet.objects.all()
    context = {
        'bouquets': bouquets,
        'success_alert_style': success_alert_style,
        'form': ConsultationForm(class_name='consultation__form_input'),
    }
    if request.method == 'POST':
        context['form'] = ConsultationForm(request.POST, class_name='consultation__form_input')
        if context['form'].is_valid():
            context['form'].save()
            response = redirect('catalog')
            expires_seconds = 3
            expires = timezone.now() + timezone.timedelta(seconds=expires_seconds)
            response.set_cookie('success_alert_style', 'block', expires=expires)
            return response
    return render(request, 'catalog.html', context)


def consultation(request: WSGIRequest) -> HttpResponse:
    context = {'form': ConsultationForm(class_name='singUpConsultation__form_input')}

    if request.method == 'POST':
        context['form'] = ConsultationForm(request.POST, class_name='singUpConsultation__form_input')
        if context['form'].is_valid():
            context['form'].save()
            response = redirect('index')
            expires_seconds = 3
            expires = timezone.now() + timezone.timedelta(seconds=expires_seconds)
            response.set_cookie('success_alert_style', 'block', expires=expires)
            return response
    return render(request, 'consultation.html', context)


def order(request: WSGIRequest, bouquet_id: int) -> HttpResponse:
    selected_bouquet = Bouquet.objects.get(id=bouquet_id)
    price_order = float(selected_bouquet.price)
    link_order = f'https://arsenalpay.ru/widget.html?widget=13711&destination=12345&amount={price_order}'
    context = {
        'link_order': link_order,
        'id': bouquet_id,
    }
    return render(request, 'order.html', context)


def order_step(request: WSGIRequest) -> HttpResponse:
    context = {}
    return render(request, 'order-step.html', context)


def quiz(request: WSGIRequest) -> HttpResponse:
    event = request.GET.get('event', None)
    price_from = request.GET.get('price_from', None)
    price_to = request.GET.get('price_to', None)
    custom = request.GET.get('custom', 'false').lower() == 'true'
    step = 1
    if event:
        step = 2
    context = {'events': Event.objects.all(), 'step': step, 'event': event, 'custom': custom}
    if step == 1:
        context['form'] = CustomEventForm()
    elif step == 2 and custom:
        context['form'] = CustomEventForm(request.GET)
        context['anchor'] = '#consultation'
        if context['form'].is_valid():
            for name, value in context['form'].cleaned_data.items():
                context[name] = str(value)
        else:
            context['step'] = 1
            return render(request, 'quiz.html', context)

    if event and price_from and price_to:
        if not custom:
            query_string = urlencode({'event': event, 'price_from': price_from, 'price_to': price_to})
            return redirect(reverse('result') + '?' + query_string)
        budget = f'От {price_from} до {price_to}'
        consultation_obj = Consultation(
            client_name=context['client_name'],
            phone=context['phone'],
            event=context['event'],
            budget=budget,
        )
        consultation_obj.save()
        response = redirect('index')
        expires_seconds = 3
        expires = timezone.now() + timezone.timedelta(seconds=expires_seconds)
        response.set_cookie('success_alert_style', 'block', expires=expires)
        return response

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
    if price_from:
        try:
            float(price_from)
            params['price__gte'] = price_from
        except ValueError:
            pass
    if price_to:
        try:
            float(price_to)
            params['price__lte'] = price_to
        except ValueError:
            pass

    if params:
        suitable_bouquets = Bouquet.objects.filter(**params)
        if suitable_bouquets:
            selected_bouquet = suitable_bouquets.order_by('-price').prefetch_related('items', 'items__item')[0]
        else:
            # else for avoid extra queries
            selected_bouquet = Bouquet.objects.order_by('-price').prefetch_related('items', 'items__item')[0]
    else:
        # else for avoid extra queries
        selected_bouquet = Bouquet.objects.order_by('-price').prefetch_related('items', 'items__item')[0]

    context = {'bouquet': selected_bouquet}
    return render(request, 'result.html', context)
