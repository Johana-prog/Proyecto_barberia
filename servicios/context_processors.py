from servicios.models import Usuario

TITULOS = {
    'inicio': 'Inicio',
    'registro': 'Crear cuenta',
    'login': 'Iniciar sesión',
    'panel_cliente': 'Mi agenda',
    'configurar_perfil': 'Editar perfil',
    'panel_barbero': 'Panel del barbero',
    'panel_admin': 'Panel de administración',
    'agendar_cita': 'Solicitar turno',
    'ver_perfil_barbero': 'Perfil del barbero',
    'galeria_publica': 'Estilos de corte',
    'asistente_estilo': 'Asistente de estilo',
    'acerca_de': 'Acerca de',
    'pantalla_contacto': 'Contacto',
}


def usuario_actual(request):
    contexto = {'usuario_sesion': None}

    correo = request.session.get('cliente_correo')
    if correo:
        contexto['usuario_sesion'] = Usuario.objects.filter(correo=correo).first()

    coincidencia = getattr(request, 'resolver_match', None)
    titulo = TITULOS.get(coincidencia.url_name) if coincidencia else None
    contexto['titulo_pagina'] = f"{titulo} · Usme Barber Top" if titulo else "Usme Barber Top"

    return contexto