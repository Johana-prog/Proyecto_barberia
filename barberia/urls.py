"""
URL configuration for barberia project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
#1. aqui le decimos a django que busque en la carpeta 'servicios' el archivo 'views'
from servicios import views

urlpatterns = [
    path('admin/', admin.site.urls),
    #2. aqui creamos la calle para que el cliente encuentre al mesero
    path('bienvenida/', views.bienvenida),
    path('contacto/', views.contacto), #nueva callle 
    
    # nueva calle inteligente
    path('barbero/<str:nombre>/', views.perfil_barbero),

    #nueva calle calculadora/fidelidad usamos <int:..> porque recibimos numero no texto
    path('puntos/<int:cantidad_cortes>/', views.calcular_puntos),

    #nueva calle para nuestra hora
    path('hora/', views.hora_actual),

    # nueva calle para el diseño HTML
    path('inicio/', views.inicio_barberia),

    path('registro/', views.registrar_cliente, name='registro'),

    path('login/', views.iniciar_sesion, name='login'),

    path('agendar/', views.agendar_cita, name='agendar_cita'),

]

