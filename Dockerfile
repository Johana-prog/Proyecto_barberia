# Imagen base: Python liviano
FROM python:3.14-slim

# Python no genera archivos .pyc y muestra los mensajes al instante en el registro
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Piezas del sistema que necesita mysqlclient para conectarse a MySQL
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential pkg-config default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Primero solo la lista de paquetes: así Docker reutiliza este paso si no cambió
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Después, el código del proyecto
COPY . .

# El servidor no corre como administrador
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Junta los archivos de diseño y arranca el servidor de producción
CMD ["sh", "-c", "python manage.py collectstatic --noinput && gunicorn barberia.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120"]