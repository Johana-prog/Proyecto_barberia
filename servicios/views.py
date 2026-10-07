from django.shortcuts import render, redirect
from servicios.models import Servicio, Usuario, Barbero, Cita, BarberoServicioEstrella, FotoTrabajoBarbero
import datetime

# 🏠 1. BIENVENIDA PÚBLICA
def inicio_barberia(request):
    ahora = datetime.datetime.now().strftime("%d/%m/%Y a las %H:%M")
    servicios_base_datos = Servicio.objects.all()
    barberos_base_datos = Barbero.objects.all()
    return render(request, 'inicio.html', {
        "servicios": servicios_base_datos,
        "barberos": barberos_base_datos,
        "fecha_actual": ahora,
        "sesion_activa": 'cliente_nombre' in request.session
    })
# =========================================================================
# 🖼️ GALERÍA PÚBLICA: Fotos de TODOS los barberos juntas
# =========================================================================
def galeria_fotos_publica(request):
    fotos = FotoTrabajoBarbero.objects.select_related('id_barbero__id_usuario').order_by('-fecha_subida')
    return render(request, 'galeria_publica.html', {
        'fotos': fotos,
        'sesion_activa': 'cliente_nombre' in request.session
    })

# 📝 2. REGISTRO
def registrar_cliente(request):
    if request.method == 'POST':
        nom = request.POST.get('nombre')
        ape = request.POST.get('apellido')
        doc = request.POST.get('documento')
        cor = request.POST.get('correo')
        cla = request.POST.get('contraseña')

        if Usuario.objects.filter(documento=doc).exists():
            return render(request, 'registro.html', {'mensaje_error': '⚠️ Este documento ya existe.'})
        if Usuario.objects.filter(correo=cor).exists():
            return render(request, 'registro.html', {'mensaje_error': '⚠️ Este correo ya está en uso.'})

        try:
            nuevo = Usuario(nombre=nom, apellido=ape, documento=doc, correo=cor, contraseña=cla, rol="cliente", estado=1)
            nuevo.save()
            return render(request, 'registro.html', {'mensaje': '¡Cuenta creada con éxito!'})
        except Exception as e:
            return render(request, 'registro.html', {'mensaje_error': f'⚠️ Error: {e}'})
    return render(request, 'registro.html')

# 👤 3. LOGIN INTERCONECTADO
def iniciar_sesion(request):
    if 'cliente_nombre' in request.session and 'cliente_rol' in request.session and request.method == 'GET':
        rol = request.session['cliente_rol']
        if rol == 'administrador': return redirect('panel_admin')
        elif rol == 'barbero': return redirect('panel_barbero')
        else: return redirect('panel_cliente')

    if request.method == 'POST':
        correo_digitado = request.POST.get('correo')
        clave_digitada = request.POST.get('contraseña')

        try:
            user = Usuario.objects.get(correo=correo_digitado)
            if user.contraseña == clave_digitada:
                request.session['cliente_nombre'] = user.nombre
                request.session['cliente_correo'] = user.correo
                request.session['cliente_rol'] = user.rol
                if user.rol == 'administrador': return redirect('panel_admin')
                elif user.rol == 'barbero': return redirect('panel_barbero')
                else: return redirect('panel_cliente')
            else:
                return render(request, 'login.html', {"error": "⚠️ Contraseña incorrecta."})
        except Usuario.DoesNotExist:
            return render(request, 'login.html', {"error": "⚠️ Este correo no existe."})
    return render(request, 'login.html')

# 👑 4. PANEL CLIENTE
def panel_cliente(request):
    if 'cliente_nombre' not in request.session: return redirect('login')
    usuario_actual = Usuario.objects.get(correo=request.session['cliente_correo'])
    barberos_base_datos = Barbero.objects.all()
    mis_citas = Cita.objects.filter(id_cliente=usuario_actual).order_by('fecha', 'hora')
    servicios_disponibles = Servicio.objects.all()
    return render(request, 'panel_cliente.html', {
        "cliente": request.session['cliente_nombre'],
        "barberos": barberos_base_datos,
        "citas": mis_citas,
        "servicios": servicios_disponibles,
        "sesion_activa": True
    })
