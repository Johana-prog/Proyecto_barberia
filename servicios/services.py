"""
Reglas de negocio de la barbería.

Aquí se decide qué se puede hacer y qué no (reservar, cancelar, cambiar un rol...).
Las vistas (views.py) solo reciben la petición, llaman a estas funciones y muestran el resultado.
"""
import datetime

from django.db import transaction
from django.utils import timezone

from servicios.models import Barbero, Cita, Usuario

ROLES_VALIDOS = ('cliente', 'barbero', 'administrador')
LIBRE = 'Horario Disponible'      # así se marca un turno publicado que nadie ha reservado
HORAS_MIN_CANCELAR = 2            # el cliente puede cancelar hasta 2 horas antes

MENSAJE_TURNO_NO_DISPONIBLE = 'Ese turno ya no está disponible. Elige otro horario.'
MENSAJE_ESTADO_CAMBIADO = 'Esa acción ya no corresponde al estado de la cita. Actualiza la página.'


class ReglaDeNegocio(Exception):
    """Algo que la persona no puede hacer. El mensaje está escrito para mostrárselo tal cual."""


# =========================================================================
# Utilidades de fecha y de cuentas
# =========================================================================
def ahora_local():
    """Fecha y hora actuales en Bogotá, sin zona horaria (para compararlas con las citas)."""
    return timezone.localtime().replace(tzinfo=None)


def momento_cita(cita):
    """Fecha y hora de una cita como un solo valor."""
    return datetime.datetime.combine(cita.fecha, cita.hora)


def usuario_comodin():
    """Cuenta a la que se asocian los turnos libres (todavía sin cliente)."""
    return Usuario.objects.filter(rol='administrador').first() or Usuario.objects.first()


# =========================================================================
# Citas
# =========================================================================
def reservar_turno(cliente, id_turno, servicio):
    """Reserva un turno libre para el cliente y devuelve la cita.

    El bloqueo (select_for_update) evita que dos personas reserven el mismo turno al mismo tiempo.
    El precio lo pone el servidor, nunca el formulario.
    """
    try:
        with transaction.atomic():
            cita = Cita.objects.select_for_update().get(
                id_cita=id_turno, observaciones=LIBRE, estado='pendiente',
            )
            if momento_cita(cita) < ahora_local():
                raise ReglaDeNegocio(MENSAJE_TURNO_NO_DISPONIBLE)
            cita.id_cliente = cliente
            cita.observaciones = f"{servicio.nombre_servicio}|{int(servicio.precio)}"
            cita.estado = 'pendiente'
            cita.save(update_fields=['id_cliente', 'observaciones', 'estado'])
    except Cita.DoesNotExist:
        raise ReglaDeNegocio(MENSAJE_TURNO_NO_DISPONIBLE)
    return cita


def _cambiar_estado(cita, desde, hacia):
    """Cambia el estado solo si la cita sigue en el estado esperado (así un doble clic no la cambia dos veces)."""
    with transaction.atomic():
        actual = Cita.objects.select_for_update().get(pk=cita.pk)
        if actual.estado != desde:
            raise ReglaDeNegocio(MENSAJE_ESTADO_CAMBIADO)
        actual.estado = hacia
        actual.save(update_fields=['estado'])
    return actual


def confirmar_cita(cita):
    return _cambiar_estado(cita, 'pendiente', 'confirmada')


def atender_cita(cita):
    return _cambiar_estado(cita, 'confirmada', 'atendida')


def cancelar_y_liberar(cita):
    """Cancela la cita y vuelve a publicar su horario como turno libre."""
    with transaction.atomic():
        actual = Cita.objects.select_for_update().get(pk=cita.pk)
        if actual.estado not in ('pendiente', 'confirmada'):
            raise ReglaDeNegocio(MENSAJE_ESTADO_CAMBIADO)
        actual.estado = 'cancelada'
        actual.save(update_fields=['estado'])
        Cita.objects.create(
            fecha=actual.fecha, hora=actual.hora, estado='pendiente',
            observaciones=LIBRE, id_cliente=usuario_comodin(), id_barbero=actual.id_barbero,
        )
    return actual


