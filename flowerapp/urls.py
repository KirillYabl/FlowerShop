from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('card/<bouquet_id>/', views.card, name='card'),
    path('catalog', views.catalog, name='catalog'),
    path('consultation', views.consultation, name='consultation'),
    path('order/<bouquet_id>/', views.order, name='order'),
    path('quiz', views.quiz, name='quiz'),
    path('result', views.result, name='result'),
    path('stats', views.stats, name='stats'),
]