# =========================================================================
# ⚙️ 5. PERFIL (con foto de perfil profesional, compartido por los 3 roles)
# =========================================================================
def configurar_perfil(request):
    if 'cliente_correo' not in request.session: return redirect('login')
    usuario_actual = Usuario.objects.get(correo=request.session['cliente_correo'])
    mensaje = None

    if request.method == 'POST':
        usuario_actual.nombre = request.POST.get('nombre')
        usuario_actual.apellido = request.POST.get('apellido')
        usuario_actual.telefono = request.POST.get('telefono')
        usuario_actual.correo = request.POST.get('correo')

        # 📸 Solo cambiamos la foto si el usuario subió una nueva
        if request.FILES.get('foto'):
            usuario_actual.foto = request.FILES['foto']

        usuario_actual.save()

        # Actualizamos la sesión por si cambió el nombre o el correo
        request.session['cliente_correo'] = usuario_actual.correo
        request.session['cliente_nombre'] = usuario_actual.nombre
        mensaje = '¡Tus datos se actualizaron con éxito!'

    return render(request, 'perfil.html', {
        'usuario': usuario_actual,
        'mensaje': mensaje,
        'sesion_activa': True
    })
# =========================================================================
# 💈 6. PANEL BARBERO (¡Ahora cada barbero ve SUS propias citas!)
# =========================================================================
def panel_barbero(request):
    if 'cliente_nombre' not in request.session: return redirect('login')
    msg_alerta = None
    msg_modal = None

    try:
        usuario_logueado = Usuario.objects.get(correo=request.session['cliente_correo'])
        barbero_obj = Barbero.objects.get(id_usuario=usuario_logueado)
    except Barbero.DoesNotExist:
        return render(request, 'panel_barbero.html', {
            "cliente": request.session['cliente_nombre'],
            "citas": [],
            "sesion_activa": True,
            "alerta": "⚠️ Tu cuenta no tiene una ficha de barbero asociada. Pide al administrador que la revise."
        })

    if request.method == 'POST':
        if 'guardar_estrellas' in request.POST:
            ids_marcados = request.POST.getlist('servicios_estrella')
            BarberoServicioEstrella.objects.filter(id_barbero=barbero_obj).delete()
            for id_serv in ids_marcados:
                servicio_obj = Servicio.objects.get(id_servicio=id_serv)
                BarberoServicioEstrella.objects.create(id_barbero=barbero_obj, id_servicio=servicio_obj)
            msg_alerta = "🌟 ¡Tus servicios estrella se actualizaron con éxito!"

        elif 'subir_foto' in request.POST:
            if request.FILES.get('foto_trabajo'):
                FotoTrabajoBarbero.objects.create(id_barbero=barbero_obj, imagen=request.FILES['foto_trabajo'])
                msg_alerta = "📸 ¡Foto agregada a tu portafolio!"
            else:
                msg_alerta = "⚠️ No seleccionaste ninguna foto."

        elif 'eliminar_foto' in request.POST:
            id_f = request.POST.get('id_foto')
            FotoTrabajoBarbero.objects.filter(id_foto=id_f, id_barbero=barbero_obj).delete()
            msg_alerta = "🗑️ Foto eliminada de tu portafolio."

        elif 'crear_espacio' in request.POST:
            fec = request.POST.get('fecha')
            hora_inicio_str = request.POST.get('hora_inicio')
            hora_fin_str = request.POST.get('hora_fin')
            try:
                h_inicio = int(hora_inicio_str.split(':')[0])
                h_fin = int(hora_fin_str.split(':')[0])
                usuario_comodin = Usuario.objects.filter(rol='administrador').first()
                if not usuario_comodin:
                    usuario_comodin = Usuario.objects.first()

                turnos_creados = 0
                for hora_actual in range(h_inicio, h_fin):
                    hora_formateada = f"{str(hora_actual).zfill(2)}:00:00"
                    if not Cita.objects.filter(fecha=fec, hora=hora_formateada, id_barbero=barbero_obj).exists():
                        Cita(
                            fecha=fec, hora=hora_formateada, estado='pendiente',
                            observaciones='Horario Disponible',
                            id_cliente=usuario_comodin, id_barbero=barbero_obj
                        ).save()
                        turnos_creados += 1

                if turnos_creados > 0:
                    msg_alerta = f"⚡ ¡Éxito! Generaste en bloque {turnos_creados} turnos disponibles para el día {fec}."
                else:
                    msg_alerta = "⚠️ Esos horarios ya se encontraban publicados en tu agenda."
            except Exception as e:
                msg_alerta = f"⚠️ Cortocircuito en la generación de agenda: {e}"

        elif 'id_cita' in request.POST:
            id_c = request.POST.get('id_cita')
            cita = Cita.objects.get(id_cita=id_c)
            if 'confirmar_cita' in request.POST:
                cita.estado = 'confirmada'
                msg_modal = "✅ Cita confirmada con éxito."
            elif 'atender_cita' in request.POST:
                cita.estado = 'atendida'
                msg_modal = "✂️ Turno completado y pasado a cobros."
            elif 'cancelar_cita' in request.POST:
                cita.estado = 'cancelada'
                msg_modal = "❌ Cita cancelada."
            cita.save()

    citas_barbero = Cita.objects.filter(id_barbero=barbero_obj).order_by('fecha', 'hora')
    citas_pendientes_count = citas_barbero.filter(estado='pendiente').exclude(observaciones='Horario Disponible').count()

    for c in citas_barbero:
        if c.observaciones and '|' in c.observaciones:
            c.nombre_limpio_servicio = c.observaciones.split('|')[0]
        else:
            c.nombre_limpio_servicio = c.observaciones

    todos_los_servicios = Servicio.objects.all()
    ids_servicios_estrella = list(BarberoServicioEstrella.objects.filter(id_barbero=barbero_obj).values_list('id_servicio_id', flat=True))
    fotos_trabajo = FotoTrabajoBarbero.objects.filter(id_barbero=barbero_obj).order_by('-fecha_subida')

    return render(request, 'panel_barbero.html', {
        "cliente": request.session['cliente_nombre'],
        "citas": citas_barbero,
        "sesion_activa": True,
        "alerta": msg_alerta,
        "alerta_modal": msg_modal,
        "citas_pendientes_count": citas_pendientes_count,
        "servicios": todos_los_servicios,
        "ids_estrella": ids_servicios_estrella,
        "fotos_trabajo": fotos_trabajo,
        "barbero_actual": barbero_obj,
    })

