from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import render, redirect
from rest_framework.viewsets import ModelViewSet
from django.db.models.query import Prefetch

from .forms import ConsultationForm
from .models import Bouquet
from .models import Consultation
from .models import FlowerShop
from .models import BouquetItemsInBouquet
from .serializers import ConsultationSerializer


def index(request: WSGIRequest) -> HttpResponse:
    bouquets = Bouquet.objects.filter(is_recommended=True)
    flower_shops = FlowerShop.objects.all()
    context = {
        'bouquets': bouquets,
        'flower_shops': flower_shops,
        'success_alert_style': 'none',
        'form': ConsultationForm()
    }
    if request.method == 'POST':
        context['form'] = ConsultationForm(request.POST)
        if context['form'].is_valid():
            context['form'].save()
            context['success_alert_style'] = 'block'

    return render(request, 'index.html', context)

def card(request: WSGIRequest, bouquet_id: int) -> HttpResponse:
    # selected_bouquet = Bouquet.objects.get(id=bouquet_id)
    bouquets = Bouquet.objects.prefetch_related(
        Prefetch(
          "items",
          queryset=BouquetItemsInBouquet.objects.filter(bouquet=bouquet_id),
          to_attr="curent_items",
       )
    )
    selected_bouquet = bouquets.get(id=bouquet_id)
    # bouquet_items = BouquetItemsInBouquet.objects.filter(bouquet=selected_bouquet).all()
    bouquet_items = selected_bouquet.curent_items
    price_order = float(selected_bouquet.price)
    # link_order = f'https://arsenalpay.ru/widget.html?widget=13711&destination=12345&amount={price_order}'
    context = {
        'bouquet': selected_bouquet,
        'bouquet_items': bouquet_items,
        'success_alert_style': 'none',
        'form': ConsultationForm(),
        # 'link_order': link_order,
    }
    if request.method == 'POST':
        context['form'] = ConsultationForm(request.POST)
        if context['form'].is_valid():
            context['form'].save()
            context['success_alert_style'] = 'block'
    return render(request, 'card.html', context)


def catalog(request: WSGIRequest) -> HttpResponse:
    bouquets =Bouquet.objects.all()
    context = {
        'bouquets': bouquets,
        'success_alert_style': 'none',
        'form': ConsultationForm()
    }
    if request.method == 'POST':
        context['form'] = ConsultationForm(request.POST)
        if context['form'].is_valid():
            context['form'].save()
            context['success_alert_style'] = 'block'
    return render(request, 'catalog.html', context)


def consultation(request: WSGIRequest) -> HttpResponse:
    context = {}
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
    context = {}
    return render(request, 'quiz.html', context)


def quiz_step(request: WSGIRequest) -> HttpResponse:
    context = {}
    return render(request, 'quiz-step.html', context)


def result(request: WSGIRequest) -> HttpResponse:
    context = {}
    return render(request, 'result.html', context)
