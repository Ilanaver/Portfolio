"""etiquetas.py + config/etiquetas.yml (paso 26)."""

import json

import pytest

from portfolio import CARPETA_DATOS
from portfolio.etiquetas import ErrorCatalogo, cargar_catalogo, normalizar_lista


@pytest.fixture(scope="module")
def catalogo():
    return cargar_catalogo()


def test_alias_y_mayusculas(catalogo):
    etiquetas, desconocidas = normalizar_lista(["python3", "NEON  postgres", "workers", "Python"], catalogo)
    assert etiquetas == [
        {"nombre": "Python", "categoria": "lenguaje"},
        {"nombre": "Neon", "categoria": "datos"},
        {"nombre": "Cloudflare Workers", "categoria": "infra"},
    ]
    assert desconocidas == []


def test_fuera_de_catalogo_se_publica_tal_cual(catalogo):
    etiquetas, desconocidas = normalizar_lista(["Cosa  Rara"], catalogo)
    assert etiquetas == [{"nombre": "Cosa Rara", "categoria": None}]
    assert desconocidas == ["Cosa Rara"]


def test_las_etiquetas_publicadas_estan_en_el_catalogo(catalogo):
    with open(CARPETA_DATOS / "proyectos.json", encoding="utf-8") as archivo:
        proyectos = json.load(archivo)["proyectos"]
    for proyecto in proyectos:
        for etiqueta in proyecto["tecnologias"] + proyecto["servicios"]:
            normalizada, _ = normalizar_lista([etiqueta["nombre"]], catalogo)
            assert normalizada[0] == etiqueta


def test_catalogo_con_alias_repetido_falla(tmp_path):
    ruta = tmp_path / "etiquetas.yml"
    ruta.write_text("A: {categoria: datos, alias: [x]}\nB: {categoria: datos, alias: [X]}\n", encoding="utf-8")
    with pytest.raises(ErrorCatalogo):
        cargar_catalogo(ruta)


def test_catalogo_con_categoria_invalida_falla(tmp_path):
    ruta = tmp_path / "etiquetas.yml"
    ruta.write_text("A: {categoria: cualquiera}\n", encoding="utf-8")
    with pytest.raises(ErrorCatalogo):
        cargar_catalogo(ruta)