# =========================================================================
# 💼 7. PANEL ADMINISTRADOR (¡Con Módulo de Cobros, Caja Real y Cambio de Precios!)
# =========================================================================
def panel_administrador(request):
    if 'cliente_nombre' not in request.session: return redirect('login')
    msg_alerta = None
    msg_modal = None

    if request.method == 'POST':
        if 'agregar_servicio' in request.POST:
            nombre_nuevo = request.POST.get('nombre_nuevo_servicio')
            descripcion_nueva = request.POST.get('descripcion_nuevo_servicio')
            precio_nuevo = request.POST.get('precio_nuevo_servicio')
            Servicio.objects.create(nombre_servicio=nombre_nuevo, descripcion=descripcion_nueva, precio=precio_nuevo, estado=1)
            msg_alerta = f"✨ ¡Servicio '{nombre_nuevo}' agregado con éxito!"

        elif 'actualizar_precio' in request.POST:
            id_s = request.POST.get('id_servicio')
            nuevo_p = request.POST.get('nuevo_precio')
            serv = Servicio.objects.get(id_servicio=id_s)
            serv.precio = nuevo_p
            serv.save()
            msg_alerta = f"💰 ¡Hecho Jefa! La tarifa de '{serv.nombre_servicio}' se actualizó a ${nuevo_p} COP."

        elif 'eliminar_usuario' in request.POST:
            id_u = request.POST.get('id_usuario')
            u = Usuario.objects.get(id_usuario=id_u)
            msg_alerta = f"🗑️ El usuario {u.nombre} fue eliminado permanentemente de MySQL."
            u.delete()

        elif 'id_cita' in request.POST:
            id_c = request.POST.get('id_cita')
            cita = Cita.objects.get(id_cita=id_c)
            if 'aceptar_cita' in request.POST:
                cita.estado = 'confirmada'
                msg_modal = "✅ Cita confirmada con éxito."
            elif 'cancelar_cita' in request.POST:
                cita.estado = 'cancelada'
                msg_modal = "❌ Cita cancelada."
            cita.save()

        elif 'cambiar_rol' in request.POST:
            id_u = request.POST.get('id_usuario')
            nuevo_rol = request.POST.get('nuevo_rol')
            usuario = Usuario.objects.get(id_usuario=id_u)
            usuario.rol = nuevo_rol
            usuario.save()
            if nuevo_rol == 'barbero':
                ficha_existente = Barbero.objects.filter(id_usuario=usuario).exists()
                if not ficha_existente:
                    Barbero.objects.create(id_usuario=usuario, especialidad="Por definir", experiencia_anios=0)
                    msg_alerta = "👤 Rol cambiado a BARBERO. Se creó su ficha automáticamente."
                else:
                    msg_alerta = "👤 Rol cambiado a BARBERO."
            else:
                msg_alerta = f"👤 Rol cambiado a {nuevo_rol.upper()}."

    # 🧲 Traemos TODAS las citas como lista (no queryset) para poder clasificarlas en Python
    citas_totales = list(Cita.objects.all().exclude(estado='libre').order_by('fecha', 'hora'))
    usuarios_totales = Usuario.objects.all().order_by('nombre')
    servicios_totales = Servicio.objects.all()

    for c in citas_totales:
        if c.observaciones and '|' in c.observaciones:
            c.nombre_limpio_servicio = c.observaciones.split('|')[0]
        else:
            c.nombre_limpio_servicio = c.observaciones

    # 🗂️ Clasificamos en 4 grupos para las sub-pestañas
    citas_pendientes = [c for c in citas_totales if c.estado == 'pendiente' and c.observaciones != 'Horario Disponible']
    citas_confirmadas = [c for c in citas_totales if c.estado == 'confirmada']
    citas_canceladas = [c for c in citas_totales if c.estado == 'cancelada']
    citas_finalizadas = [c for c in citas_totales if c.estado == 'atendida']

    total_caja = 0
    for cita in citas_finalizadas:
        try:
            partes = cita.observaciones.split('|')
            if len(partes) > 1:
                total_caja += int(float(partes[1]))
            else:
                total_caja += 25000
        except:
            total_caja += 25000

    return render(request, 'panel_admin.html', {
        'usuarios': usuarios_totales,
        'servicios': servicios_totales,
        'sesion_activa': True,
        'alerta': msg_alerta,
        'alerta_modal': msg_modal,
        'ingresos_totales': f"{total_caja:,}",
        'amount_cobros': len(citas_finalizadas),
        'citas_pendientes': citas_pendientes,
        'citas_confirmadas': citas_confirmadas,
        'citas_canceladas': citas_canceladas,
        'citas_finalizadas': citas_finalizadas,
        'citas_pendientes_admin': len(citas_pendientes),
    })

