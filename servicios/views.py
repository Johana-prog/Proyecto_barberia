import datetime
import logging
from collections import Counter
from decimal import Decimal, InvalidOperation
from functools import wraps

from django.contrib import messages
from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import dateformat, timezone

from servicios.models import (
    Barbero,
    BarberoServicioEstrella,
    Cita,
    FotoTrabajoBarbero,
    Servicio,
    Usuario,
)

logger = logging.getLogger(__name__)

ROLES_VALIDOS = ('cliente', 'barbero', 'administrador')
LIBRE = 'Horario Disponible'      # así se marca un turno publicado que nadie ha reservado
HORAS_MIN_CANCELAR = 2            # el cliente puede cancelar hasta 2 horas antes
MAX_FOTO_MB = 5
MESES_CORTOS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']


# =========================================================================
# Seguridad: contraseñas cifradas y control de acceso por rol
# =========================================================================
def esta_cifrada(valor):
    """True si el texto ya es un hash de Django (y no una contraseña en texto plano)."""
    try:
        identify_hasher(valor)
        return True
    except ValueError:
        return False


def verificar_clave(usuario, clave):
    """Compara la clave escrita con la guardada. Si la cuenta es antigua
    (texto plano), la acepta una vez y la cifra en el momento."""
    guardada = usuario.contraseña or ''
    if esta_cifrada(guardada):
        return check_password(clave, guardada)
    if guardada == clave:
        usuario.contraseña = make_password(clave)
        usuario.save()
        return True
    return False


def cifrar_claves_existentes():
    """Se ejecuta UNA sola vez desde el shell: cifra las cuentas que siguen en texto plano."""
    cifradas = 0
    for u in Usuario.objects.all():
        if not esta_cifrada(u.contraseña or ''):
            u.contraseña = make_password(u.contraseña)
            u.save()
            cifradas += 1
    return cifradas


def url_panel(rol):
    """Nombre de la ruta del panel que le corresponde a cada rol."""
    if rol == 'administrador':
        return 'panel_admin'
    if rol == 'barbero':
        return 'panel_barbero'
    return 'panel_cliente'


def usuario_de_sesion(request):
    """Devuelve el usuario de la sesión, o None si no hay sesión o la cuenta ya no es válida
    (borrada, desactivada o con un rol desconocido)."""
    correo = request.session.get('cliente_correo')
    if not correo:
        return None
    usuario = Usuario.objects.filter(correo=correo).first()
    if usuario is None or usuario.estado == 0 or usuario.rol not in ROLES_VALIDOS:
        request.session.flush()
        return None
    request.session['cliente_rol'] = usuario.rol   # mantiene la sesión sincronizada
    return usuario


def login_requerido(vista):
    """Protege una vista: solo entra quien tenga una sesión válida."""
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if usuario_de_sesion(request) is None:
            return redirect('login')
        return vista(request, *args, **kwargs)
    return envoltura


