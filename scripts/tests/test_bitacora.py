"""bitacora.py: solo encabezados → fecha + título; ningún texto del cuerpo en la salida (paso 25)."""

import json

import pytest

from portfolio.bitacora import leer_bitacora

from tests.utiles import FIXTURES


def leer(nombre, maximo=10):
    texto = (FIXTURES / "bitacoras" / nombre).read_text(encoding="utf-8")
    return leer_bitacora(texto, maximo)


def test_formato_unico_ordena_y_limpia_markdown():
    entradas = leer("unico.md")["entradas"]
    assert entradas == [
        {"fecha": "2026-02-03", "titulo": "Tercera entrada con link"},
        {"fecha": "2026-02-02", "titulo": "Segunda entrada"},
        {"fecha": "2026-02-01", "titulo": "Primera entrada"},
    ]


def test_max_entradas():
    assert len(leer("unico.md", 2)["entradas"]) == 2
    assert leer("unico.md", 2)["entradas"][0]["fecha"] == "2026-02-03"


def test_formato_a_sin_titulos_no_publica_y_advierte():
    resultado = leer("formato_a.md")
    assert resultado["entradas"] == []
    assert resultado["advertencias"] == ["bitacora_sin_titulos"]
    assert resultado["con_fecha"] == 2


def test_formato_b_ignora_titulos_sin_fecha_y_recorta():
    entradas = leer("formato_b.md")["entradas"]
    assert [entrada["fecha"] for entrada in entradas] == ["2026-11-15", "2026-11-14"]
    assert len(entradas[0]["titulo"]) == 100
    assert entradas[0]["titulo"].endswith("…")


def test_formato_c_descarta_fechas_imposibles_y_nivel_4():
    assert leer("formato_c.md")["entradas"] == [{"fecha": "2026-11-04", "titulo": "Armado inicial"}]


@pytest.mark.parametrize("nombre", ["unico.md", "formato_a.md", "formato_b.md", "formato_c.md"])
def test_ningun_texto_del_cuerpo_en_la_salida(nombre):
    salida = json.dumps(leer(nombre), ensure_ascii=False)
    assert "CUERPO" not in salida
    assert "ghp_" not in salida
    assert "privado.ejemplo.test" not in salida
    assert "USD" not in salida
