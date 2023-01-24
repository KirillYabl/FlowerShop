from django.urls import path
from django.shortcuts import redirect

from . import views

app_name = "floristapp"

urlpatterns = [
    path('', lambda request: redirect('floristapp:orders')),
    path('availability/', views.view_availability, name="availability"),
    path('orders/', views.view_orders, name="orders"),
    path('orders/<int:order_id>/', views.change_status, name="change_status"),
]
