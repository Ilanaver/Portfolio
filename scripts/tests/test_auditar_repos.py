"""auditar_repos.py sin red: filas de repos y extras con `gh` simulado (paso 37)."""

import auditar_repos
from portfolio.imagenes import hash_corto

from tests.utiles import FIXTURES

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100


def repo(privado, texto):
    return {"id": "R_x", "nombre": "repo-x", "dueno": "dueno", "es_privado": privado, "creado": "2025-01-01T00:00:00Z", "portfolio_md": texto}


def test_repo_sin_archivo():
    fila = auditar_repos.fila_de_repo(repo(True, None))
    assert fila["clave"].startswith("priv-") and fila["archivo"] == "no"


def test_privado_con_imagen_que_cambio(monkeypatch):
    monkeypatch.setattr(auditar_repos, "descargar_archivo", lambda r, ruta: PNG)
    texto = (FIXTURES / "portfolio" / "valido.md").read_text(encoding="utf-8")
    fila = auditar_repos.fila_de_repo(repo(True, texto))
    assert fila["estado"] == "visible"
    assert "imagen: CAMBIÓ: aprobada 0123456789ab, actual " + hash_corto(PNG) in fila["detalles"]
    aprobado = texto.replace("aprobada: 0123456789ab", "aprobada: " + hash_corto(PNG))
    assert "imagen: aprobada" in auditar_repos.fila_de_repo(repo(True, aprobado))["detalles"]
    sin_aprobar = texto.replace("aprobada: 0123456789ab", "aprobada: null")
    assert "imagen: SIN APROBAR (" + hash_corto(PNG) + ")" in auditar_repos.fila_de_repo(repo(True, sin_aprobar))["detalles"]


def test_repo_que_no_valida_muestra_el_detalle():
    fila = auditar_repos.fila_de_repo(repo(False, "---\nversion: 2\n---\n"))
    assert fila["estado"] == "NO VALIDA" and fila["detalles"]


def test_inglés_faltante_como_advertencia():
    texto = (FIXTURES / "portfolio" / "sin_ingles.md").read_text(encoding="utf-8")
    fila = auditar_repos.fila_de_repo(repo(False, texto))
    assert "falta_ingles:descripcion_en" in fila["detalles"]


def test_extras():
    valido = auditar_repos.fila_de_extra(FIXTURES / "extras" / "automatizacion-inventada.md")
    assert valido["clave"] == "extra-automatizacion-inventada" and valido["estado"] == "visible"
    roto = auditar_repos.fila_de_extra(FIXTURES / "extras" / "nombre-equivocado.md")
    assert roto["estado"] == "NO VALIDA"