# =========================================================================
# 📅 8. FORMULARIO DE AGENDAR CITAS (Coordinado con el ENUM)
# =========================================================================
def agendar_cita(request):
    if 'cliente_correo' not in request.session: return redirect('login')
    
    turnos_disponibles = Cita.objects.filter(observaciones='Horario Disponible', estado='pendiente').order_by('fecha', 'hora')
    servicios_disponibles = Servicio.objects.all()  # 🎯 CONEXIÓN REAL: traemos los servicios de MySQL
    barberos_disponibles = Barbero.objects.all()

    if request.method == 'POST':
        id_turn = request.POST.get('turno_id')
        ser_elegido = request.POST.get('servicio_elegido') 
        
        try:
            usuario_cliente = Usuario.objects.get(correo=request.session['cliente_correo'])
            
            cita_reservada = Cita.objects.get(id_cita=id_turn)
            cita_reservada.id_cliente = usuario_cliente
            cita_reservada.observaciones = ser_elegido  
            cita_reservada.estado = 'pendiente'         
            cita_reservada.save()                       

            return render(request, 'agendar_cita.html', {
                'mensaje': '¡Tu turno ha sido reservado con éxito! El barbero ya sabe qué servicio quieres.', 
                'turnos': Cita.objects.filter(observaciones='Horario Disponible', estado='pendiente'), 
                'servicios': Servicio.objects.all(),  # 🎯 también aquí
                'barberos_disponibles': barberos_disponibles,
                'sesion_activa': True
            })
        except Exception as e:
            return render(request, 'agendar_cita.html', {
                'mensaje_error': f'⚠️ Error al reservar: {e}', 
                'turnos': turnos_disponibles, 
                'servicios': servicios_disponibles,  # 🎯 también aquí
                'barberos_disponibles': barberos_disponibles,
                'sesion_activa': True
            })
            
    return render(request, 'agendar_cita.html', {
        'turnos': turnos_disponibles, 
        'servicios': servicios_disponibles,  # 🎯 y aquí
        'barberos_disponibles': barberos_disponibles,
        'sesion_activa': True
    })
 # =========================================================================
# 👁️ VER PERFIL PÚBLICO DE UN BARBERO
# =========================================================================
def ver_perfil_barbero(request, id_barbero):
    if 'cliente_correo' not in request.session: return redirect('login')

    barbero_obj = Barbero.objects.get(id_barbero=id_barbero)
    servicios_estrella = BarberoServicioEstrella.objects.filter(id_barbero=barbero_obj)
    fotos_trabajo = FotoTrabajoBarbero.objects.filter(id_barbero=barbero_obj).order_by('-fecha_subida')

    return render(request, 'perfil_barbero_publico.html', {
        'barbero': barbero_obj,
        'servicios_estrella': servicios_estrella,
        'fotos_trabajo': fotos_trabajo,
        'sesion_activa': True
    })

# =========================================================================
# 🎓 9. RUTAS ACADÉMICAS Y DE SALIDA
# =========================================================================
def acerca_de_sena(request): 
    return render(request, 'acerca_de.html', {'sesion_activa': 'cliente_nombre' in request.session})

def pantalla_contacto(request): 
    return render(request, 'contacto.html', {'sesion_activa': 'cliente_nombre' in request.session})

def cerrar_sesion(request): 
    request.session.flush()
    return redirect('inicio')
