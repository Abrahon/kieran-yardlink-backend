from django.urls import path
from .views import SubscribeRainAlert, UnsubscribeRainAlert, WeatherByDateView

urlpatterns = [
    path('subscribe/', SubscribeRainAlert.as_view(), name='subscribe'),
    path('unsubscribe/', UnsubscribeRainAlert.as_view(), name='unsubscribe'),
    path('weather-by-date/', WeatherByDateView.as_view(), name='weather-by-date'),

]
