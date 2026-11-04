import os
import re
import sys

import django

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barberia.settings')
django.setup()

from servicios.models import Servicio, Barbero, Cita

EMOJI = re.compile(r'[\U0001F000-\U0001FAFF\u2300-\u23FF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D]+')


def limpiar(texto):
    return re.sub(r'\s+', ' ', EMOJI.sub('', texto)).strip()


aplicar = '--aplicar' in sys.argv

# Nombres oficiales de los servicios (sin emojis), para unificar las citas viejas
canonicos = {}
for s in Servicio.objects.all():
    nombre = limpiar(s.nombre_servicio)
    canonicos[nombre.casefold()] = nombre


def limpiar_observacion(texto):
    if '|' in texto:
        nombre, resto = texto.split('|', 1)
        nombre = limpiar(nombre)
        nombre = canonicos.get(nombre.casefold(), nombre)
        return nombre + '|' + resto.strip()
    return limpiar(texto)


cambios = []


def revisar(objeto, campo, funcion=limpiar):
    original = getattr(objeto, campo)
    if original and EMOJI.search(original):
        nuevo = funcion(original)
        if nuevo != original:
            cambios.append((objeto, campo, original, nuevo))


for s in Servicio.objects.all():
    revisar(s, 'nombre_servicio')
    revisar(s, 'descripcion')

for b in Barbero.objects.all():
    revisar(b, 'especialidad')

for c in Cita.objects.all():
    revisar(c, 'observaciones', limpiar_observacion)

if not cambios:
    print('No hay emojis en los datos. Todo limpio.')
else:
    print(f'Se encontraron {len(cambios)} cambios:\n')
    for objeto, campo, antes, despues in cambios:
        print(f'  {objeto.__class__.__name__} #{objeto.pk} · {campo}')
        print(f'      antes:   {antes}')
        print(f'      después: {despues}')

    if aplicar:
        for objeto, campo, antes, despues in cambios:
            setattr(objeto, campo, despues)
            objeto.save(update_fields=[campo])
        print('\nCambios aplicados.')
    else:
        print('\nEsto fue solo una vista previa. No se modificó nada.')
        print('Si todo se ve bien, aplica los cambios con:')
        print('    python limpiar_datos.py --aplicar')