def solo_rol(*roles_permitidos):
    """Protege una vista: solo entra quien tenga uno de los roles indicados."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            usuario = usuario_de_sesion(request)
            if usuario is None:
                return redirect('login')
            if usuario.rol not in roles_permitidos:
                return redirect(url_panel(usuario.rol))
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador


# =========================================================================
# Utilidades de fechas, precios y datos de las citas
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


def entero(valor):
    """Convierte a número entero o devuelve None (evita errores con datos mal enviados)."""
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def leer_precio(texto):
    """Convierte el texto de un precio a número, o devuelve None si no es válido."""
    try:
        valor = Decimal(str(texto).strip())
    except (InvalidOperation, ValueError):
        return None
    return valor if valor >= 0 else None


def es_imagen_valida(archivo):
    """Comprueba que el archivo subido sea de verdad una imagen (no solo que lo diga su nombre)."""
    try:
        from PIL import Image
        imagen = Image.open(archivo)
        imagen.verify()
        archivo.seek(0)
        return True
    except Exception:
        return False


def precio_guardado(cita):
    """Precio guardado dentro de la cita ('Servicio|precio'), o None si no lo trae."""
    try:
        partes = (cita.observaciones or '').split('|')
        if len(partes) > 1:
            return int(float(partes[1]))
    except (ValueError, TypeError):
        pass
    return None


def precio_cita(cita):
    """Igual que precio_guardado, pero con 25000 por defecto (citas antiguas), para la caja."""
    valor = precio_guardado(cita)
    return valor if valor is not None else 25000


def pesos(valor):
    """Formato colombiano: 1250000 -> 1.250.000"""
    return f"{int(valor):,}".replace(",", ".")


def nombre_servicio_cita(cita):
    observaciones = cita.observaciones or ''
    return observaciones.split('|')[0] if '|' in observaciones else observaciones


def preparar_cita(cita):
    """Agrega a la cita los datos que las pantallas necesitan mostrar."""
    cita.nombre_limpio_servicio = nombre_servicio_cita(cita)
    cita.precio_mostrar = precio_guardado(cita)
    cita.es_libre = (cita.observaciones == LIBRE)
    return cita


# =========================================================================
# 1. Páginas públicas
# =========================================================================
def inicio_barberia(request):
    return render(request, 'inicio.html', {
        "servicios": Servicio.objects.all(),
        "barberos": Barbero.objects.select_related('id_usuario').exclude(id_usuario__estado=0),
        "sesion_activa": 'cliente_nombre' in request.session
    })


def galeria_fotos_publica(request):
    fotos = FotoTrabajoBarbero.objects.select_related('id_barbero__id_usuario', 'id_servicio').order_by('-fecha_subida', '-id_foto')

    servicio_filtro = request.GET.get('servicio')
    if servicio_filtro and servicio_filtro.isdigit():
        fotos = fotos.filter(id_servicio=servicio_filtro)
    else:
        servicio_filtro = None

    return render(request, 'galeria_publica.html', {
        'fotos': fotos,
        'servicios': Servicio.objects.all(),
        'servicio_filtro': servicio_filtro,
        'sesion_activa': 'cliente_nombre' in request.session
    })


# =========================================================================
# 2. Registro e inicio de sesión
#
def registrar_cliente(request):
    contexto = {'sesion_activa': 'cliente_nombre' in request.session}

    if request.method == 'POST':
        nom = (request.POST.get('nombre') or '').strip()
        ape = (request.POST.get('apellido') or '').strip()
        doc = (request.POST.get('documento') or '').strip()
        cor = (request.POST.get('correo') or '').strip()
        cla = request.POST.get('contraseña') or ''

        if not (nom and ape and doc and cor and cla):
            messages.error(request, 'Completa todos los campos.')
        elif len(cla) < 8:
            messages.error(request, 'La contraseña debe tener mínimo 8 caracteres.')
        elif Usuario.objects.filter(documento=doc).exists():
            messages.error(request, 'Este documento ya está registrado.')
        elif Usuario.objects.filter(correo=cor).exists():
            messages.error(request, 'Este correo ya está en uso.')
        else:
            try:
                Usuario.objects.create(
                    nombre=nom, apellido=ape, documento=doc, correo=cor,
                    contraseña=make_password(cla), rol='cliente', estado=1,
                )
            except Exception:
                logger.exception('No se pudo registrar al usuario')
                messages.error(request, 'No pudimos crear la cuenta. Inténtalo de nuevo en unos minutos.')
            else:
                if usuario_de_sesion(request) is not None:
                    # Un administrador está registrando a otra persona: se queda en el formulario
                    messages.success(request, f'La cuenta de {nom} {ape} se creó con éxito.')
                    return redirect('/registro/')
                messages.success(request, 'Cuenta creada con éxito. Ya puedes iniciar sesión.')
                return redirect('/login/')

    return render(request, 'registro.html', contexto)


def iniciar_sesion(request):
    if 'cliente_nombre' in request.session and 'cliente_rol' in request.session and request.method == 'GET':
        return redirect(url_panel(request.session['cliente_rol']))

    if request.method == 'POST':
        correo_digitado = request.POST.get('correo', '').strip()
        clave_digitada = request.POST.get('contraseña', '')

        user = Usuario.objects.filter(correo=correo_digitado).first()

        if user is None or not verificar_clave(user, clave_digitada):
            messages.error(request, 'Correo o contraseña incorrectos.')
            return render(request, 'login.html')

        if user.estado == 0:
            messages.error(request, 'Tu cuenta está desactivada. Comunícate con la barbería.')
            return render(request, 'login.html')

        request.session.cycle_key()
        request.session['cliente_nombre'] = user.nombre
        request.session['cliente_correo'] = user.correo
        request.session['cliente_rol'] = user.rol

        return redirect(url_panel(user.rol))

    return render(request, 'login.html')

# =========================================================================
# 4. Panel del cliente (ahora puede cancelar su propia cita)
# =========================================================================
@solo_rol('cliente')
def panel_cliente(request):
    usuario = usuario_de_sesion(request)

    if request.method == 'POST' and 'cancelar_mi_cita' in request.POST:
        cita = (
            Cita.objects.filter(id_cita=entero(request.POST.get('id_cita')), id_cliente=usuario)
            .exclude(observaciones=LIBRE)
            .first()
        )
        if cita is None:
            messages.error(request, 'No encontramos esa cita.')
        elif cita.estado not in ('pendiente', 'confirmada'):
            messages.error(request, 'Esta cita ya no se puede cancelar.')
        elif momento_cita(cita) - ahora_local() < datetime.timedelta(hours=HORAS_MIN_CANCELAR):
            messages.error(
                request,
                f'Solo puedes cancelar hasta {HORAS_MIN_CANCELAR} horas antes de la cita. '
                'Si necesitas ayuda, comunícate con la barbería.',
            )
        else:
            cancelar_y_liberar(cita)
            messages.success(request, 'Tu cita fue cancelada. El horario quedó libre para otras personas.')
        return redirect('panel_cliente')

    ahora = ahora_local()
    citas = list(
        Cita.objects.select_related('id_barbero__id_usuario')
        .filter(id_cliente=usuario)
        .exclude(observaciones=LIBRE)
    )

    proximas, historial = [], []
    for c in citas:
        preparar_cita(c)
        activa = c.estado in ('pendiente', 'confirmada')
        c.puede_cancelar = activa and (momento_cita(c) - ahora >= datetime.timedelta(hours=HORAS_MIN_CANCELAR))
        if activa and momento_cita(c) >= ahora:
            proximas.append(c)
        else:
            historial.append(c)

    proximas.sort(key=momento_cita)
    historial.sort(key=momento_cita, reverse=True)

    return render(request, 'panel_cliente.html', {
        "cliente": usuario.nombre,
        "citas": proximas + historial,
        "proximas": proximas,
        "historial": historial,
        "servicios": Servicio.objects.all(),
        "horas_cancelar": HORAS_MIN_CANCELAR,
        "sesion_activa": True,
    })


# =========================================================================
# 5. Perfil (compartido por los tres roles)
# =========================================================================
@login_requerido
def configurar_perfil(request):
    usuario = usuario_de_sesion(request)

    if request.method == 'POST':
        nombre = (request.POST.get('nombre') or '').strip()
        apellido = (request.POST.get('apellido') or '').strip()
        telefono = (request.POST.get('telefono') or '').strip()
        correo = (request.POST.get('correo') or '').strip()
        foto = request.FILES.get('foto')

        if not (nombre and apellido and correo):
            messages.error(request, 'El nombre, el apellido y el correo son obligatorios.')
        elif Usuario.objects.filter(correo=correo).exclude(id_usuario=usuario.id_usuario).exists():
            messages.error(request, 'Ese correo ya está en uso por otra cuenta.')
        elif foto and foto.size > MAX_FOTO_MB * 1024 * 1024:
            messages.error(request, f'La foto pesa más de {MAX_FOTO_MB} MB. Elige una más liviana.')
        elif foto and not es_imagen_valida(foto):
            messages.error(request, 'El archivo que elegiste no es una imagen válida.')
        else:
            usuario.nombre = nombre
            usuario.apellido = apellido
            usuario.telefono = telefono or None
            usuario.correo = correo
            if foto:
                usuario.foto = foto
            usuario.save()

            request.session['cliente_correo'] = usuario.correo
            request.session['cliente_nombre'] = usuario.nombre
            messages.success(request, 'Tus datos se actualizaron con éxito.')
        return redirect('configurar_perfil')

    return render(request, 'perfil.html', {'usuario': usuario, 'sesion_activa': True})



# =========================================================================
# 6. Panel del barbero
# =========================================================================
@solo_rol('barbero')
def panel_barbero(request):
    usuario = usuario_de_sesion(request)
    barbero = Barbero.objects.filter(id_usuario=usuario).first()

    if barbero is None:
        messages.error(request, 'Tu cuenta no tiene una ficha de barbero asociada. Pide al administrador que la revise.')
        return render(request, 'panel_barbero.html', {
            "citas": [], "servicios": [], "ids_estrella": [], "fotos_trabajo": [],
            "citas_pendientes_count": 0, "sesion_activa": True,
        })

    if request.method == 'POST':
        destino = '#agenda-sec'

        if 'guardar_estrellas' in request.POST:
            destino = '#portafolio-sec'
            ids = [i for i in (entero(x) for x in request.POST.getlist('servicios_estrella')) if i is not None]
            validos = list(Servicio.objects.filter(id_servicio__in=ids))
            with transaction.atomic():
                BarberoServicioEstrella.objects.filter(id_barbero=barbero).delete()
                for servicio in validos:
                    BarberoServicioEstrella.objects.create(id_barbero=barbero, id_servicio=servicio)
            messages.success(request, 'Tus servicios estrella se actualizaron.')

        elif 'subir_foto' in request.POST:
            destino = '#portafolio-sec'
            archivo = request.FILES.get('foto_trabajo')
            if not archivo:
                messages.error(request, 'No seleccionaste ninguna foto.')
            elif archivo.size > MAX_FOTO_MB * 1024 * 1024:
                messages.error(request, f'La foto pesa más de {MAX_FOTO_MB} MB. Elige una más liviana.')
            elif not es_imagen_valida(archivo):
                messages.error(request, 'El archivo que elegiste no es una imagen válida.')
            else:
                servicio = Servicio.objects.filter(id_servicio=entero(request.POST.get('servicio_foto'))).first()
                nombre = (request.POST.get('nombre_estilo') or '').strip()[:80]
                FotoTrabajoBarbero.objects.create(
                    id_barbero=barbero, imagen=archivo,
                    nombre_estilo=nombre or None, id_servicio=servicio,
                )
                messages.success(request, 'Estilo agregado a tu portafolio.')

        elif 'eliminar_foto' in request.POST:
            destino = '#portafolio-sec'
            FotoTrabajoBarbero.objects.filter(id_foto=entero(request.POST.get('id_foto')), id_barbero=barbero).delete()
            messages.success(request, 'Foto eliminada de tu portafolio.')

        elif 'crear_espacio' in request.POST:
            destino = '#agenda-sec'
            try:
                fecha = datetime.date.fromisoformat(request.POST.get('fecha', ''))
                h_ini = int(request.POST.get('hora_inicio', '').split(':')[0])
                h_fin = int(request.POST.get('hora_fin', '').split(':')[0])
            except (ValueError, TypeError):
                messages.error(request, 'Revisa la fecha y las horas: no se pudo leer la jornada.')
            else:
                if fecha < timezone.localdate():
                    messages.error(request, 'No puedes publicar horarios en una fecha que ya pasó.')
                elif h_fin <= h_ini:
                    messages.error(request, 'La hora de salida debe ser posterior a la de entrada.')
                else:
                    comodin = usuario_comodin()
                    creados = 0
                    try:
                        with transaction.atomic():
                            for hora in range(h_ini, h_fin):
                                momento = datetime.time(hora, 0)
                                if not Cita.objects.filter(fecha=fecha, hora=momento, id_barbero=barbero).exclude(estado='cancelada').exists():
                                    Cita.objects.create(
                                        fecha=fecha, hora=momento, estado='pendiente',
                                        observaciones=LIBRE, id_cliente=comodin, id_barbero=barbero,
                                    )
                                    creados += 1
                    except Exception:
                        logger.exception('No se pudo generar la agenda')
                        messages.error(request, 'No pudimos generar la agenda. Inténtalo de nuevo.')
                    else:
                        if creados:
                            messages.success(request, f'Publicaste {creados} turno{"s" if creados != 1 else ""} para el {fecha.strftime("%d/%m/%Y")}.')
                        else:
                            messages.warning(request, 'Esos horarios ya estaban publicados en tu agenda.')

        elif 'eliminar_turno' in request.POST:
            destino = '#turnos-sec'
            borrados, _ = Cita.objects.filter(
                id_cita=entero(request.POST.get('id_cita')), id_barbero=barbero, observaciones=LIBRE,
            ).delete()
            if borrados:
                messages.success(request, 'Turno libre eliminado.')
            else:
                messages.error(request, 'No se pudo eliminar: el turno ya fue reservado o no existe.')

        elif 'id_cita' in request.POST:
            destino = '#turnos-sec'
            cita = (
                Cita.objects.filter(id_cita=entero(request.POST.get('id_cita')), id_barbero=barbero)
                .exclude(observaciones=LIBRE)
                .first()
            )
            if cita is None:
                messages.error(request, 'No encontramos esa cita.')
            elif 'confirmar_cita' in request.POST and cita.estado == 'pendiente':
                cita.estado = 'confirmada'
                cita.save(update_fields=['estado'])
                messages.success(request, 'Cita confirmada.', extra_tags='modal')
            elif 'atender_cita' in request.POST and cita.estado == 'confirmada':
                cita.estado = 'atendida'
                cita.save(update_fields=['estado'])
                messages.success(request, 'Cita marcada como atendida.', extra_tags='modal')
            elif 'cancelar_cita' in request.POST and cita.estado in ('pendiente', 'confirmada'):
                cancelar_y_liberar(cita)
                messages.success(request, 'Cita cancelada. El horario quedó libre otra vez.')
            else:
                messages.error(request, 'Esa acción ya no corresponde al estado de la cita. Actualiza la página.')

        return redirect(f"{reverse('panel_barbero')}{destino}")

    citas = list(Cita.objects.select_related('id_cliente').filter(id_barbero=barbero).order_by('fecha', 'hora'))
    for c in citas:
        preparar_cita(c)
    pendientes = sum(1 for c in citas if c.estado == 'pendiente' and not c.es_libre)

    return render(request, 'panel_barbero.html', {
        "citas": citas,
        "sesion_activa": True,
        "citas_pendientes_count": pendientes,
        "servicios": Servicio.objects.all(),
        "ids_estrella": list(BarberoServicioEstrella.objects.filter(id_barbero=barbero).values_list('id_servicio_id', flat=True)),
        "fotos_trabajo": FotoTrabajoBarbero.objects.select_related('id_servicio').filter(id_barbero=barbero).order_by('-fecha_subida', '-id_foto'),
        "barbero_actual": barbero,
        "hoy_iso": timezone.localdate().isoformat(),
    })


# =========================================================================
# 7. Panel del administrador
# =========================================================================
@solo_rol('administrador')
def panel_administrador(request):
    yo = usuario_de_sesion(request)

    if request.method == 'POST':
        destino = '#citas-sec'

        if 'agregar_servicio' in request.POST:
            destino = '#servicios-sec'
            nombre = (request.POST.get('nombre_nuevo_servicio') or '').strip()
            descripcion = (request.POST.get('descripcion_nuevo_servicio') or '').strip()
            precio = leer_precio(request.POST.get('precio_nuevo_servicio'))
            if not nombre or precio is None:
                messages.error(request, 'Escribe el nombre y un precio válido para el servicio.')
            elif Servicio.objects.filter(nombre_servicio__iexact=nombre).exists():
                messages.error(request, f'Ya existe un servicio llamado «{nombre}».')
            else:
                Servicio.objects.create(nombre_servicio=nombre, descripcion=descripcion or None, precio=precio, estado=1)
                messages.success(request, f'Servicio «{nombre}» creado. Ya aparece en el inicio y en las reservas.')

        elif 'actualizar_precio' in request.POST:
            destino = '#servicios-sec'
            servicio = Servicio.objects.filter(id_servicio=entero(request.POST.get('id_servicio'))).first()
            precio = leer_precio(request.POST.get('nuevo_precio'))
            if servicio is None or precio is None:
                messages.error(request, 'Escribe un precio válido.')
            else:
                servicio.precio = precio
                servicio.save(update_fields=['precio'])
                messages.success(request, f'La tarifa de «{servicio.nombre_servicio}» ahora es ${pesos(precio)} COP.')

        elif 'desactivar_usuario' in request.POST or 'activar_usuario' in request.POST:
            destino = '#usuarios-sec'
            activar = 'activar_usuario' in request.POST
            objetivo = Usuario.objects.filter(id_usuario=entero(request.POST.get('id_usuario'))).first()
            if objetivo is None:
                messages.error(request, 'No encontramos a ese usuario.')
            elif objetivo.id_usuario == yo.id_usuario:
                messages.error(request, 'No puedes desactivar tu propia cuenta.')
            else:
                objetivo.estado = 1 if activar else 0
                objetivo.save(update_fields=['estado'])
                accion = 'activada' if activar else 'desactivada'
                messages.success(request, f'La cuenta de {objetivo.nombre} {objetivo.apellido} fue {accion}.')

        elif 'eliminar_usuario' in request.POST:
            destino = '#usuarios-sec'
            messages.warning(request, 'La opción Eliminar se reemplazó por Desactivar. Actualiza la página.')

        elif 'id_cita' in request.POST:
            destino = '#citas-sec'
            cita = Cita.objects.filter(id_cita=entero(request.POST.get('id_cita'))).exclude(observaciones=LIBRE).first()
            if cita is None:
                messages.error(request, 'No encontramos esa cita.')
            elif ('confirmar_cita' in request.POST or 'aceptar_cita' in request.POST) and cita.estado == 'pendiente':
                cita.estado = 'confirmada'
                cita.save(update_fields=['estado'])
                messages.success(request, 'Cita confirmada.', extra_tags='modal')
            elif 'cancelar_cita' in request.POST and cita.estado in ('pendiente', 'confirmada'):
                cancelar_y_liberar(cita)
                messages.success(request, 'Cita cancelada. El horario quedó libre otra vez.')
            else:
                messages.error(request, 'Esa acción ya no corresponde al estado de la cita. Actualiza la página.')

        elif 'cambiar_rol' in request.POST:
            destino = '#usuarios-sec'
            nuevo = request.POST.get('nuevo_rol')
            objetivo = Usuario.objects.filter(id_usuario=entero(request.POST.get('id_usuario'))).first()
            if nuevo not in ROLES_VALIDOS:
                messages.error(request, 'Rol no válido.')
            elif objetivo is None:
                messages.error(request, 'No encontramos a ese usuario.')
            elif objetivo.id_usuario == yo.id_usuario and nuevo != objetivo.rol:
                messages.error(request, 'No puedes cambiar tu propio rol. Pídeselo a otra persona administradora.')
            elif objetivo.rol == nuevo:
                messages.info(request, 'Ese usuario ya tenía ese rol.')
            else:
                objetivo.rol = nuevo
                objetivo.save(update_fields=['rol'])
                if nuevo == 'barbero' and not Barbero.objects.filter(id_usuario=objetivo).exists():
                    Barbero.objects.create(id_usuario=objetivo, especialidad='Por definir', experiencia_anios=0)
                    messages.success(request, f'{objetivo.nombre} ahora es barbero y su ficha se creó automáticamente.')
                else:
                    messages.success(request, f'El rol de {objetivo.nombre} cambió a {nuevo}.')

        return redirect(f"{reverse('panel_admin')}{destino}")

    # ---------------- Datos para las pestañas ----------------
    citas_totales = list(
        Cita.objects.select_related('id_cliente', 'id_barbero__id_usuario')
        .exclude(estado='libre')
        .order_by('fecha', 'hora')
    )
    for c in citas_totales:
        preparar_cita(c)

    reales = [c for c in citas_totales if not c.es_libre]
    citas_pendientes = [c for c in reales if c.estado == 'pendiente']
    citas_confirmadas = [c for c in reales if c.estado == 'confirmada']
    citas_canceladas = [c for c in reales if c.estado == 'cancelada']
    citas_atendidas = [c for c in reales if c.estado == 'atendida']

    total_caja = sum(precio_cita(c) for c in citas_atendidas)

    # ---------------- Datos para las gráficas ----------------
    activas = [c for c in reales if c.estado != 'cancelada']

    hoy = datetime.date.today()
    fin = max([hoy] + [c.fecha for c in citas_atendidas])
    meses = []
    anio, mes = fin.year, fin.month
    for _ in range(6):
        meses.append((anio, mes))
        mes -= 1
        if mes == 0:
            mes = 12
            anio -= 1
    meses.reverse()

    ingresos_por_mes = {clave: 0 for clave in meses}
    for c in citas_atendidas:
        clave = (c.fecha.year, c.fecha.month)
        if clave in ingresos_por_mes:
            ingresos_por_mes[clave] += precio_cita(c)

    servicios_top = Counter(c.nombre_limpio_servicio for c in activas if c.nombre_limpio_servicio).most_common(5)
    por_barbero = Counter(c.id_barbero.id_usuario.nombre for c in activas).most_common(6)

    ingresos_mes_actual = ingresos_por_mes.get((fin.year, fin.month), 0)
    ticket_promedio = int(total_caja / len(citas_atendidas)) if citas_atendidas else 0
    tasa_cancelacion = round(len(citas_canceladas) * 100 / len(reales)) if reales else 0

    datos_graficas = {
        'ingresos': {
            'etiquetas': [f"{MESES_CORTOS[m - 1]} {a}" for (a, m) in meses],
            'valores': [ingresos_por_mes[k] for k in meses],
        },
        'servicios': {
            'etiquetas': [s[0] for s in servicios_top],
            'valores': [s[1] for s in servicios_top],
        },
        'estados': {
            'etiquetas': ['Pendientes', 'Confirmadas', 'Atendidas', 'Canceladas'],
            'valores': [len(citas_pendientes), len(citas_confirmadas), len(citas_atendidas), len(citas_canceladas)],
        },
        'barberos': {
            'etiquetas': [b[0] for b in por_barbero],
            'valores': [b[1] for b in por_barbero],
        },
    }

    resumen = {
        'ingresos_mes': pesos(ingresos_mes_actual),
        'ticket': pesos(ticket_promedio),
        'total_citas': len(reales),
        'cancelacion': tasa_cancelacion,
    }

    return render(request, 'panel_admin.html', {
        'usuarios': Usuario.objects.all().order_by('nombre'),
        'servicios': Servicio.objects.all(),
        'sesion_activa': True,
        'yo_id': yo.id_usuario,
        'ingresos_totales': pesos(total_caja),
        'amount_cobros': len(citas_atendidas),
        'citas_pendientes': citas_pendientes,
        'citas_confirmadas': citas_confirmadas,
        'citas_canceladas': citas_canceladas,
        'citas_finalizadas': citas_atendidas,
        'citas_atendidas': citas_atendidas,
        'citas_pendientes_admin': len(citas_pendientes),
        'datos_graficas': datos_graficas,
        'resumen': resumen,
    })



# =========================================================================
# 8. Reservar un turno
# =========================================================================
@login_requerido
def agendar_cita(request):
    usuario = usuario_de_sesion(request)
    ahora = ahora_local()

    if request.method == 'POST':
        id_turno = entero(request.POST.get('turno_id'))
        servicio = Servicio.objects.filter(id_servicio=entero(request.POST.get('servicio_elegido'))).first()

        if servicio is None:
            messages.error(request, 'Elige un servicio válido.')
        else:
            try:
                # El bloqueo evita que dos personas reserven el mismo turno al mismo tiempo
                with transaction.atomic():
                    cita = Cita.objects.select_for_update().get(id_cita=id_turno, observaciones=LIBRE, estado='pendiente')
                    if momento_cita(cita) < ahora:
                        raise ValueError('El turno ya pasó')
                    cita.id_cliente = usuario
                    # El precio lo pone el servidor, no el formulario
                    cita.observaciones = f"{servicio.nombre_servicio}|{int(servicio.precio)}"
                    cita.estado = 'pendiente'
                    cita.save(update_fields=['id_cliente', 'observaciones', 'estado'])
            except (Cita.DoesNotExist, ValueError):
                messages.error(request, 'Ese turno ya no está disponible. Elige otro horario.')
            except Exception:
                logger.exception('Error al reservar un turno')
                messages.error(request, 'No pudimos completar tu reserva. Inténtalo de nuevo.')
            else:
                barbero = cita.id_barbero.id_usuario
                fecha = dateformat.format(cita.fecha, r'l j \d\e F')
                hora = dateformat.time_format(cita.hora, 'g:i A')
                messages.success(
                    request,
                    f'Reservaste {servicio.nombre_servicio} con {barbero.nombre} {barbero.apellido} '
                    f'el {fecha} a las {hora}. Total: ${pesos(servicio.precio)} COP. '
                    'Tu cita queda pendiente de confirmación.',
                    extra_tags='modal',
                )
                return redirect('panel_cliente')
        return redirect('agendar_cita')

    turnos = [
        c for c in Cita.objects.select_related('id_barbero__id_usuario')
        .filter(observaciones=LIBRE, estado='pendiente', fecha__gte=ahora.date())
        .exclude(id_barbero__id_usuario__estado=0)
        .order_by('fecha', 'hora')
        if momento_cita(c) >= ahora
    ]

    return render(request, 'agendar_cita.html', {
        'turnos': turnos,
        'servicios': Servicio.objects.all(),
        'barberos_disponibles': Barbero.objects.select_related('id_usuario').exclude(id_usuario__estado=0),
        'servicio_pre': request.GET.get('servicio'),
        'sesion_activa': True,
    })


# =========================================================================
# Perfil público de un barbero
# =========================================================================
@login_requerido
def ver_perfil_barbero(request, id_barbero):
    barbero_obj = get_object_or_404(Barbero, id_barbero=id_barbero)
    servicios_estrella = BarberoServicioEstrella.objects.filter(id_barbero=barbero_obj).select_related('id_servicio')
    fotos_trabajo = FotoTrabajoBarbero.objects.filter(id_barbero=barbero_obj).select_related('id_servicio').order_by('-fecha_subida', '-id_foto')

    return render(request, 'perfil_barbero_publico.html', {
        'barbero': barbero_obj,
        'servicios_estrella': servicios_estrella,
        'fotos_trabajo': fotos_trabajo,
        'sesion_activa': True
    })


# =========================================================================
# Páginas informativas y salida
# =========================================================================
def acerca_de_sena(request):
    return render(request, 'acerca_de.html', {'sesion_activa': 'cliente_nombre' in request.session})


def pantalla_contacto(request):
    return render(request, 'contacto.html', {'sesion_activa': 'cliente_nombre' in request.session})


def cerrar_sesion(request):
    request.session.flush()
    return redirect('inicio')

# =========================================================================
# 10. ASISTENTE DE ESTILO
# =========================================================================
def asistente_estilo(request):
    import unicodedata

    OPCIONES = {
        'queres': ('cabello', 'ambos', 'barba'),
        'cabello': ('liso', 'ondulado', 'rizado', 'poco'),
        'cara': ('ovalada', 'redonda', 'cuadrada', 'alargada', 'nose'),
        'mantenimiento': ('bajo', 'medio', 'alto'),
        'estilo': ('clasico', 'urbano', 'abierto'),
    }

    ETIQUETAS = {
        'queres': {'cabello': 'Solo corte', 'ambos': 'Corte y barba', 'barba': 'Solo barba'},
        'cabello': {'liso': 'Cabello liso', 'ondulado': 'Cabello ondulado', 'rizado': 'Cabello rizado', 'poco': 'Poco cabello'},
        'cara': {'ovalada': 'Cara ovalada', 'redonda': 'Cara redonda', 'cuadrada': 'Cara cuadrada', 'alargada': 'Cara alargada', 'nose': None},
        'mantenimiento': {'bajo': 'Mantenimiento bajo', 'medio': 'Mantenimiento medio', 'alto': 'Mantenimiento alto'},
        'estilo': {'clasico': 'Estilo clásico', 'urbano': 'Estilo urbano', 'abierto': None},
    }

    contexto = {'sesion_activa': 'cliente_nombre' in request.session}

    respuestas = {}
    for campo, validos in OPCIONES.items():
        valor = request.GET.get(campo)
        if valor in validos:
            respuestas[campo] = valor

    queres = respuestas.get('queres')
    requeridas = ['queres', 'mantenimiento']
    if queres in ('cabello', 'ambos'):
        requeridas += ['cabello', 'cara', 'estilo']

    if not queres or any(c not in respuestas for c in requeridas):
        return render(request, 'asistente_estilo.html', contexto)

    perfiles = ('clasico', 'fade', 'combo', 'perfilado')
    puntaje = {p: 0 for p in perfiles}
    razones = {p: [] for p in perfiles}

    def suma(perfil, puntos, razon=None):
        puntaje[perfil] += puntos
        if razon:
            razones[perfil].append(razon)

    mant = respuestas['mantenimiento']

    if queres == 'barba':
        for p in ('clasico', 'fade', 'combo'):
            suma(p, -100)
        suma('perfilado', 100, 'Solo quieres arreglar la barba: el perfilado deja el contorno definido y prolijo.')
        suma('perfilado', 0, {
            'bajo': 'Un buen perfilado mantiene la barba prolija con poco esfuerzo entre visitas.',
            'medio': 'Con una visita cada tres o cuatro semanas, tu barba se ve siempre cuidada.',
            'alto': 'Si te gusta verte impecable, repetir el perfilado cada dos semanas mantiene el contorno perfecto.',
        }[mant])
    else:
        suma('perfilado', -100)
        cabello = respuestas['cabello']
        cara = respuestas['cara']
        estilo = respuestas['estilo']

        if cabello == 'liso':
            suma('clasico', 1, 'Tu cabello liso responde muy bien a los cortes con tijera y peinado definido.')
            suma('fade', 1, 'En cabello liso, la transición del degradado se ve limpia y precisa.')
        elif cabello == 'ondulado':
            suma('clasico', 2, 'Tu cabello ondulado le da textura natural a un corte clásico.')
            suma('fade', 1)
        elif cabello == 'rizado':
            suma('fade', 3, 'Los degradados dan forma y definición al cabello rizado.')
            suma('clasico', 1)
        else:
            suma('fade', 2, 'Con menos cabello, un degradado bien hecho se ve prolijo y firme.')
            suma('clasico', 1)

        if cara == 'ovalada':
            suma('clasico', 1, 'Tu cara ovalada admite casi cualquier estilo.')
            suma('fade', 1)
        elif cara == 'redonda':
            suma('fade', 2, 'En una cara redonda, los laterales cortos estilizan el rostro.')
        elif cara == 'cuadrada':
            suma('clasico', 2, 'Tu mandíbula marcada combina con cortes clásicos.')
            suma('fade', 1)
        elif cara == 'alargada':
            suma('clasico', 2, 'En un rostro alargado conviene no sumar demasiada altura.')

        if mant == 'bajo':
            suma('clasico', 2, 'Un corte clásico aguanta más tiempo entre visitas.')
            suma('fade', -1)
        elif mant == 'medio':
            suma('clasico', 1)
            suma('fade', 1)
        else:
            suma('fade', 2, 'Un degradado se luce más cuando lo mantienes fresco.')

        if estilo == 'clasico':
            suma('clasico', 3, 'Buscas elegancia y lo clásico.')
        elif estilo == 'urbano':
            suma('fade', 3, 'Buscas estilo moderno y urbano.')

        if queres == 'ambos':
            mejor_corte = 'fade' if puntaje['fade'] > puntaje['clasico'] else 'clasico'
            nombre_corte = 'degradado' if mejor_corte == 'fade' else 'clásico'
            suma('combo', 100, 'Quieres arreglar cabello y barba: el combo lo resuelve todo.')
            suma('combo', 0, f'Para el corte, lo que mejor te va es un estilo {nombre_corte}.')
            for r in razones[mejor_corte][:2]:
                suma('combo', 0, r)
        else:
            suma('combo', -100)

    def normalizar(texto):
        base = unicodedata.normalize('NFD', (texto or '').lower())
        return ''.join(c for c in base if unicodedata.category(c) != 'Mn')

    servicios = list(Servicio.objects.all())
    reglas = {
        'clasico': lambda n: 'clasico' in n and 'barba' not in n,
        'fade': lambda n: 'fade' in n or 'degrad' in n,
        'combo': lambda n: 'barba' in n and 'corte' in n,
        'perfilado': lambda n: 'perfilado' in n,
    }

    candidatos = []
    for perfil, cumple in reglas.items():
        for s in servicios:
            if cumple(normalizar(s.nombre_servicio)):
                if puntaje[perfil] > -50:
                    candidatos.append((puntaje[perfil], perfil, s))
                break

    candidatos.sort(key=lambda c: c[0], reverse=True)

    if not candidatos and servicios:
        candidatos = [(0, 'clasico', servicios[0])]

    if not candidatos:
        contexto['sin_resultado'] = True
        return render(request, 'asistente_estilo.html', contexto)

    _, perfil_principal, servicio_principal = candidatos[0]
    razones_finales = razones[perfil_principal][:4] or ['Es una excelente opción para conocernos.']

    alternativa = None
    for _, _, s in candidatos[1:]:
        if s.id_servicio != servicio_principal.id_servicio:
            alternativa = s
            break

    fotos = (
        FotoTrabajoBarbero.objects
        .filter(id_servicio=servicio_principal)
        .select_related('id_barbero__id_usuario')
        .order_by('-fecha_subida', '-id_foto')[:3]
    )

    chips = []
    for campo in ('queres', 'cabello', 'cara', 'mantenimiento', 'estilo'):
        if campo in requeridas:
            etiqueta = ETIQUETAS[campo].get(respuestas[campo])
            if etiqueta:
                chips.append(etiqueta)

    contexto['resultado'] = {
        'principal': servicio_principal,
        'razones': razones_finales,
        'alternativa': alternativa,
        'fotos': fotos,
        'chips': chips,
    }
    return render(request, 'asistente_estilo.html', contexto)

# =========================================================================
# CANCELAR CITA
# =========================================================================
def cancelar_y_liberar(cita):
    """Cancela la cita y vuelve a publicar su horario como turno libre."""
    with transaction.atomic():
        cita.estado = 'cancelada'
        cita.save(update_fields=['estado'])
        Cita.objects.create(
            fecha=cita.fecha, hora=cita.hora, estado='pendiente',
            observaciones=LIBRE, id_cliente=usuario_comodin(), id_barbero=cita.id_barbero,
        )