def cancelar_cita_cliente(cliente, id_cita):
    """El cliente cancela su propia cita (hasta HORAS_MIN_CANCELAR horas antes)."""
    cita = (
        Cita.objects.filter(id_cita=id_cita, id_cliente=cliente)
        .exclude(observaciones=LIBRE)
        .first()
    )
    if cita is None:
        raise ReglaDeNegocio('No encontramos esa cita.')
    if cita.estado not in ('pendiente', 'confirmada'):
        raise ReglaDeNegocio('Esta cita ya no se puede cancelar.')
    if momento_cita(cita) - ahora_local() < datetime.timedelta(hours=HORAS_MIN_CANCELAR):
        raise ReglaDeNegocio(
            f'Solo puedes cancelar hasta {HORAS_MIN_CANCELAR} horas antes de la cita. '
            'Si necesitas ayuda, comunícate con la barbería.'
        )
    return cancelar_y_liberar(cita)


# =========================================================================
# Agenda del barbero
# =========================================================================
def publicar_jornada(barbero, fecha, hora_inicio, hora_fin):
    """Publica un turno por cada hora entre la entrada y la salida. Devuelve cuántos creó."""
    if fecha < timezone.localdate():
        raise ReglaDeNegocio('No puedes publicar horarios en una fecha que ya pasó.')
    if hora_fin <= hora_inicio:
        raise ReglaDeNegocio('La hora de salida debe ser posterior a la de entrada.')

    comodin = usuario_comodin()
    creados = 0
    with transaction.atomic():
        for hora in range(hora_inicio, hora_fin):
            momento = datetime.time(hora, 0)
            ocupado = (
                Cita.objects.filter(fecha=fecha, hora=momento, id_barbero=barbero)
                .exclude(estado='cancelada')
                .exists()
            )
            if not ocupado:
                Cita.objects.create(
                    fecha=fecha, hora=momento, estado='pendiente',
                    observaciones=LIBRE, id_cliente=comodin, id_barbero=barbero,
                )
                creados += 1
    return creados


def eliminar_turno_libre(barbero, id_cita):
    """El barbero quita un turno libre que publicó. Si ya lo reservaron, no se puede."""
    borrados, _ = Cita.objects.filter(id_cita=id_cita, id_barbero=barbero, observaciones=LIBRE).delete()
    if not borrados:
        raise ReglaDeNegocio('No se pudo eliminar: el turno ya fue reservado o no existe.')


# =========================================================================
# Usuarios y roles
# =========================================================================
def _quedan_otros_administradores(objetivo):
    return Usuario.objects.filter(rol='administrador', estado=1).exclude(pk=objetivo.pk).exists()


def cambiar_rol(quien, objetivo, nuevo):
    """Cambia el rol de una persona. Devuelve (hubo_cambio, ficha_de_barbero_creada)."""
    if nuevo not in ROLES_VALIDOS:
        raise ReglaDeNegocio('Rol no válido.')
    if objetivo.id_usuario == quien.id_usuario and nuevo != objetivo.rol:
        raise ReglaDeNegocio('No puedes cambiar tu propio rol. Pídeselo a otra persona administradora.')
    if objetivo.rol == nuevo:
        return False, False
    if objetivo.rol == 'administrador' and not _quedan_otros_administradores(objetivo):
        raise ReglaDeNegocio('Debe quedar al menos una persona administradora activa.')

    ficha_creada = False
    with transaction.atomic():
        objetivo.rol = nuevo
        objetivo.save(update_fields=['rol'])
        if nuevo == 'barbero' and not Barbero.objects.filter(id_usuario=objetivo).exists():
            Barbero.objects.create(id_usuario=objetivo, especialidad='Por definir', experiencia_anios=0)
            ficha_creada = True
    return True, ficha_creada


def cambiar_estado_usuario(quien, objetivo, activar):
    """Activa o desactiva una cuenta (las cuentas no se eliminan, así se conserva el historial)."""
    if not activar:
        if objetivo.id_usuario == quien.id_usuario:
            raise ReglaDeNegocio('No puedes desactivar tu propia cuenta.')
        if objetivo.rol == 'administrador' and not _quedan_otros_administradores(objetivo):
            raise ReglaDeNegocio('Debe quedar al menos una persona administradora activa.')
    objetivo.estado = 1 if activar else 0
    objetivo.save(update_fields=['estado'])
    return objetivo