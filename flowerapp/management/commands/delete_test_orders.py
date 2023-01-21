from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from flowerapp.models import Order

User = get_user_model()


class Command(BaseCommand):
    help = "Delete test orders"

    def handle(self, *args, **kwargs):
        Order.objects.filter(delivery_address__contains='delivery_address_').delete()
        User.objects.filter(username__contains='florist_').delete()
        User.objects.filter(username__contains='courier_').delete()
