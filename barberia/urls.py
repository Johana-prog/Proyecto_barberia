from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from servicios import views

urlpatterns = [
    # La dirección sin nada más lleva al inicio
    path('', RedirectView.as_view(pattern_name='inicio', permanent=False)),
    path('admin/', admin.site.urls),
    path('inicio/', views.inicio_barberia, name='inicio'),
    path('registro/', views.registrar_cliente, name='registro'),
    path('login/', views.iniciar_sesion, name='login'),
    path('panel-cliente/', views.panel_cliente, name='panel_cliente'),
    path('perfil/', views.configurar_perfil, name='configurar_perfil'),
    path('panel-barbero/', views.panel_barbero, name='panel_barbero'),
    path('dashboard-admin/', views.panel_administrador, name='panel_admin'),
    path('agendar/', views.agendar_cita, name='agendar_cita'),
    path('barbero/<int:id_barbero>/', views.ver_perfil_barbero, name='ver_perfil_barbero'),
    path('galeria/', views.galeria_fotos_publica, name='galeria_publica'),
    path('asistente/', views.asistente_estilo, name='asistente_estilo'),
    path('cerrar/', views.cerrar_sesion, name='cerrar_sesion'),
    path('acerca-de/', views.acerca_de_sena, name='acerca_de'),
    path('contacto-info/', views.pantalla_contacto, name='pantalla_contacto'),
]


# Esto permite que las fotos subidas se vean en el navegador (solo modo desarrollo)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)