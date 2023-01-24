import datetime
from typing import Any

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import F, Count, Min, Case, When, Value, Avg, Sum
from django.db.models.functions import TruncDate, Concat
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

User = get_user_model()


class Event(models.Model):
    name = models.CharField('название', max_length=200, unique=True)

    class Meta:
        verbose_name = 'событие для букета'
        verbose_name_plural = 'события для букета'

    def __str__(self):
        return self.name


class BouquetQuerySet(models.QuerySet):
    def get_recommended_bouquet(self, event: str, price_from: str, price_to: str) -> 'Bouquet':
        """
        Get bouquet by recommendation algorithm

        Algorithm: filter by event and price range and return most expensive bouquet after filter
        If no bouquets after filter return just most expensive bouquet
        """
        params = {}
        if event:
            try:
                Event.objects.get(id=event)
                params['events__id__in'] = event
            except Event.DoesNotExist:
                pass

        for price, price_lookup in {price_from: 'gte', price_to: 'lte'}.items():
            if price:
                try:
                    float(price)
                    params[f'price__{price_lookup}'] = price
                except ValueError:
                    pass

        recommended_bouquets = self.filter(**params).order_by(
            '-price').prefetch_related('items', 'items__item')
        all_bouquets = self.order_by('-price').prefetch_related('items', 'items__item')

        # economy 1 query because of lazy QuerySet and lazy python logic if recommended_bouquets exists
        return recommended_bouquets.first() or all_bouquets.first()


