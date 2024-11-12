from django.urls import path
from . import views
from .views import dashboard

urlpatterns = [
    path('', views.check_url, name='check_url'),
    path('dashboard/', dashboard, name='dashboard'),
     path('download_json/', views.download_json, name='download_json'),
]