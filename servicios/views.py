#from django.http import HttpResponse 
#import datetime
#from django.template import Template, Context
#import datetime
#from django.template.loader import get_template
from django.shortcuts import render
from django.http import HttpResponse
import datetime
from servicios.models import Servicio, Usuario, Barbero , Cita
import datetime

# Este es nuestro "mesero" que saluda a los clientes de la barbería
def bienvenida(request):  #primera vista
    return HttpResponse("¡Bienvenidos a la Barbería! Aquí verás los mejores cortes.")

# segunda vista
def contacto(request):
    return render(request, 'contacto.html')

# Este mesero recibe el 'request' del cliente Y ADEMÁS el 'nombre' del barbero
def perfil_barbero(request, nombre):
    return HttpResponse(f"💇‍♂️ Estás viendo el perfil del barbero: {nombre.capitalize()}. ¡Agenda tu cita con él!")

#aqui vamos a hacer una calculadora de puntos de fidelidad
def calcular_puntos(request, cantidad_cortes):
    #convertimos el texto de la url en un numero entero (int) para multiplicar
    cortes = int(cantidad_cortes)
    total_puntos = cortes * 10

    return HttpResponse(f"🏆 Si te haces {cortes} cortes con nosotras, ¡acumularás {total_puntos} puntos para cortes gratis!") 

#nueva vista hora actual recuerda importar datetime
def hora_actual(request):
    #le preguntamos la hora exacta a la computadora
    ahora = datetime.datetime.now()
    # se le da un formato bonito (hora:minutos)
    hora_formateada = ahora.strftime("%H:%M")

    return HttpResponse(f"⏰ La hora actual es {hora_formateada}. Recuerda que nuestro horario de atención es de 8am a 6pm.")

# que nunca se te olvide agregar las herramientas que necesitas en este caso template  y context 
# from django.template import template, context

#def inicio_barberia(request):
    #abrimos el archivo HTML usando la ruta de nuestro pc cambia la posicion de las barras 
    #doc_externo = open("C:/Users/HP/Desktop/Proyecto_barbershop/barberia/barberia/plantillas/inicio.html")

    #django lee el contenido del archivo
    #plt= Template(doc_externo.read())
    #se cierra el archivo porque ya lo leimos 
    #doc_externo.close()  <- asi importamos documentos

    # otra forma de importar recuerda que se agrego la ruta en settings templates dirs
    #plt = get_template('inicio.html')

    ahora = datetime.datetime.now().strftime ("%d/%m/%Y a las %H:%M")
   
    # 1. Creamos nuestra lista de servicios de la barbería
    lista_servicios = ["Corte Clásico ✂️", "Perfilado de Barba 🧔", "Tintura Platinada 🎨", "Lavado Premium 🧼"]
     

    # 2. Metemos la lista como un ingrediente en el diccionario
    # aqui quitamos el conetext porque estamos usando get_template
    #datos = {
        #"cliente": "Johana",
       # "servicios": lista_servicios ,# <-- Aquí pasamos la lista completa
       # "fecha_actual":ahora 
    # }
    
    # 2. 🪄 ¡EL TRUCO MAGÍCO! Todo se hace en una sola línea gracias a 'render'
    return render(request, 'inicio.html', {
        "cliente": "Johana",
        "servicios": lista_servicios,
        "fecha_actual": ahora 
    })

    # combinamos template con contexto cuando impostamos de la forma larga
    # renderizamos pasando directamente el diccionario porque importamos con get_template
    documento_final = plt.render(datos)

    # se entrega el resultado final al navegador del cliente
    return HttpResponse(documento_final)

def inicio_barberia(request):
    # 1. Le pedimos la hora al reloj del sistema
    ahora = datetime.datetime.now().strftime("%d/%m/%Y a las %H:%M")
    
    # 2. 🧲 ¡EL COMANDO MÁGICO DE LECTURA! 
    # Django viaja a MySQL Workbench y se trae TODOS los servicios que tengas guardados
    servicios_base_datos = Servicio.objects.all()

    # 🧲 IMÁN 2: ¡NUEVO! Django viaja a MySQL y se trae a TODOS tus barberos reales
    barberos_base_datos = Barbero.objects.all()
    # 3. Le pasamos los datos reales de la base de datos a tu plantilla HTML
   
      # Pasamos las dos listas reales a tu plantilla HTML dentro de la caja organizadora
    return render(request, 'inicio.html', {
        "cliente": request.GET.get('user', 'Invitado'), # Saludo dinámico inicial
        "servicios": servicios_base_datos,
        "barberos": barberos_base_datos,  # <-- Enviamos los barberos a la pantalla
        "fecha_actual": ahora 
    })


