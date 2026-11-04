# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


# =========================================================================
# 🔒 TABLAS INTERNAS AUTOMÁTICAS DE SEGURIDAD DE DJANGO (NO TOCAR)
# =========================================================================

class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


# =========================================================================
# 💈 TABLAS REALES DE TU PROYECTO DE BARBERÍA (CONECTADAS A WORKBENCH)
# =========================================================================

class Barbero(models.Model):
    id_barbero = models.AutoField(primary_key=True)
    # Llave foránea amarrada a la tabla Usuario
    id_usuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='id_usuario')
    especialidad = models.CharField(max_length=100, blank=True, null=True)
    experiencia_anios = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'barbero'


class Cita(models.Model):
    id_cita = models.AutoField(primary_key=True)
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(max_length=10, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    # Llaves foráneas obligatorias del circuito de agendamiento
    id_cliente = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='id_cliente')
    id_barbero = models.ForeignKey(Barbero, models.DO_NOTHING, db_column='id_barbero')

    class Meta:
        managed = False
        db_table = 'cita'


class DetalleCita(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    id_cita = models.ForeignKey(Cita, models.DO_NOTHING, db_column='id_cita')
    id_servicio = models.ForeignKey('Servicio', models.DO_NOTHING, db_column='id_servicio')
    precio_aplicado = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'detalle_cita'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class HorarioBarbero(models.Model):
    id_horario = models.AutoField(primary_key=True)
    id_barbero = models.ForeignKey(Barbero, models.DO_NOTHING, db_column='id_barbero')
    dia_semana = models.CharField(max_length=9)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        managed = False
        db_table = 'horario_barbero'


class Pago(models.Model):
    id_pago = models.AutoField(primary_key=True)
    id_cita = models.ForeignKey(Cita, models.DO_NOTHING, db_column='id_cita')
    fecha_pago = models.DateField(blank=True, null=True)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=13)
    estado_pago = models.CharField(max_length=9, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pago'


class Servicio(models.Model):
    id_servicio = models.AutoField(primary_key=True)
    nombre_servicio = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_minutos = models.IntegerField(blank=True, null=True)
    
    # 💡 OPCIONES DEL ESTADO DEL SERVICIO: Texto de la lista desplegable en español
    OPCIONES_ESTADO_SERVICIO = [
        (1, 'Disponible'),
        (0, 'No Disponible'),
    ]
    # Transformamos el número frío por un menú interactivo con un valor por defecto de 1
    estado = models.IntegerField(blank=True, null=True, choices=OPCIONES_ESTADO_SERVICIO, default=1)

    class Meta:
        managed = False
        db_table = 'servicio'

    # 🏷️ El letrero para que Django muestre el nombre del corte de cabello en el panel
    def __str__(self):
        return self.nombre_servicio 

class BarberoServicioEstrella(models.Model):
    id_relacion = models.AutoField(primary_key=True)
    id_barbero = models.ForeignKey(Barbero, models.CASCADE, db_column='id_barbero')
    id_servicio = models.ForeignKey(Servicio, models.CASCADE, db_column='id_servicio')

    class Meta:
        managed = False
        db_table = 'barbero_servicio_estrella'
        unique_together = (('id_barbero', 'id_servicio'),)


class FotoTrabajoBarbero(models.Model):
    id_foto = models.AutoField(primary_key=True)
    id_barbero = models.ForeignKey(Barbero, models.CASCADE, db_column='id_barbero')
    imagen = models.ImageField(upload_to='trabajos_barberos/')
    fecha_subida = models.DateField(blank=True, null=True, auto_now_add=True)
    nombre_estilo = models.CharField(max_length=80, blank=True, null=True)
    id_servicio = models.ForeignKey('Servicio', models.SET_NULL, db_column='id_servicio', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'foto_trabajo_barbero'

class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    documento = models.CharField(unique=True, max_length=20)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    foto = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    correo = models.CharField(unique=True, max_length=100)
    contraseña = models.CharField(max_length=255)
    rol = models.CharField(max_length=13)
    fecha_registro = models.DateField(blank=True, null=True)
    
    # 💡 OPCIONES DEL ESTADO DEL USUARIO: Para que el administrador no cometa errores numéricos
    OPCIONES_ESTADO_USUARIO = [
        (1, 'Activo'),
        (0, 'Inactivo'),
    ]
    # Transformamos la cajita de texto en una lista desplegable humana de opciones fijas
    estado = models.IntegerField(blank=True, null=True, choices=OPCIONES_ESTADO_USUARIO, default=1)

    class Meta:
        managed = False
        db_table = 'usuario'

    # 🏷️ ¡CORREGIDO! Con doble guion bajo en cada lado para ver el Nombre y Apellido humano del cliente
    def __str__(self):
        return f"{self.nombre} {self.apellido}"

  