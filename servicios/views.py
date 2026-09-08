from django.shortcuts import render, redirect
from servicios.models import Servicio, Usuario, Barbero, Cita
import datetime

# 🏠 1. PÁGINA PRINCIPAL PÚBLICA
def inicio_barberia(request):
    ahora = datetime.datetime.now().strftime("%d/%m/%Y a las %H:%M")
    servicios_base_datos = Servicio.objects.all()
    barberos_base_datos = Barbero.objects.all()
    sesion = 'cliente_nombre' in request.session
    return render(request, 'inicio.html', {
        "servicios": servicios_base_datos,
        "barberos": barberos_base_datos,
        "fecha_actual": ahora,
        "sesion_activa": sesion
    })

# 📝 2. REGISTRO DE CLIENTES (Ojos de seguridad)
def registrar_cliente(request):
    if request.method == 'POST':
        nom = request.POST.get('nombre')
        ape = request.POST.get('apellido')
        doc = request.POST.get('documento')
        cor = request.POST.get('correo')
        cla = request.POST.get('contraseña')

        if Usuario.objects.filter(documento=doc).exists():
            return render(request, 'registro.html', {'mensaje_error': '⚠️ Error: Este documento ya existe.'})
        if Usuario.objects.filter(correo=cor).exists():
            return render(request, 'registro.html', {'mensaje_error': '⚠️ Error: Este correo ya está en uso.'})

        try:
            nuevo = Usuario(nombre=nom, apellido=ape, documento=doc, correo=cor, contraseña=cla, rol="cliente", estado=1)
            nuevo.save()
            return render(request, 'registro.html', {'mensaje': '¡Cuenta creada con éxito!'})
        except Exception as e:
            return render(request, 'registro.html', {'mensaje_error': f'⚠️ Error: {e}'})
    return render(request, 'registro.html')

# 👤 3. INICIO DE SESIÓN / ENRUTAMIENTO POR ROLES
def iniciar_sesion(request):
    # CONTROL DE ENTRADA RÁPIDA: Si ya tiene la sesión abierta
    if 'cliente_nombre' in request.session and 'cliente_rol' in request.session and request.method == 'GET':
        rol = request.session['cliente_rol']
        if rol == 'administrador': return redirect('panel_admin')
        elif rol == 'barbero': return redirect('panel_barbero')
        else: return redirect('panel_cliente')

    # PROCESO CUANDO ENGANCHA EL POST CON CLAVE
    if request.method == 'POST':
        correo_digitado = request.POST.get('correo')
        clave_digitada = request.POST.get('contraseña')

        try:
            user = Usuario.objects.get(correo=correo_digitado)
            if user.contraseña == clave_digitada:
                # Seteamos las sesiones seguras
                request.session['cliente_nombre'] = user.nombre
                request.session['cliente_correo'] = user.correo
                request.session['cliente_rol'] = user.rol
                
                # Desvíos directos según la base de datos
                if user.rol == 'administrador': return redirect('panel_admin')
                elif user.rol == 'barbero': return redirect('panel_barbero')
                else: return redirect('panel_cliente')
            else:
                return render(request, 'login.html', {"error": "⚠️ Contraseña incorrecta."})
        except Usuario.DoesNotExist:
            return render(request, 'login.html', {"error": "⚠️ Este correo no existe."})
    return render(request, 'login.html')

# 👑 4. PANEL DEL CLIENTE
def panel_cliente(request):
    if 'cliente_nombre' not in request.session: return redirect('login')
    usuario_actual = Usuario.objects.get(correo=request.session['cliente_correo'])
    barberos_base_datos = Barbero.objects.all()
    mis_citas = Cita.objects.filter(id_cliente=usuario_actual).order_by('fecha', 'hora')
    return render(request, 'panel_cliente.html', {
        "cliente": request.session['cliente_nombre'],
        "barberos": barberos_base_datos,
        "citas": mis_citas,
        "sesion_activa": True
    })

# ⚙️ 6. PERFIL DEL CLIENTE
def configurar_perfil(request):
    if 'cliente_correo' not in request.session: return redirect('login')
    usuario_actual = Usuario.objects.get(correo=request.session['cliente_correo'])
    if request.method == 'POST':
        usuario_actual.telefono = request.POST.get('telefono')
        usuario_actual.correo = request.POST.get('correo')
        usuario_actual.save()
        request.session['cliente_correo'] = usuario_actual.correo
        return render(request, 'perfil.html', {'usuario': usuario_actual, 'mensaje': '¡Datos actualizados!', 'sesion_activa': True})
    return render(request, 'perfil.html', {'usuario': usuario_actual, 'sesion_activa': True})

# 💈 6. PANEL DEL BARBERO (Con triple botón)
def panel_barbero(request):
    if 'cliente_nombre' not in request.session: return redirect('login')

    if request.method == 'POST':
        id_c = request.POST.get('id_cita')
        cita = Cita.objects.get(id_cita=id_c)
        
        if 'confirmar_cita' in request.POST: cita.estado = 'confirmada'
        elif 'atender_cita' in request.POST: cita.estado = 'atendida'
        elif 'cancelar_cita' in request.POST: cita.estado = 'cancelada'
        cita.save()

    citas_barbero = Cita.objects.filter(id_barbero=1).order_by('fecha', 'hora')
    return render(request, 'panel_barbero.html', {
        "cliente": request.session['cliente_nombre'],
        "citas": citas_barbero,
        "sesion_activa": True
    })

# 💼 7. PANEL DEL ADMINISTRADOR
def panel_administrador(request):
    if request.method == 'POST':
        id_c = request.POST.get('id_cita')
        cita = Cita.objects.get(id_cita=id_c)
        if 'aceptar_cita' in request.POST: cita.estado = 'confirmada'
        elif 'cancelar_cita' in request.POST: cita.estado = 'cancelada'
        cita.save()

    citas_totales = Cita.objects.all().order_by('fecha', 'hora')
    return render(request, 'panel_admin.html', {'citas': citas_totales, 'sesion_activa': True})

# 📅 8. AGENDAR CITAS Y OTROS
def agendar_cita(request):
    barberos_base_datos = Barbero.objects.all()
    if request.method == 'POST':
        fec = request.POST.get('fecha')
        hor = request.POST.get('hora')
        id_bar = request.POST.get('barbero')
        obs = request.POST.get('observaciones')
        try:
            barbero_elegido = Barbero.objects.get(id_barbero=id_bar)
            usuario_cliente = Usuario.objects.get(correo=request.session['cliente_correo'])
            nueva_cita = Cita(fecha=fec, hora=hor, estado="pendiente", observaciones=obs, id_cliente=usuario_cliente, id_barbero=barbero_elegido)
            nueva_cita.save()
            return render(request, 'agendar_cita.html', {'mensaje': '¡Cita agendada!', 'barberos': barberos_base_datos, 'sesion_activa': True})
        except Exception as e:
            return render(request, 'agendar_cita.html', {'mensaje': f'⚠️ Error: {e}', 'barberos': barberos_base_datos, 'sesion_activa': True})
    return render(request, 'agendar_cita.html', {'barberos': barberos_base_datos, 'sesion_activa': True})

def cerrar_sesion(request):
    request.session.flush()
    return redirect('inicio')

def contacto(request):
    return render(request, 'contacto.html', {'sesion_activa': 'cliente_nombre' in request.session})
