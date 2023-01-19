from django.shortcuts import render

from .models import Bouquet
from .models import FlowerShop


def index(request):
    bouquets = Bouquet.objects.filter(is_recommended=True)
    flower_shops = FlowerShop.objects.all()
    context = {'bouquets': bouquets, 'flower_shops': flower_shops}
    return render(request, 'index.html', context)


def catalog(request):
    bouquets =Bouquet.objects.all()
    context = {'bouquets': bouquets}
    return render(request, 'catalog.html', context)


def card(request):
    return render(request, 'card.html')
