from servicios.models import Usuario

def usuario_actual(request):
    correo = request.session.get('cliente_correo')
    if correo:
        try:
            usuario = Usuario.objects.get(correo=correo)
            return {'usuario_sesion': usuario}
        except Usuario.DoesNotExist:
            return {'usuario_sesion': None}
    return {'usuario_sesion': None}