class Bouquet(models.Model):
    name = models.CharField('название', max_length=100, unique=True)
    description = models.TextField('описание')
    photo = models.ImageField('фото')
    price = models.DecimalField('цена', max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    height_cm = models.PositiveSmallIntegerField(
        'высота',
        validators=[MinValueValidator(0)],
        help_text='задается в сантиметрах'
    )
    width_cm = models.PositiveSmallIntegerField(
        'ширина',
        validators=[MinValueValidator(0)],
        help_text='задается в сантиметрах'
    )
    events = models.ManyToManyField(Event)
    is_recommended = models.BooleanField('рекомендованный', default=False)

    objects = BouquetQuerySet.as_manager()

    class Meta:
        verbose_name = 'букет'
        verbose_name_plural = 'букеты'

    def __str__(self):
        return self.name


class BouquetItem(models.Model):
    name = models.CharField('название', max_length=200, unique=True)
    bouquets = models.ManyToManyField(Bouquet, through='BouquetItemsInBouquet')

    class Meta:
        verbose_name = 'элемент букета'
        verbose_name_plural = 'элементы букетов'

    def __str__(self):
        return self.name


class BouquetItemsInBouquet(models.Model):
    bouquet = models.ForeignKey(Bouquet, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(BouquetItem, related_name='bouquet_relations', on_delete=models.CASCADE)
    count = models.PositiveSmallIntegerField('количество', validators=[MinValueValidator(1)], default=1)

    class Meta:
        verbose_name = 'элемент букета в букете'
        verbose_name_plural = 'элементы букета в букете'
        unique_together = [['bouquet', 'item']]

    def __str__(self):
        return f'{self.item} в {self.bouquet} ({self.count} шт.)'


class FlowerShop(models.Model):
    address = models.CharField('адрес', max_length=200, unique=True)
    phone = PhoneNumberField('контактный номер', region='RU', blank=True)  # TODO: migration for remove blank

    class Meta:
        verbose_name = 'магазин цветов'
        verbose_name_plural = 'магазины цветов'

    def __str__(self):
        return self.address


class FlowerShopCatalogItem(models.Model):
    flower_shop = models.ForeignKey(
        FlowerShop,
        related_name='catalog_items',
        verbose_name='магазин цветов',
        on_delete=models.CASCADE,
    )
    bouquet = models.ForeignKey(
        Bouquet,
        on_delete=models.CASCADE,
        related_name='catalog_items',
        verbose_name='букет',
    )
    availability = models.BooleanField(
        'в наличии',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт каталога магазина цветов'
        verbose_name_plural = 'пункты каталога магазина цветов'
        unique_together = [['flower_shop', 'bouquet']]

    def __str__(self):
        return f'{self.flower_shop.address} - {self.bouquet.name}'


class DeliveryWindow(models.Model):
    name = models.CharField('название', max_length=200, unique=True)
    from_hour = models.PositiveSmallIntegerField(
        'доставить с',
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        null=True,
        blank=True
    )
    to_hour = models.PositiveSmallIntegerField(
        'доставить до',
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'окно доставки'
        verbose_name_plural = 'окна доставки'
        unique_together = [['from_hour', 'to_hour']]

    def __str__(self):
        return self.name


class OrderQuerySet(models.QuerySet):
    def get_by_hours_distribution(self) -> list[dict[str, Any]]:
        """Get distribution of order hour and percent of all orders in these hours through all orders in self."""
        by_hours_distribution = list(self.annotate(hour=F('created_at__hour')).values('hour').annotate(
            num=Count('hour')).order_by('hour'))
        all_count = sum([item['num'] for item in by_hours_distribution])
        return [
            {
                'hour': item['hour'],
                'percent': str(round((item['num'] / all_count) * 100, 1)).replace(',', '.')
            }
            for item
            in by_hours_distribution
        ]

    def get_by_time_distribution(self, period: str) -> models.QuerySet:
        """Get distribution of time unit (depends on period parameter) and count of orders"""
        first_order_dt = self.aggregate(dt=Min('created_at'))['dt'] or timezone.now()
        show_days_maximal_days_limit = 120
        show_months_maximal_days_limit = 365 * 2

        show_hours = period == Order.DashboardFilterPeriod.today.name
        show_days = period in (
            Order.DashboardFilterPeriod.week.name,
            Order.DashboardFilterPeriod.month.name,
            Order.DashboardFilterPeriod.this_month.name,
            Order.DashboardFilterPeriod.previous_month.name,
        ) or (timezone.now() - first_order_dt).days < show_days_maximal_days_limit
        show_months = period in (
            Order.DashboardFilterPeriod.year.name,
            Order.DashboardFilterPeriod.this_year.name,
            Order.DashboardFilterPeriod.previous_year.name,
        ) or (timezone.now() - first_order_dt).days < show_months_maximal_days_limit

        if show_hours:
            annotate = F('created_at__hour')
        elif show_days:
            annotate = F('created_at__date')
        elif show_months:
            annotate = Case(
                # no need add leading zero
                When(
                    created_at__month__in=[10, 11, 12],
                    # concat for right ordering in case of different years, for example 2022_12 and 2023_01
                    then=Concat(
                        F('created_at__year'), Value('.'), F('created_at__month'),
                        output_field=models.CharField()
                    )
                ),
                # need add leading zero
                When(
                    created_at__month__in=[i for i in range(1, 10)],  # first 9 months
                    # concat for right ordering in case of different years, for example 2022_12 and 2023_01
                    then=Concat(
                        F('created_at__year'), Value('.0'), F('created_at__month'),
                        output_field=models.CharField()
                    )
                )
            )
        else:
            annotate = F('created_at__year')

        return self.annotate(t=annotate).values('t').annotate(num=Count('t')).order_by('t')

    def get_order_points_avg(self) -> models.QuerySet:
        """Compute avg time between each pair from points of order: create time, compose time, delivery time"""
        work_day_start = datetime.time(8, 0, tzinfo=timezone.get_current_timezone())
        return self.annotate(
            delivered_date=F('delivered_at__date'),
            composed_date=F('composed_at__date'),
            created_date=F('created_at__date'),
            delivered_time=F('delivered_at__time'),
            composed_time=F('composed_at__time'),
        ).annotate(
            # if order was delivered in next day from created, we will
            # approve then courier start delivery in the start of work day
            order_to_delivery_time=Case(
                When(delivered_date=F('created_date'), then=F('delivered_at') - F('created_at')),
                When(delivered_date__gt=F('created_date'),
                     then=F('delivered_time') - work_day_start),
            ),
            # if order was composed in next day from created, we will
            # approve then florist start compose in the start of work day
            order_to_compose_time=Case(
                When(composed_date=F('created_date'), then=F('composed_at') - F('created_at')),
                When(composed_date__gt=F('created_date'),
                     then=F('composed_time') - work_day_start),
            ),
            # if order was delivered in next day from composed, we will
            # approve then courier start delivery in the start of work day
            compose_to_delivery_time=Case(
                When(delivered_date=F('composed_date'), then=F('delivered_at') - F('composed_at')),
                When(delivered_date__gt=F('composed_date'),
                     then=F('delivered_time') - work_day_start),
            ),
        ).aggregate(
            order_to_delivery_avg_time=Avg('order_to_delivery_time'),
            order_to_compose_avg_time=Avg('order_to_compose_time'),
            compose_to_delivery_avg_time=Avg('compose_to_delivery_time'),
        )

    def get_top_n_clients(self, n: int) -> models.QuerySet:
        """Get n top clients by sum of orders and count of orders"""
        return self.values('phone').annotate(
            order_sum=Sum('price'),
            order_cnt=Count('id')
        ).order_by('-order_sum', '-order_cnt')[:n]

    def get_top_n_bouquets(self, n: int) -> models.QuerySet:
        """Get n top bouquets by count of orders"""
        return self.select_related('bouquet').values('bouquet__name').annotate(
            orders_cnt=Count('id')
        ).order_by('-orders_cnt')[:n]


class Order(models.Model):
    class Status(models.TextChoices):
        created = 'создан'
        composing = 'собирается'
        composed = 'собран'
        delivering = 'доставляется'
        delivered = 'доставлен'
        cancelled = 'отменен'

    class DashboardFilterPeriod(models.TextChoices):
        all = 'За все время'
        today = 'Сегодня'
        week = 'За неделю'
        month = 'За месяц'
        year = 'За год'
        this_month = 'Этот месяц'
        this_year = 'Этот год'
        previous_month = 'Прошлый месяц'
        previous_year = 'Прошлый год'

    now_date = timezone.now().date()
    dashboard_period_filters = {
        'all': {},
        'today': {'created_at__date': now_date},
        'week': {'created_at__date__gt': now_date - timezone.timedelta(days=7)},
        'month': {'created_at__date__gt': now_date - timezone.timedelta(days=31)},
        'year': {'created_at__date__gt': now_date - timezone.timedelta(days=365)},
        'this_month': {
            'created_at__month': now_date.month,
            'created_at__year': now_date.year,
        },
        'this_year': {'created_at__year': now_date.year},
        'previous_month': {
            'created_at__month': now_date.month - 1 if now_date.month != 1 else 12,
            'created_at__year': now_date.year if now_date.month != 1 else now_date.year - 1
        },
        'previous_year': {'created_at__year': timezone.now().date().year - 1},
    }

    bouquet = models.ForeignKey(Bouquet, related_name='orders', on_delete=models.DO_NOTHING)
    price = models.DecimalField(  # price of bouquet can change
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    client_name = models.CharField('имя клиента', max_length=200)
    phone = PhoneNumberField('контактный номер', region='RU')
    delivery_address = models.CharField('адрес доставки', max_length=200)
    delivery_window = models.ForeignKey(
        DeliveryWindow,
        related_name='orders',
        on_delete=models.DO_NOTHING,
        null=True,  # null if ASAP
        blank=True
    )
    email = models.EmailField('email адрес', blank=True)
    paid = models.BooleanField('оплачен')
    comment = models.TextField('комментарий', blank=True)
    created_at = models.DateTimeField('дата и время создания заказа', default=timezone.now)
    composed_at = models.DateTimeField('дата и время сбора букета флористом', null=True, blank=True)
    delivered_at = models.DateTimeField('дата и время доставки букета', null=True, blank=True)
    status = models.CharField(
        'статус заказа',
        max_length=15,
        choices=Status.choices,
        default=Status.created,
        db_index=True
    )
    florist = models.ForeignKey(User, related_name='f_orders', on_delete=models.DO_NOTHING, null=True, blank=True)
    courier = models.ForeignKey(User, related_name='c_orders', on_delete=models.DO_NOTHING, null=True, blank=True)

    objects = OrderQuerySet.as_manager()

    def is_for_florist_statuses(self):
        return self.status in [self.Status.created, self.Status.composing]

    def is_for_courier_statuses(self):
        return self.status in [self.Status.composed, self.Status.delivering]

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
        indexes = [models.Index(TruncDate("created_at"), "created_at", name="order_created_at_date_idx")]

    def __str__(self):
        return f'Заказ {self.pk} ({self.created_at}), {self.bouquet} по адресу {self.delivery_address}'


class Consultation(models.Model):
    class Status(models.TextChoices):
        created = 'создана'
        consulted = 'оказана'
        cancelled = 'отменена (не доступен)'

    client_name = models.CharField('имя клиента', max_length=200)
    phone = PhoneNumberField('контактный номер', region='RU')
    created_at = models.DateTimeField('дата и время заказа консультации', default=timezone.now)
    consulted_at = models.DateTimeField('дата и время оказания консультации', null=True, blank=True)
    status = models.CharField(
        'статус консультации',
        max_length=30,
        choices=Status.choices,
        default=Status.created,
        db_index=True
    )
    event = models.CharField('повод', max_length=100, blank=True)
    budget = models.CharField('бюджет', max_length=100, blank=True)

    class Meta:
        verbose_name = 'консультация'
        verbose_name_plural = 'консультации'
        indexes = [models.Index(TruncDate("created_at"), "created_at", name="cons_created_at_date_idx")]

    def __str__(self):
        return f'Консультация {self.pk} ({self.created_at}), {self.phone} ({self.client_name})'