def registrar_cliente(request):
    # 1. ¿El usuario hundió el botón rojo de enviar (POST)?
    if request.method == 'POST':
        # 2. El mesero mete la mano en el sobre y saca los textos de las cajitas
        nom = request.POST.get('nombre')
        ape = request.POST.get('apellido')
        doc = request.POST.get('documento')
        cor = request.POST.get('correo')
        cla = request.POST.get('contraseña')

        # 3. Usamos tu molde de Workbench para crear el registro
        nuevo_usuario = Usuario(
            nombre=nom,
            apellido=ape,
            documento=doc,
            correo=cor,
            contraseña=cla,
            rol="cliente",        # Todos los que se registren entran como clientes
            estado=1
        )
        # 4. 💾 El comando rey: ¡Directo a MySQL!
        nuevo_usuario.save()

        # 5. Le avisamos que todo salió bien mandándolo a una pantalla de éxito
        return render(request, 'registro.html', {'mensaje': '¡Cuenta creada con éxito! Bienvenido a la Barbería.'})

    # Si la persona solo viene a mirar la página (GET), le mostramos el formulario vacío
    return render(request, 'registro.html')

def iniciar_sesion(request):
    # 1. ¿El usuario hundió el botón de ENTRAR (POST)?
    if request.method == 'POST':
        correo_digitado = request.POST.get('correo')
        clave_digitada = request.POST.get('contraseña')

        try:
            usuario_encontrado = Usuario.objects.get(correo=correo_digitado)
            
            if usuario_encontrado.contraseña == clave_digitada:
                # 🧲 Traemos los barberos reales para mostrarlos en el panel derecho
                barberos_base_datos = Barbero.objects.all()
                
                # 🚀 ¡CAMBIO CLAVE! Mandamos al usuario a su panel privado con su nombre
                return render(request, 'panel_cliente.html',  {
                    "cliente": usuario_encontrado.nombre,
                    "barberos": barberos_base_datos,
                     "sesion_activa": True  # 💡 OJO AQUI LE AVISAMOS AL MENÚ QUE YA ENTRÓ
                })
            else:
                return render(request, 'login.html', {"error": "⚠️ Contraseña incorrecta. Inténtalo de nuevo."})
                
        except Usuario.DoesNotExist:
            # Si el correo no existe en la base de datos, entra aquí
            return render(request, 'login.html', {"error": "⚠️ Este correo no está registrado en el sistema."})

    # Si entra por primera vez a mirar la página (GET), le mostramos el formulario vacío
    return render(request, 'login.html')

def agendar_cita(request):
    # 1. Traemos los barberos de MySQL para llenar la cajita de opciones del formulario
    barberos_base_datos = Barbero.objects.all()

    # 2. ¿El cliente hundió el botón de CONFIRMAR RESERVA (POST)?
    if request.method == 'POST':
        fec = request.POST.get('fecha')
        hor = request.POST.get('hora')
        id_bar = request.POST.get('barbero')
        obs = request.POST.get('observaciones')

        try:
            # 🛡️ Control de llaves foráneas: Buscamos los registros reales en sus cajones
            barbero_elegido = Barbero.objects.get(id_barbero=id_bar)
            # Como prueba, asignamos la cita al usuario número 1 o al primero disponible
            usuario_cliente = Usuario.objects.first() 

            # 3. Amasamos el molde de la Cita con los datos del sobre
            nueva_cita = Cita(
                fecha=fec,
                hora=hor,
                estado="pendiente",  # Nace con el estado por defecto de tu script SQL
                observaciones=obs,
                id_cliente=usuario_cliente, # Llave foránea obligatoria
                id_barbero=barbero_elegido   # Llave foránea obligatoria
            )
            # 4. 💾 El comando rey: ¡Directo al archivador MySQL Workbench!
            nueva_cita.save()

            return render(request, 'agendar_cita.html', {
                'mensaje': '¡Tu cita ha sido agendada con éxito! Te esperamos.',
                'barberos': barberos_base_datos
            })
            
        except Exception as e:
            return render(request, 'agendar_cita.html', {
                'mensaje': f'⚠️ Hubo un error al guardar: {e}',
                'barberos': barberos_base_datos
            })

    # Si entra por primera vez (GET), le mostramos el formulario vacío con los barberos listos
    return render(request, 'agendar_cita.html', {'barberos': barberos_base_datos})
