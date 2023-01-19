from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils import timezone
from rest_framework.viewsets import ModelViewSet

from .forms import ConsultationForm
from .models import Bouquet
from .models import FlowerShop
from .models import BouquetItemsInBouquet


def index(request: WSGIRequest) -> HttpResponse:
    success_alert_style = request.COOKIES.get('success_alert_style', 'none')

    bouquets = Bouquet.objects.filter(is_recommended=True)
    flower_shops = FlowerShop.objects.all()
    context = {
        'bouquets': bouquets,
        'flower_shops': flower_shops,
        'success_alert_style': success_alert_style,
        'form': ConsultationForm()
    }
    if request.method == 'POST':
        context['form'] = ConsultationForm(request.POST)
        if context['form'].is_valid():
            context['form'].save()
            response = redirect('index')
            expires_seconds = 3
            expires = timezone.now() + timezone.timedelta(seconds=expires_seconds)
            response.set_cookie('success_alert_style', 'block', expires=expires)
            return response

    return render(request, 'index.html', context)


def card(request: WSGIRequest, bouquet_id: int) -> HttpResponse:
    selected_bouquet = Bouquet.objects.get(id=bouquet_id)
    bouquet_items = BouquetItemsInBouquet.objects.filter(bouquet=selected_bouquet).all()
    context = {
        'bouquet': selected_bouquet,
        'bouquet_items': bouquet_items,
    }
    return render(request, 'card.html', context)


def catalog(request: WSGIRequest) -> HttpResponse:
    bouquets = Bouquet.objects.all()
    context = {'bouquets': bouquets}
    return render(request, 'catalog.html', context)


def consultation(request: WSGIRequest) -> HttpResponse:
    context = {}
    return render(request, 'consultation.html', context)


def order(request: WSGIRequest) -> HttpResponse:
    context = {}
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
