"""proyectos_extra.py (paso 31)."""

import datetime

import pytest

from portfolio.archivo_estandar import ErrorArchivoEstandar
from portfolio.imagenes import tipo_real
from portfolio.proyectos_extra import esta_desactualizado, leer_extra, leer_imagen_extra, listar_archivos

from tests.utiles import FIXTURES

CARPETA = FIXTURES / "extras"


def test_lista_solo_md_en_orden():
    nombres = []
    for ruta in listar_archivos(CARPETA):
        nombres.append(ruta.name)
    assert nombres == ["automatizacion-inventada.md", "nombre-equivocado.md"]


def test_carpeta_inexistente_da_lista_vacia(tmp_path):
    assert listar_archivos(tmp_path / "no-existe") == []


def test_lee_extra_valido():
    extra = leer_extra(CARPETA / "automatizacion-inventada.md")
    datos = extra["datos"]
    assert extra["clave"] == "extra-automatizacion-inventada"
    assert extra["advertencias"] == []
    assert datos["ultima_actividad"] == "2026-10"
    assert datos["links"]["repo"] is None
    assert datos["mostrar_bitacora"] is False
    assert datos["captura_auto"] is True
    assert tipo_real(leer_imagen_extra(extra)) == "png"


def test_nombre_de_archivo_distinto_del_slug():
    with pytest.raises(ErrorArchivoEstandar):
        leer_extra(CARPETA / "nombre-equivocado.md")


def test_imagen_fuera_de_imagenes_se_rechaza():
    extra = leer_extra(CARPETA / "automatizacion-inventada.md")
    extra["datos"]["imagen"]["archivo"] = "imagenes/../../portfolio/valido.md"
    with pytest.raises(ErrorArchivoEstandar):
        leer_imagen_extra(extra)


def test_desactualizado():
    datos = {"estado": "activo", "ultima_actividad": "2026-01"}
    assert esta_desactualizado(datos, datetime.date(2026, 7, 31)) is False
    assert esta_desactualizado(datos, datetime.date(2026, 8, 1)) is True
    datos["estado"] = "terminado"
    assert esta_desactualizado(datos, datetime.date(2030, 1, 1)) is False
