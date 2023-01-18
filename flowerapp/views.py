from django.shortcuts import render

from .models import Bouquet
from .models import FlowerShop


def index(request):
    bouquets = Bouquet.objects.filter(is_recommended=True)
    flower_shops = FlowerShop.objects.all()
    context = {'bouquets': bouquets, 'flower_shops': flower_shops}
    return render(request, 'index.html', context)
