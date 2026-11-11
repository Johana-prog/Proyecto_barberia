"""Sube a Cloudinary las fotos que ya estaban en la carpeta media/. Se corre una sola vez."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import cloudinary
import cloudinary.uploader

MEDIA = Path(__file__).resolve().parent / 'media'
EXTENSIONES = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}

if not os.environ.get('CLOUDINARY_URL'):
    raise SystemExit('Falta CLOUDINARY_URL en el archivo .env')

subidas = 0
for archivo in sorted(MEDIA.rglob('*')):
    if archivo.suffix.lower() not in EXTENSIONES:
        continue
    relativo = archivo.relative_to(MEDIA).as_posix()
    public_id = os.path.splitext(relativo)[0]
    cloudinary.uploader.upload(str(archivo), public_id=public_id, overwrite=True, resource_type='image')
    subidas += 1
    print('Subida:', relativo)

print(f'Listo: {subidas} fotos subidas.')