from django.shortcuts import render, redirect
from rest_framework.viewsets import ModelViewSet

from .models import Bouquet
from .models import Consultation
from .models import FlowerShop
from .serializers import ConsultationSerializer


def index(request):
    bouquets = Bouquet.objects.filter(is_recommended=True)
    flower_shops = FlowerShop.objects.all()
    context = {'bouquets': bouquets, 'flower_shops': flower_shops}
    return render(request, 'index.html', context)


class ConsultationViewSet(ModelViewSet):
    queryset = Consultation.objects.all()
    serializer_class = ConsultationSerializer

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return redirect('index')
