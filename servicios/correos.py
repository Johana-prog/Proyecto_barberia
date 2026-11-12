"""
Correos de la barbería: reserva recibida, cita confirmada y cita cancelada.

Cada función arma el mensaje con los datos de la cita y lo envía en segundo plano, para que la página
no se quede esperando al servidor de correo. Si algo falla, se anota en la terminal (o en el registro de
Azure) y la reserva, la confirmación o la cancelación NO se deshacen.
"""
import logging
import threading
from functools import wraps

from django.core.mail import send_mail
from django.utils import dateformat

logger = logging.getLogger(__name__)

NEGOCIO = 'Usme Barber Top'
FIRMA = (
    '\n\n--\n'
    'Usme Barber Top\n'
    'Sede principal: El Poblado, Medellín\n'
    'Horario: lunes a sábado 8:00 AM - 8:00 PM; domingos y festivos 9:00 AM - 4:00 PM\n'
    'Teléfono: +57 323 6214485\n'
    'Correo: soporteusmebarbertop@gmail.com'
)


def _horas_min_cancelar():
    # Se importa aquí (y no arriba) para evitar un círculo entre este archivo y services.py
    from servicios.services import HORAS_MIN_CANCELAR
    return HORAS_MIN_CANCELAR


def _seguro(funcion):
    """Si algo falla al preparar un correo, se anota y se sigue: el correo nunca rompe una reserva."""
    @wraps(funcion)
    def envoltura(*args, **kwargs):
        try:
            return funcion(*args, **kwargs)
        except Exception:
            logger.exception('No se pudo preparar el correo')
    return envoltura


def _enviar(destinatario, asunto, cuerpo):
    """Envía el correo en un hilo aparte, sin hacer esperar a la página."""
    if not destinatario:
        return

    def tarea():
        try:
            send_mail(asunto, cuerpo, None, [destinatario], fail_silently=False)
        except Exception:
            logger.exception('No se pudo enviar el correo «%s»', asunto)

    threading.Thread(target=tarea, daemon=True).start()


def _datos(cita):
    """Junta los datos de la cita en texto simple (la fecha sale en español)."""
    cliente = cita.id_cliente
    barbero = cita.id_barbero.id_usuario
    partes = (cita.observaciones or '').split('|')
    try:
        precio = f"${int(float(partes[1])):,}".replace(',', '.') + ' COP'
    except (IndexError, ValueError):
        precio = None
    return {
        'correo': cliente.correo,
        'nombre': cliente.nombre,
        'barbero': f'{barbero.nombre} {barbero.apellido}',
        'servicio': partes[0],
        'precio': precio,
        'fecha': dateformat.format(cita.fecha, r'l j \d\e F'),
        'hora': dateformat.time_format(cita.hora, 'g:i A'),
    }


def _resumen(d):
    lineas = [
        f"Servicio: {d['servicio']}",
        f"Barbero: {d['barbero']}",
        f"Día: {d['fecha']}",
        f"Hora: {d['hora']}",
    ]
    if d['precio']:
        lineas.append(f"Total: {d['precio']}")
    return '\n'.join(lineas)


@_seguro
def cita_reservada(cita):
    d = _datos(cita)
    cuerpo = (
        f"Hola, {d['nombre']}.\n\n"
        "Recibimos tu reserva. Queda pendiente hasta que la barbería la confirme; te avisaremos por este mismo medio.\n\n"
        f"{_resumen(d)}\n\n"
        f"Puedes cancelarla desde «Mi agenda» hasta {_horas_min_cancelar()} horas antes de la cita."
        + FIRMA
    )
    _enviar(d['correo'], f'Recibimos tu reserva - {NEGOCIO}', cuerpo)


@_seguro
def cita_confirmada(cita):
    d = _datos(cita)
    cuerpo = (
        f"Hola, {d['nombre']}.\n\n"
        "¡Tu cita fue confirmada! Te esperamos.\n\n"
        f"{_resumen(d)}\n\n"
        f"Si no puedes asistir, cancélala desde «Mi agenda» hasta {_horas_min_cancelar()} horas antes, "
        "así otra persona puede tomar el horario."
        + FIRMA
    )
    _enviar(d['correo'], f'Tu cita fue confirmada - {NEGOCIO}', cuerpo)


@_seguro
def cita_cancelada(cita, por_cliente=False):
    d = _datos(cita)
    if por_cliente:
        intro = 'Tu cita fue cancelada, como lo pediste. El horario quedó libre para otras personas.'
        cierre = 'Cuando quieras, puedes reservar otro horario desde nuestra página.'
    else:
        intro = 'Lamentamos avisarte que la barbería canceló tu cita.'
        cierre = 'Puedes reservar otro horario desde nuestra página, o escribirnos y te ayudamos a reprogramar.'
    cuerpo = f"Hola, {d['nombre']}.\n\n{intro}\n\n{_resumen(d)}\n\n{cierre}{FIRMA}"
    _enviar(d['correo'], f'Tu cita fue cancelada - {NEGOCIO}', cuerpo)