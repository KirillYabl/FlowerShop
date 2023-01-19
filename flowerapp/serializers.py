from rest_framework import serializers

from .models import Consultation


class ConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = ['client_name', 'phone', 'consulted_at', 'status']
