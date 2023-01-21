from django.urls import path
from django.shortcuts import redirect

from . import views

app_name = "floristapp"

urlpatterns = [
    path('', lambda request: redirect('floristapp:orders')),
    path('availability/', views.view_availability, name="availability"),
    path('orders/', views.view_orders, name="orders"),
    path('login/', views.LoginView.as_view(), name="login"),
    path('logout/', views.LogoutView.as_view(), name="logout"),
]
