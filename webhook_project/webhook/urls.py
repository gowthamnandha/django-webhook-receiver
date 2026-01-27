from django.urls import path
from .views import webhook_receiver

urlpatterns = [
    path('webhook/', webhook_receiver, name='webhook'),  
]
