"""Capturas automáticas desde la demo pública con Playwright (§2.4).

- Ventana 1280×800, escala 1; red quieta + 2 s; tope 30 s (config/capturas.yml).
- Dos capturas: navegador en es-AR y en en-US (locale + Accept-Language). Si no se ven distintas, se guarda
  una sola imagen para los dos idiomas.
- HTTP ≥ 400, redirección a otro dominio o tope superado → ErrorCaptura: no se reemplaza nada.
- Solo se reemplaza lo publicado si cambió de forma visible (comparación de píxeles con tolerancia).
- Mismo procesamiento que las manuales: WebP 1200/600 sin metadatos.
Los errores salen por tipo, nunca con el texto de Playwright (incluye la URL).
"""

import io
import subprocess
import sys
from contextlib import contextmanager
from urllib.parse import urlsplit

import yaml
from PIL import Image, ImageChops

from portfolio import CARPETA_CONFIG
from portfolio.imagenes import guardar_variantes, imagen_para_salida, medida_publicada

RUTA_CONFIG = CARPETA_CONFIG / "capturas.yml"
IDIOMAS = ("es", "en")


class ErrorCaptura(Exception):
    """tipo siempre 'captura_auto_fallida'; motivo: http | redireccion | timeout | navegador."""

    def __init__(self, motivo, codigo=None):
        super().__init__("captura_auto_fallida")
        self.tipo = "captura_auto_fallida"
        self.motivo = motivo
        self.codigo = codigo

    def descripcion(self):
        if self.codigo is not None:
            return self.tipo + " (HTTP " + str(self.codigo) + ")"
        return self.tipo + " (" + self.motivo + ")"


def cargar_config(ruta=RUTA_CONFIG):
    with open(ruta, encoding="utf-8") as archivo:
        return yaml.safe_load(archivo)


# ------------------------------------------------------------------ navegador


def instalar_chromium():
    """`playwright install chromium` (con dependencias del sistema en Linux, como en el runner de Actions)."""
    comando = [sys.executable, "-m", "playwright", "install"]
    if sys.platform.startswith("linux"):
        comando.append("--with-deps")
    comando.append("chromium")
    subprocess.run(comando, check=True, capture_output=True)


def lanzar_chromium(playwright):
    """Lanza Chromium; si no está instalado, lo instala una vez y reintenta. Así el Action solo lo descarga
    en las corridas que sacan capturas o generan el PDF (§4.2)."""
    from playwright.sync_api import Error as ErrorPlaywright

    try:
        return playwright.chromium.launch()
    except ErrorPlaywright as error:
        if "Executable doesn't exist" not in str(error):
            raise
    instalar_chromium()
    return playwright.chromium.launch()


