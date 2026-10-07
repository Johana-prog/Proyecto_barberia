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
from django.conf import settings
from django.conf.urls.static import static
from servicios import views

urlpatterns = [
    # Oficina de administración azul original
    path('admin/', admin.site.urls), 
    
    # 🏠 Página principal de bienvenida pública (Figma)
    path('inicio/', views.inicio_barberia, name='inicio'), 
    
    # 📝 Registro con ojos de seguridad (Semana 4)
    path('registro/', views.registrar_cliente, name='registro'), 
    
    # 👤 Login con enrutamiento inteligente por roles (Semana 5)
    path('login/', views.iniciar_sesion, name='login'), 
    
    # 👑 Panel privado del cliente (Saludo + Historial de citas)
    path('panel-cliente/', views.panel_cliente, name='panel_cliente'), 
    
    # ⚙️ Pantalla para que el cliente configure su teléfono y correo
    path('perfil/', views.configurar_perfil, name='configurar_perfil'), 
    
    # 💈 Panel privado del barbero (Con triple botón de moderación)
    path('panel-barbero/', views.panel_barbero, name='panel_barbero'), 
    
    # 💼 Panel del administrador global para la Jefa
    path('dashboard-admin/', views.panel_administrador, name='panel_admin'),
    
    # 📅 Formulario para solicitar y agendar turnos en MySQL
    path('agendar/', views.agendar_cita, name='agendar_cita'),

    path('barbero/<int:id_barbero>/', views.ver_perfil_barbero, name='ver_perfil_barbero'),
    
    # 🚪 Botón de salida para borrar la memoria (Sesiones)
    path('cerrar/', views.cerrar_sesion, name='cerrar_sesion'),
    

    path('acerca-de/', views.acerca_de_sena, name='acerca_de'),

    # 🎯 NUEVA CALLE: Para la pantalla de Contacto y Ubicación Avanzada
    path('contacto-info/', views.pantalla_contacto, name='pantalla_contacto'),

    path('galeria/', views.galeria_fotos_publica, name='galeria_publica'),

    path('contacto-info/', views.pantalla_contacto, name='pantalla_contacto'),

    

]


# 🆕 Esto permite que las fotos subidas se vean en el navegador (solo modo desarrollo)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)