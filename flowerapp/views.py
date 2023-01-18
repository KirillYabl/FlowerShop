from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import render, redirect
from rest_framework.viewsets import ModelViewSet

from .models import Bouquet
from .models import Consultation
from .models import FlowerShop
from .serializers import ConsultationSerializer


def index(request: WSGIRequest) -> HttpResponse:
    print(request.GET)
    bouquets = Bouquet.objects.filter(is_recommended=True)
    flower_shops = FlowerShop.objects.all()
    context = {
        'bouquets': bouquets,
        'flower_shops': flower_shops,
        'success_alert_style': request.GET.get('success_alert_style', 'none')
    }
    return render(request, 'index.html', context)


class ConsultationViewSet(ModelViewSet):
    queryset = Consultation.objects.all()
    serializer_class = ConsultationSerializer

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        response = redirect('index')
        response['Location'] += '?success_alert_style=block'
        return response
