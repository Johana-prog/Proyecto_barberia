class SinCacheEnSesion:
    """Si hay una sesión abierta, el navegador no guarda copia de las páginas.
    Así, al cerrar sesión y presionar 'Atrás', el panel no reaparece."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.session.get('cliente_correo'):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
        return response