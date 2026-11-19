"""salida.py: lista blanca, versión anterior ante falla, slugs, orden y escritura estable (paso 32)."""

import copy
import json

import pytest

import validar_datos
from portfolio import CARPETA_CONFIG
from portfolio.archivo_estandar import leer_archivo_estandar
from portfolio.etiquetas import cargar_catalogo
from portfolio.salida import (
    ErrorFallaTotal,
    armar_proyecto,
    escribir_proyectos,
    limpiar_imagenes,
    ordenar,
    proyectos_anteriores,
    resolver_resultados,
    resolver_slugs,
)

from tests.utiles import FIXTURES

ESQUEMA = validar_datos.leer_json(CARPETA_CONFIG / "esquema_salida.json")


def errores_de_esquema(proyectos):
    datos = {"version": 1, "proyectos": proyectos}
    return validar_datos.errores_de_esquema(ESQUEMA, "archivo_proyectos", datos, "proyectos.json")


@pytest.fixture(scope="module")
def catalogo():
    return cargar_catalogo()


@pytest.fixture(scope="module")
def publicados():
    """Tres proyectos publicados reales (válidos contra el esquema de salida)."""
    return json.loads((FIXTURES / "proyectos_publicados.json").read_text(encoding="utf-8"))["proyectos"]


def fuente_desde_fixture(clave="pub-0000aaaa", es_privado=False):
    texto = (FIXTURES / "portfolio" / "valido.md").read_text(encoding="utf-8")
    contexto = {"tipo": "repo", "es_privado": es_privado, "nombre_repo": "inventado", "creado": "2025-01-01T00:00:00Z"}
    datos = leer_archivo_estandar(texto, contexto)["datos"]
    return {
        "clave": clave,
        "origen": "repo",
        "es_privado": es_privado,
        "datos": datos,
        "url_repo": "https://github.com/dueno/inventado",
        "ultima_actividad": "2025-09",
        "imagen": None,
        "bitacora": [{"fecha": "2025-05-01", "titulo": "Entrada"}],
    }


def test_armado_valida_contra_el_esquema_de_salida(catalogo):
    proyecto, desconocidas = armar_proyecto(fuente_desde_fixture(), catalogo)
    assert errores_de_esquema([proyecto]) == []
    assert desconocidas == []
    assert proyecto["links"]["repo"] == "https://github.com/dueno/inventado"
    assert proyecto["tecnologias"][0] == {"nombre": "Python", "categoria": "lenguaje"}
    # Solo campos de la lista blanca (nada de captura_auto, visible, mostrar_bitacora, aprobada…).
    assert "captura_auto" not in proyecto and "visible" not in proyecto


def test_armado_privado_sin_link_al_repo(catalogo):
    proyecto, _ = armar_proyecto(fuente_desde_fixture("priv-0000bbbb", es_privado=True), catalogo)
    assert proyecto["links"]["repo"] is None
    assert errores_de_esquema([proyecto]) == []


def test_fixture_valida(publicados):
    assert len(publicados) == 3
    assert errores_de_esquema(publicados) == []


def anteriores_de(proyectos):
    anteriores = {}
    for proyecto in proyectos:
        anteriores[proyecto["clave"]] = proyecto
    return anteriores


def test_falla_de_un_repo_mantiene_su_version_anterior(publicados):
    anteriores = anteriores_de(publicados)
    actualizado = copy.deepcopy(publicados[1])
    actualizado["descripcion"]["es"] = "Descripción nueva."
    resultados = [
        {"clave": publicados[0]["clave"], "estado": "fallo", "tipo": "no_se_pudo_leer", "detalle": "HTTP 502", "nombre_publico": None},
        {"clave": publicados[1]["clave"], "estado": "ok", "proyecto": actualizado},
        {"clave": publicados[2]["clave"], "estado": "ok", "proyecto": publicados[2]},
    ]
    proyectos, advertencias = resolver_resultados(resultados, anteriores)
    assert proyectos[0] == publicados[0]  # idéntico a lo publicado (incluida su imagen)
    assert proyectos[1]["descripcion"]["es"] == "Descripción nueva."
    assert advertencias == [{
        "clave": publicados[0]["clave"],
        "nombre": None,
        "tipo": "no_se_pudo_leer",
        "detalle": "HTTP 502; se mantiene la versión anterior",
    }]


def test_falla_de_un_proyecto_nuevo_no_entra(publicados):
    resultados = [
        {"clave": "pub-nuevo000", "estado": "fallo", "tipo": "no_valida", "nombre_publico": "Nuevo"},
        {"clave": publicados[0]["clave"], "estado": "ok", "proyecto": publicados[0]},
        {"clave": publicados[1]["clave"], "estado": "ok", "proyecto": publicados[1]},
    ]
    proyectos, advertencias = resolver_resultados(resultados, {})
    assert len(proyectos) == 2
    assert advertencias[0]["detalle"] == "proyecto nuevo: no entra"


