"""Prueba mínima: el paquete se importa y las rutas apuntan al repo."""

from portfolio import CARPETA_CONFIG, RAIZ


def test_raiz_es_el_repo():
    assert (RAIZ / "package.json").exists()
    assert (CARPETA_CONFIG / "esquema_salida.json").exists()