@contextmanager
def abrir_navegador():
    """Chromium headless de Playwright. Se importa acá para que el resto del paquete no dependa de él."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        navegador = lanzar_chromium(playwright)
        try:
            yield navegador
        finally:
            navegador.close()


def host_sin_www(url):
    host = (urlsplit(url).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def mismo_sitio(url_original, url_final):
    return host_sin_www(url_original) == host_sin_www(url_final)


def sacar_captura(navegador, url, locale, config):
    """PNG de la ventana visible. Lanza ErrorCaptura si la página falla, redirige afuera o tarda de más."""
    from playwright.sync_api import Error as ErrorPlaywright
    from playwright.sync_api import TimeoutError as TiempoAgotado

    contexto = navegador.new_context(
        viewport={"width": config["ventana"]["ancho"], "height": config["ventana"]["alto"]},
        device_scale_factor=config["escala"],
        locale=locale,
        extra_http_headers={"Accept-Language": locale + "," + locale.split("-")[0] + ";q=0.9"},
        color_scheme="light",
        reduced_motion="reduce",
    )
    try:
        pagina = contexto.new_page()
        try:
            respuesta = pagina.goto(url, wait_until="networkidle", timeout=config["tope_ms"])
        except TiempoAgotado:
            raise ErrorCaptura("timeout") from None
        except ErrorPlaywright:
            raise ErrorCaptura("navegador") from None
        if respuesta is None:
            raise ErrorCaptura("navegador")
        if respuesta.status >= 400:
            raise ErrorCaptura("http", respuesta.status)
        if not mismo_sitio(url, pagina.url):
            raise ErrorCaptura("redireccion")
        pagina.wait_for_timeout(config["espera_extra_ms"])
        try:
            return pagina.screenshot(type="png", animations="disabled")
        except ErrorPlaywright:
            raise ErrorCaptura("navegador") from None
    finally:
        contexto.close()


# ------------------------------------------------------------------ comparación


def reducida_en_grises(contenido, ancho):
    with Image.open(io.BytesIO(contenido)) as imagen:
        gris = imagen.convert("L")
    alto = max(1, round(gris.height * ancho / gris.width))
    return gris.resize((ancho, alto), Image.Resampling.BILINEAR)


def porcentaje_distinto(contenido_a, contenido_b, config):
    """% de píxeles con diferencia > umbral_nivel, con las dos imágenes reducidas en grises."""
    comparacion = config["comparacion"]
    a = reducida_en_grises(contenido_a, comparacion["ancho"])
    b = reducida_en_grises(contenido_b, comparacion["ancho"])
    if a.size != b.size:
        return 100.0
    diferencia = ImageChops.difference(a, b)
    histograma = diferencia.histogram()
    distintos = 0
    for nivel in range(comparacion["umbral_nivel"] + 1, 256):
        distintos += histograma[nivel]
    return 100.0 * distintos / (a.width * a.height)


def cambio_visible(contenido_a, contenido_b, config):
    return porcentaje_distinto(contenido_a, contenido_b, config) > config["comparacion"]["porcentaje_cambio"]


# ------------------------------------------------------------------ archivos publicados


def base_desde_ruta(ruta):
    """'/proyectos/mi-app-es-1200.webp' → 'mi-app-es'."""
    nombre = ruta.rsplit("/", 1)[-1]
    return nombre[: -len("-1200.webp")]


def bases_anteriores(imagen_anterior):
    """{idioma: base} de una captura automática publicada, o None si no había (o era manual)."""
    if not imagen_anterior or imagen_anterior.get("origen") != "auto":
        return None
    bases = {}
    for idioma in IDIOMAS:
        bases[idioma] = base_desde_ruta(imagen_anterior["archivos"][idioma]["1200"])
    return bases


def bytes_publicados(carpeta, base):
    ruta = carpeta / (base + "-1200.webp")
    if not ruta.exists():
        return None
    return ruta.read_bytes()


def bases_nuevas(slug, distintas):
    if distintas:
        return {"es": slug + "-es", "en": slug + "-en"}
    return {"es": slug, "en": slug}


# ------------------------------------------------------------------ proyecto


def capturar_proyecto(navegador, slug, url, imagen_anterior, carpeta, config):
    """Saca las capturas ES/EN y decide qué publicar. Devuelve (imagen para la salida, hubo_cambio).

    Lanza ErrorCaptura si alguna de las dos capturas falla (el que llama conserva la anterior).
    """
    capturas = {}
    for idioma in IDIOMAS:
        capturas[idioma] = sacar_captura(navegador, url, config["idiomas"][idioma], config)
    distintas = cambio_visible(capturas["es"], capturas["en"], config)
    bases = bases_nuevas(slug, distintas)
    anteriores = bases_anteriores(imagen_anterior)

    hubo_cambio = anteriores != bases
    escritas = set()
    for idioma in IDIOMAS:
        base = bases[idioma]
        if base in escritas:
            continue
        escritas.add(base)
        publicado = bytes_publicados(carpeta, base) if anteriores == bases else None
        if publicado is not None and not cambio_visible(capturas[idioma], publicado, config):
            continue
        with Image.open(io.BytesIO(capturas[idioma])) as imagen:
            guardar_variantes(imagen, carpeta, base)
        hubo_cambio = True

    if not hubo_cambio:
        return imagen_anterior, False
    medida = medida_publicada(carpeta, bases["es"])
    return imagen_para_salida("auto", None, medida, bases["es"], bases["en"]), True
