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