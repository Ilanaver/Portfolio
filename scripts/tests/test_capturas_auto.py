"""capturas_auto.py contra páginas HTML locales (paso 30).

Casos: página fija → sin cambio; cambio chico invisible → sin cambio; cambio visible → reemplazo;
página bilingüe → dos imágenes; HTTP 500 → error (se mantiene la anterior); redirección a otro dominio → error.
Necesita Chromium de Playwright (`python -X utf8 -m playwright install chromium`); si no está, se saltean.
"""

import copy
import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pytest

from portfolio.capturas_auto import (
    ErrorCaptura,
    abrir_navegador,
    capturar_proyecto,
    cargar_config,
    mismo_sitio,
)

from tests.utiles import FIXTURES


class Manejador(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/500":
            self.send_error(500)
            return
        if self.path == "/afuera":
            self.send_response(302)
            self.send_header("Location", "http://localhost:" + str(self.server.server_port) + "/fija.html")
            self.end_headers()
            return
        super().do_GET()

    def log_message(self, *argumentos):
        pass


@pytest.fixture(scope="module")
def servidor():
    manejador = functools.partial(Manejador, directory=str(FIXTURES / "paginas"))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), manejador)
    hilo = threading.Thread(target=httpd.serve_forever, daemon=True)
    hilo.start()
    yield "http://127.0.0.1:" + str(httpd.server_port)
    httpd.shutdown()


@pytest.fixture(scope="module")
def navegador():
    try:
        with abrir_navegador() as abierto:
            yield abierto
    except Exception as error:  # Chromium no instalado
        if "Executable doesn't exist" in str(error):
            pytest.skip("Chromium de Playwright no está instalado")
        raise


@pytest.fixture(scope="module")
def config():
    datos = copy.deepcopy(cargar_config())
    datos["espera_extra_ms"] = 200
    datos["tope_ms"] = 15000
    return datos


def test_mismo_sitio():
    assert mismo_sitio("https://ejemplo.test/a", "https://www.ejemplo.test/b")
    assert not mismo_sitio("https://ejemplo.test/", "https://otro.test/")


def test_fija_chica_visible(servidor, navegador, config, tmp_path):
    imagen, cambio = capturar_proyecto(navegador, "app", servidor + "/fija.html", None, tmp_path, config)
    assert cambio is True
    assert imagen["origen"] == "auto" and imagen["alt"] is None
    assert imagen["archivos"]["es"] == imagen["archivos"]["en"]
    assert imagen["archivos"]["es"]["1200"] == "/proyectos/app-1200.webp"
    assert (imagen["ancho"], imagen["alto"]) == (1200, 750)
    publicado = (tmp_path / "app-1200.webp").read_bytes()

    # Misma página otra vez → sin cambio, sin escribir.
    misma, cambio = capturar_proyecto(navegador, "app", servidor + "/fija.html", imagen, tmp_path, config)
    assert cambio is False and misma is imagen
    assert (tmp_path / "app-1200.webp").read_bytes() == publicado

    # Cambio chico (un dígito en el pie) → por debajo de la tolerancia.
    _, cambio = capturar_proyecto(navegador, "app", servidor + "/chica.html", imagen, tmp_path, config)
    assert cambio is False
    assert (tmp_path / "app-1200.webp").read_bytes() == publicado

    # Cambio visible → se reemplaza.
    nueva, cambio = capturar_proyecto(navegador, "app", servidor + "/visible.html", imagen, tmp_path, config)
    assert cambio is True
    assert (tmp_path / "app-1200.webp").read_bytes() != publicado
    assert nueva["archivos"] == imagen["archivos"]


def test_bilingue_da_dos_imagenes(servidor, navegador, config, tmp_path):
    imagen, cambio = capturar_proyecto(navegador, "bi", servidor + "/bilingue.html", None, tmp_path, config)
    assert cambio is True
    assert imagen["archivos"]["es"]["1200"] == "/proyectos/bi-es-1200.webp"
    assert imagen["archivos"]["en"]["1200"] == "/proyectos/bi-en-1200.webp"
    for nombre in ("bi-es-1200.webp", "bi-es-600.webp", "bi-en-1200.webp", "bi-en-600.webp"):
        assert (tmp_path / nombre).exists()
    _, cambio = capturar_proyecto(navegador, "bi", servidor + "/bilingue.html", imagen, tmp_path, config)
    assert cambio is False


def test_http_500_no_reemplaza(servidor, navegador, config, tmp_path):
    with pytest.raises(ErrorCaptura) as error:
        capturar_proyecto(navegador, "app", servidor + "/500", None, tmp_path, config)
    assert error.value.motivo == "http" and error.value.codigo == 500
    assert error.value.descripcion() == "captura_auto_fallida (HTTP 500)"
    assert "127.0.0.1" not in str(error.value)
    assert list(tmp_path.iterdir()) == []


def test_redireccion_a_otro_dominio_no_reemplaza(servidor, navegador, config, tmp_path):
    with pytest.raises(ErrorCaptura) as error:
        capturar_proyecto(navegador, "app", servidor + "/afuera", None, tmp_path, config)
    assert error.value.motivo == "redireccion"
    assert list(tmp_path.iterdir()) == []


def test_sitio_caido_es_error_por_tipo(navegador, config, tmp_path):
    with pytest.raises(ErrorCaptura) as error:
        capturar_proyecto(navegador, "app", "http://127.0.0.1:9/", None, tmp_path, config)
    assert error.value.motivo == "navegador"
