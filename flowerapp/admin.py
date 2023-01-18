from django.templatetags.static import static
from django.contrib import admin
from django.shortcuts import reverse
from django.utils.html import format_html

from . import models as m


@admin.register(m.Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_display_links = ['name']
    search_fields = ['name']


@admin.register(m.FlowerShop)
class FlowerShopAdmin(admin.ModelAdmin):
    list_display = ['address']
    list_display_links = ['address']
    search_fields = ['address']


@admin.register(m.DeliveryWindow)
class DeliveryWindowAdmin(admin.ModelAdmin):
    list_display = ['name', 'from_hour', 'to_hour']
    list_display_links = ['name', 'from_hour', 'to_hour']
    search_fields = ['name']
    list_filter = ['from_hour', 'to_hour']


@admin.register(m.BouquetItem)
class BouquetItemAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_display_links = ['name']
    search_fields = ['name']
    list_filter = ['bouquets']


@admin.register(m.BouquetItemsInBouquet)
class BouquetItemsInBouquetAdmin(admin.ModelAdmin):
    list_display = ['bouquet', 'item', 'count']
    list_display_links = ['bouquet', 'item', 'count']
    list_filter = ['bouquet', 'item', 'count']


class BouquetItemsInBouquetInline(admin.TabularInline):
    model = m.BouquetItemsInBouquet


@admin.register(m.Bouquet)
class BouquetAdmin(admin.ModelAdmin):
    inlines = [BouquetItemsInBouquetInline]
    list_display = ['get_image_list_preview', 'name', 'price', 'height_cm', 'width_cm']
    list_display_links = ['name', 'price', 'height_cm', 'width_cm']
    search_fields = ['name', 'description', 'price']
    list_filter = ['price', 'height_cm', 'width_cm', 'events']

    readonly_fields = [
        'get_image_preview',
    ]

    class Media:
        css = {
            "all": (
                static("admin/flowerapp.css")
            )
        }

    def get_image_preview(self, obj):
        if not obj.photo:
            return 'выберите картинку'
        return format_html('<img src="{url}" style="max-height: 200px;"/>', url=obj.photo.url)

    get_image_preview.short_description = 'превью'

    def get_image_list_preview(self, obj):
        if not obj.photo or not obj.id:
            return 'нет картинки'
        edit_url = reverse('admin:flowerapp_bouquet_change', args=(obj.id,))
        return format_html('<a href="{edit_url}"><img src="{src}" style="max-height: 50px;"/></a>', edit_url=edit_url,
                           src=obj.photo.url)

    get_image_list_preview.short_description = 'превью'


@admin.register(m.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['bouquet', 'client_name', 'phone', 'delivery_address',
                    'paid', 'status', 'created_at', 'composed_at', 'delivered_at']
    list_display_links = ['bouquet', 'client_name', 'phone', 'delivery_address',
                          'paid', 'status', 'created_at', 'composed_at', 'delivered_at']
    search_fields = ['client_name', 'phone', 'delivery_address']
    list_filter = ['bouquet', 'paid', 'status']


@admin.register(m.Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['client_name', 'phone', 'created_at', 'status', 'consulted_at']
    list_display_links = ['client_name', 'phone', 'created_at', 'status', 'consulted_at']
    search_fields = ['client_name', 'phone']
    list_filter = ['status']
