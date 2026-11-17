"""config/esquema_portfolio.json: casos válidos e inválidos de repo y de proyecto sin repo."""

import copy
import json

import pytest
from jsonschema import Draft202012Validator

from portfolio import CARPETA_CONFIG


def validador(definicion):
    with open(CARPETA_CONFIG / "esquema_portfolio.json", encoding="utf-8") as archivo:
        esquema = json.load(archivo)
    esquema["$ref"] = "#/$defs/" + definicion
    return Draft202012Validator(esquema)


REPO_VALIDO = {
    "version": 1,
    "visible": True,
    "mostrar_bitacora": False,
    "nombre": "Proyecto de prueba",
    "descripcion": "Una línea.",
    "estado": "activo",
    "tecnologias": ["Python"],
    "links": {"demo": "https://ejemplo.test", "repo": "auto", "otros": []},
    "imagen": {"archivo": "docs/captura.png", "alt": "Una captura", "aprobada": "0123456789ab"},
}

EXTRA_VALIDO = {
    "version": 1,
    "visible": True,
    "mostrar_bitacora": False,
    "nombre": "Extra",
    "slug": "extra",
    "descripcion": "Una línea.",
    "estado": "terminado",
    "fecha_inicio": "2025-01",
    "fecha_fin": "2025-06",
    "ultima_actividad": "2025-06",
    "tecnologias": ["Make.com"],
    "imagen": {"archivo": "imagenes/extra.png", "alt": "Captura"},
}


def test_repo_valido():
    assert list(validador("portfolio_repo").iter_errors(REPO_VALIDO)) == []


def test_extra_valido():
    assert list(validador("proyecto_extra").iter_errors(EXTRA_VALIDO)) == []


def con_cambio(base, ruta, valor):
    datos = copy.deepcopy(base)
    actual = datos
    for parte in ruta[:-1]:
        actual = actual[parte]
    if valor is BORRAR:
        del actual[ruta[-1]]
    else:
        actual[ruta[-1]] = valor
    return datos


BORRAR = object()

CASOS_REPO_INVALIDOS = [
    ("falta descripcion", ("descripcion",), BORRAR),
    ("estado raro", ("estado",), "en_pausa"),
    ("activo con fecha_fin", ("fecha_fin",), "2026-01"),
    ("demo http", ("links", "demo"), "http://ejemplo.test"),
    ("slug inválido", ("slug",), "Con_Mayus"),
    ("imagen sin alt", ("imagen", "alt"), BORRAR),
    ("campo desconocido", ("descripción",), "typo"),
    ("ultima_actividad en repo", ("ultima_actividad",), "2026-01"),
    ("imagen con ..", ("imagen", "archivo"), "../afuera.png"),
    ("aprobada corta", ("imagen", "aprobada"), "abc"),
]


@pytest.mark.parametrize("nombre,ruta,valor", CASOS_REPO_INVALIDOS)
def test_repo_invalido(nombre, ruta, valor):
    datos = con_cambio(REPO_VALIDO, ruta, valor)
    assert list(validador("portfolio_repo").iter_errors(datos)) != [], nombre


def test_terminado_sin_fecha_fin():
    datos = con_cambio(REPO_VALIDO, ("estado",), "terminado")
    assert list(validador("portfolio_repo").iter_errors(datos)) != []


CASOS_EXTRA_INVALIDOS = [
    ("sin slug", ("slug",), BORRAR),
    ("sin fecha_inicio", ("fecha_inicio",), BORRAR),
    ("sin ultima_actividad", ("ultima_actividad",), BORRAR),
    ("con bitácora", ("mostrar_bitacora",), True),
    ("con repo", ("links",), {"repo": "auto"}),
    ("imagen fuera de imagenes/", ("imagen", "archivo"), "otra/extra.png"),
]


@pytest.mark.parametrize("nombre,ruta,valor", CASOS_EXTRA_INVALIDOS)
def test_extra_invalido(nombre, ruta, valor):
    datos = con_cambio(EXTRA_VALIDO, ruta, valor)
    assert list(validador("proyecto_extra").iter_errors(datos)) != [], nombre
