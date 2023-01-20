from datetime import datetime, time, timedelta
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from flowerapp.models import Bouquet
from flowerapp.models import DeliveryWindow
from flowerapp.models import Order

User = get_user_model()


def rand_datetime(dt_start: datetime, dt_end: datetime) -> datetime:
    """Returns a random datetime between start and end."""

    return datetime.fromtimestamp(random.randrange(
        round(dt_start.timestamp()), round(dt_end.timestamp())
    ))


def rand_time(t_start: time, t_end: time) -> time:
    """Returns a random time between start and end."""

    dt0 = datetime.fromtimestamp(87000)
    s = datetime.combine(dt0, t_start)
    e = datetime.combine(dt0 if t_start < t_end else dt0 + timedelta(days=1), t_end)
    return rand_datetime(s, e).time()


class Command(BaseCommand):
    help = "Create test orders"

    def handle(self, *args, **kwargs):
        delivery_windows = list(DeliveryWindow.objects.all())
        bouquets = list(Bouquet.objects.all())

        for i in range(5):
            user = User(username=f'florist_{i}', password=f'Passw0rd_{i}_!£3', role=User.Role.florist)
            user.save()

        for i in range(10):
            user = User(username=f'courier_{i}', password=f'Passw0rd_{i}_!£4', role=User.Role.courier)
            user.save()

        florists = list(User.objects.filter(role=User.Role.florist))
        couriers = list(User.objects.filter(role=User.Role.courier))

        clients = []
        for i in range(5000):
            clients.append({
                'client_name': f'client_name_{i}',
                'phone': f'+{79000000000 + i}',
                'delivery_address': f'delivery_address_{i}',
                'email': f'email_{i}'
            })

        today = timezone.now().date()
        four_years_ago = 365 * 4

        work_stime = time(hour=8, minute=0)
        work_etime = time(hour=21, minute=0)

        for day_delta in range(-four_years_ago, 0):
            day = today + timezone.timedelta(days=day_delta)
            day_orders_count = random.randint(5, 40)
            orders = []
            for _ in range(day_orders_count):
                order_time = rand_time(work_stime, work_etime)
                order_datetime = datetime.combine(day, order_time)

                compose_minutes = random.randint(30, 120)
                compose_datetime = datetime.combine(day, work_stime)
                if (datetime.combine(day, work_etime) - order_datetime).seconds > compose_minutes * 60:
                    compose_datetime = datetime.combine(day + timedelta(days=1), work_stime)

                delivery_minutes = random.randint(30, 120)
                delivery_datetime = compose_datetime + timezone.timedelta(minutes=delivery_minutes)

                client = random.choice(clients)

                paid = random.choice([True, True, True, True, True, True, True, True, True, True, False])
                order_data = {
                    'composed_at': str(compose_datetime),
                    'delivered_at': str(delivery_datetime),
                    'status': Order.Status.delivered,
                    'florist': random.choice(florists),
                    'courier': random.choice(couriers)

                }
                if not paid:
                    order_data = {
                        'composed_at': None,
                        'delivered_at': None,
                        'status': Order.Status.cancelled,
                        'florist': None,
                        'courier': None
                    }

                bouquet = random.choice(bouquets)
                order = Order(
                    bouquet=bouquet,
                    price=bouquet.price,
                    client_name=client['client_name'],
                    phone=client['phone'],
                    delivery_address=client['delivery_address'],
                    delivery_window=random.choice(delivery_windows),
                    email=client['email'],
                    paid=paid,
                    composed_at=order_data['composed_at'],
                    delivered_at=order_data['delivered_at'],
                    status=order_data['status'],
                    florist=order_data['florist'],
                    courier=order_data['courier'],
                )
                order.created_at = str(order_datetime)
                orders.append(order)
            Order.objects.bulk_create(orders)
            print(f'day={day} handled, {len(orders)} orders')
