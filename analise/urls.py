from django.urls import path

from . import views

urlpatterns = [
    path('mapa/', views.mapa_analise, name='analise_mapa'),
]
