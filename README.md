# Usme Barber Top

Sistema web de gestión de citas para una barbería. Permite a los clientes reservar turnos en línea, a los barberos administrar su agenda y su portafolio, y a la administración controlar citas, usuarios, tarifas y estadísticas.

Proyecto académico del SENA · Tecnólogo en Análisis y Desarrollo de Software (ADSO).
Autoría: [Tu nombre]

**Sitio desplegado:** _pendiente_

## Funcionalidades

**Cliente**
- Reserva turnos libres eligiendo servicio y horario, y ve el total antes de reservar.
- Cancela sus citas hasta 2 horas antes; el horario queda libre para otras personas.
- Consulta sus citas por estado (próximas, atendidas, canceladas, vencidas) y sus estadísticas personales.
- Recibe correos al reservar, al confirmarse y al cancelarse una cita.
- Asistente de estilo que recomienda un servicio según su cabello, su rostro y su estilo.
- Galería pública de estilos de corte, con filtro por servicio.

**Barbero**
- Publica su jornada por horas y puede quitar turnos libres.
- Confirma, atiende o cancela las reservas, organizadas por estado.
- Administra su portafolio de fotos y sus servicios estrella.
- Estadísticas personales (ingresos, servicios más pedidos, citas por día).

**Administrador**
- Gestiona todas las citas con cliente, barbero, fecha, servicio y precio.
- Cambia roles y activa o desactiva cuentas (las cuentas no se eliminan, para conservar el historial).
- Administra los servicios y sus tarifas.
- Estadísticas generales con gráficas.

**General**
- Inicio de sesión con contraseñas cifradas y control de acceso por rol.
- Recuperación de contraseña por correo, con enlace que vence en 60 minutos y solo sirve una vez.
- Diseño adaptable a celular, con atención a la accesibilidad (etiquetas, foco visible, lectores de pantalla, respeto por «reducir animaciones»).

## Tecnologías

- Python 3.14 y Django 6
- MySQL (`mysqlclient`); consultas con el ORM de Django
- Cloudinary para las fotos subidas por los usuarios
- Envío de correos por SMTP (Gmail)
- WhiteNoise y Gunicorn para producción
- Docker (`Dockerfile`) y Azure para el despliegue
- Chart.js para las gráficas

## Estructura

```
barberia/        configuración del proyecto (settings, urls) y plantillas HTML
servicios/       aplicación principal
  models.py      modelos de la base de datos
  views.py       vistas: reciben la petición y muestran el resultado
  services.py    reglas de negocio (reservar, cancelar, roles, recuperar contraseña)
  correos.py     mensajes de correo
  storage.py     almacenamiento de fotos en Cloudinary
static/          estilos, imágenes y scripts
```

## Instalación local

1. Clona el repositorio e instala las dependencias:

   ```
   git clone https://github.com/Johana-prog/Proyecto_barberia.git
   cd Proyecto_barberia
   pip install -r requirements.txt
   ```

2. Crea la base de datos MySQL `gestorbarberia` e importa las tablas desde MySQL Workbench. Las tablas se crean fuera de Django (`managed = False`).

3. Copia `.env.example` como `.env` y completa los valores (clave secreta, base de datos, Cloudinary y correo). El archivo `.env` nunca se sube al repositorio.

4. Inicia el servidor:

   ```
   python manage.py runserver
   ```

## Variables de entorno

| Variable | Para qué sirve |
| --- | --- |
| `SECRET_KEY` | Clave secreta de Django |
| `DEBUG` | `True` solo en desarrollo |
| `ALLOWED_HOSTS` | Direcciones permitidas, separadas por comas |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Conexión a MySQL |
| `DB_SSL` | `True` para exigir conexión cifrada (Azure) |
| `CLOUDINARY_URL` | Credenciales de Cloudinary; sin ella, las fotos se guardan en `media/` |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Cuenta y contraseña de aplicación para enviar correos; sin ellas, los correos se imprimen en la terminal |

## Roles

| Rol | Acceso |
| --- | --- |
| Cliente | Reservas, su agenda y sus estadísticas |
| Barbero | Su agenda, su portafolio y sus estadísticas |
| Administrador | Citas, usuarios, tarifas y estadísticas generales |

## Despliegue

El proyecto incluye `requirements.txt` y un `Dockerfile`. En producción se sirve con Gunicorn, los archivos estáticos con WhiteNoise y las fotos desde Cloudinary.