def test_mas_de_la_mitad_es_falla_total(publicados):
    resultados = [
        {"clave": "a", "estado": "fallo", "tipo": "timeout"},
        {"clave": "b", "estado": "fallo", "tipo": "timeout"},
        {"clave": publicados[0]["clave"], "estado": "ok", "proyecto": publicados[0]},
    ]
    with pytest.raises(ErrorFallaTotal):
        resolver_resultados(resultados, anteriores_de(publicados))
    # Exactamente la mitad no es falla total.
    resolver_resultados(resultados[1:], anteriores_de(publicados))


def test_choque_de_slug_revierte_al_que_lo_introdujo(publicados):
    anteriores = anteriores_de(publicados)
    cambiado = copy.deepcopy(publicados[1])
    cambiado["slug"] = publicados[0]["slug"]  # roba el slug de otro
    nuevo = copy.deepcopy(publicados[2])
    nuevo["clave"] = "pub-nuevo111"
    nuevo["slug"] = "otro"
    nuevo["slugs_anteriores"] = [publicados[2]["slug"]]  # choca con un slug actual
    proyectos, advertencias = resolver_slugs([publicados[0], cambiado, publicados[2], nuevo], anteriores, {"pub-nuevo111": "Nuevo"})
    assert proyectos == [publicados[0], publicados[1], publicados[2]]
    tipos = []
    for item in advertencias:
        tipos.append((item["clave"], item["tipo"], item["detalle"]))
    assert (publicados[1]["clave"], "slug_repetido", "se mantiene la versión anterior") in tipos
    assert ("pub-nuevo111", "slug_repetido", "proyecto nuevo: no entra") in tipos


def test_orden(publicados):
    a = copy.deepcopy(publicados[0])
    a.update({"clave": "x1", "slug": "a", "destacado": False, "estado": "terminado", "ultima_actividad": "2026-11"})
    b = copy.deepcopy(publicados[0])
    b.update({"clave": "x2", "slug": "b", "destacado": False, "estado": "activo", "ultima_actividad": "2025-01"})
    c = copy.deepcopy(publicados[0])
    c.update({"clave": "x3", "slug": "c", "destacado": True, "estado": "pausado", "ultima_actividad": "2024-01"})
    d = copy.deepcopy(publicados[0])
    d.update({"clave": "x4", "slug": "d", "destacado": False, "estado": "activo", "ultima_actividad": "2026-02"})
    orden = []
    for proyecto in ordenar([a, b, c, d]):
        orden.append(proyecto["slug"])
    assert orden == ["c", "d", "b", "a"]


def test_escritura_deterministica_byte_a_byte(publicados, tmp_path):
    ruta_a = tmp_path / "a.json"
    ruta_b = tmp_path / "b.json"
    assert escribir_proyectos(ordenar(publicados), ruta_a) is True
    assert escribir_proyectos(ordenar(list(reversed(publicados))), ruta_b) is True
    assert ruta_a.read_bytes() == ruta_b.read_bytes()
    assert b"\r\n" not in ruta_a.read_bytes()
    marca = ruta_a.stat().st_mtime_ns
    assert escribir_proyectos(ordenar(publicados), ruta_a) is False  # sin cambios → no se toca
    assert ruta_a.stat().st_mtime_ns == marca
    assert proyectos_anteriores(ruta_a)[publicados[0]["clave"]] == publicados[0]
    assert json.loads(ruta_a.read_text(encoding="utf-8"))["version"] == 1


def test_limpiar_imagenes_borra_solo_las_huerfanas(publicados, tmp_path):
    proyecto = copy.deepcopy(publicados[0])
    proyecto["imagen"] = {
        "origen": "auto",
        "alt": None,
        "ancho": 1200,
        "alto": 750,
        "archivos": {
            "es": {"1200": "/proyectos/x-es-1200.webp", "600": "/proyectos/x-es-600.webp"},
            "en": {"1200": "/proyectos/x-en-1200.webp", "600": "/proyectos/x-en-600.webp"},
        },
    }
    for nombre in ("x-es-1200.webp", "x-es-600.webp", "x-en-1200.webp", "x-en-600.webp", "x-1200.webp", "viejo-600.webp"):
        (tmp_path / nombre).write_bytes(b"w")
    assert limpiar_imagenes([proyecto], tmp_path) == ["viejo-600.webp", "x-1200.webp"]
    assert len(list(tmp_path.iterdir())) == 4
