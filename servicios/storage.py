"""
Almacenamiento de fotos en Cloudinary.

En Azure el disco del servidor no guarda archivos de forma permanente, así que las fotos
(perfiles y trabajos de los barberos) se suben a Cloudinary. En la base de datos se guarda
solo el nombre del archivo, por ejemplo «perfiles/foto_ab12cd34.jpg», y de ahí se arma la dirección.
"""
import io
import os
import uuid

import cloudinary
import cloudinary.uploader
import cloudinary.utils
from django.core.files.storage import Storage


class CloudinaryMediaStorage(Storage):

    def get_available_name(self, name, max_length=None):
        # Cada foto recibe un sufijo al azar: dos archivos con el mismo nombre nunca se pisan
        carpeta, archivo = os.path.split(name)
        base, extension = os.path.splitext(archivo)
        nombre = f"{base}_{uuid.uuid4().hex[:8]}{extension.lower()}"
        return f"{carpeta}/{nombre}" if carpeta else nombre

    def _save(self, name, content):
        public_id = os.path.splitext(name)[0]
        content.seek(0)
        resultado = cloudinary.uploader.upload(
            io.BytesIO(content.read()),
            public_id=public_id,
            resource_type="image",
        )
        return f"{resultado['public_id']}.{resultado['format']}"

    def _open(self, name, mode="rb"):
        raise NotImplementedError("Las fotos se leen desde la dirección de Cloudinary.")

    def exists(self, name):
        return False

    def delete(self, name):
        public_id = os.path.splitext(name)[0]
        try:
            cloudinary.uploader.destroy(public_id, resource_type="image")
        except Exception:
            pass

    def url(self, name):
        public_id, extension = os.path.splitext(name)
        direccion, _ = cloudinary.utils.cloudinary_url(public_id, format=extension.lstrip("."), secure=True)
        return direccion