from django.shortcuts import render

from .models import Bouquet
from .models import FlowerShop
from .models import BouquetItemsInBouquet


def index(request):
    bouquets = Bouquet.objects.filter(is_recommended=True)
    flower_shops = FlowerShop.objects.all()
    context = {'bouquets': bouquets, 'flower_shops': flower_shops}
    return render(request, 'index.html', context)


def catalog(request):
    bouquets =Bouquet.objects.all()
    context = {'bouquets': bouquets}
    return render(request, 'catalog.html', context)


def card(request, bouquet_id):
    selected_bouquet = Bouquet.objects.get(id=bouquet_id)
    bouquet_items = BouquetItemsInBouquet.objects.filter(bouquet=selected_bouquet).all()
    context = {
        'bouquet': selected_bouquet,
        'bouquet_items': bouquet_items,
    }
    return render(request, 'card.html', context)
