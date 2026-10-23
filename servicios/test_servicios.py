from django.test import Client


def test_pagina_login():
    cliente = Client()
    respuesta = cliente.get("/login/")
    assert respuesta.status_code == 200


def test_pagina_agendar_sin_sesion():
    cliente = Client()
    respuesta = cliente.get("/agendar/")
    assert respuesta.status_code == 302