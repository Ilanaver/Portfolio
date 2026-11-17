"""Capturas manuales (§2.4) y procesamiento común de imágenes (también lo usa capturas_auto).

Reglas:
- Tipo real por los bytes iniciales (no por la extensión): PNG, JPEG o WebP. ≤ 5 MB. Ancho ≥ 800 px.
- Repos privados: solo se publica si `imagen.aprobada` == primeros 12 caracteres del SHA-256 del archivo.
- Se eliminan TODOS los metadatos (EXIF, GPS, ICC, XMP): se copian solo los píxeles a una imagen nueva.
- WebP de 1200 y 600 px de ancho en public/proyectos/<slug>-1200.webp / -600.webp (o <slug>-es-… / -en-…).
- Sin reproceso si el origen no cambió: la huella del origen se guarda en src/datos/huellas.json.
"""

import hashlib
import io

from PIL import Image, ImageOps

BYTES_MAXIMOS = 5 * 1024 * 1024
ANCHO_MINIMO = 800
ANCHOS = (1200, 600)
CALIDAD_WEBP = 82
CARPETA_PUBLICA = "/proyectos/"


class ErrorImagen(Exception):
    """tipo: imagen_invalida | imagen_sin_aprobar. Sin texto del repo."""

    def __init__(self, tipo, motivo):
        super().__init__(tipo)
        self.tipo = tipo
        self.motivo = motivo  # motivo genérico (no cita al repo): 'tamaño', 'formato', 'ancho', 'hash'


def hash_corto(contenido):
    return hashlib.sha256(contenido).hexdigest()[:12]


def tipo_real(contenido):
    if contenido.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if contenido.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if len(contenido) >= 12 and contenido[0:4] == b"RIFF" and contenido[8:12] == b"WEBP":
        return "webp"
    return None


def abrir_imagen(contenido):
    """Valida tamaño, tipo real y ancho. Devuelve la imagen de Pillow ya orientada según su EXIF."""
    if len(contenido) > BYTES_MAXIMOS:
        raise ErrorImagen("imagen_invalida", "tamaño")
    if tipo_real(contenido) is None:
        raise ErrorImagen("imagen_invalida", "formato")
    try:
        imagen = Image.open(io.BytesIO(contenido))
        imagen.load()
    except Exception:
        raise ErrorImagen("imagen_invalida", "formato") from None
    imagen = ImageOps.exif_transpose(imagen)
    if imagen.width < ANCHO_MINIMO:
        raise ErrorImagen("imagen_invalida", "ancho")
    return imagen


def tiene_transparencia(imagen):
    if imagen.mode in ("RGBA", "LA", "PA"):
        return True
    return imagen.mode == "P" and "transparency" in imagen.info


def solo_pixeles(imagen):
    """Imagen nueva con los mismos píxeles y sin ningún metadato."""
    modo = "RGBA" if tiene_transparencia(imagen) else "RGB"
    convertida = imagen.convert(modo)
    limpia = Image.new(modo, convertida.size)
    limpia.paste(convertida)
    return limpia


def redimensionar(imagen, ancho):
    """Achica al ancho pedido manteniendo la proporción. Nunca agranda."""
    if imagen.width <= ancho:
        return imagen.copy()
    alto = round(imagen.height * ancho / imagen.width)
    return imagen.resize((ancho, alto), Image.Resampling.LANCZOS)


def webp_en_bytes(imagen):
    salida = io.BytesIO()
    imagen.save(salida, format="WEBP", quality=CALIDAD_WEBP, method=6)
    return salida.getvalue()


def nombre_base(slug, idioma=None):
    if idioma is None:
        return slug
    return slug + "-" + idioma


def rutas_publicas(base):
    return {"1200": CARPETA_PUBLICA + base + "-1200.webp", "600": CARPETA_PUBLICA + base + "-600.webp"}


def guardar_variantes(imagen, carpeta_destino, base):
    """Escribe <base>-1200.webp y <base>-600.webp sin metadatos. Devuelve (ancho, alto) de la de 1200."""
    carpeta_destino.mkdir(parents=True, exist_ok=True)
    limpia = solo_pixeles(imagen)
    medida_1200 = None
    for ancho in ANCHOS:
        variante = redimensionar(limpia, ancho)
        (carpeta_destino / (base + "-" + str(ancho) + ".webp")).write_bytes(webp_en_bytes(variante))
        if ancho == ANCHOS[0]:
            medida_1200 = variante.size
    return medida_1200


def existen_variantes(carpeta_destino, base):
    for ancho in ANCHOS:
        if not (carpeta_destino / (base + "-" + str(ancho) + ".webp")).exists():
            return False
    return True


def medida_publicada(carpeta_destino, base):
    with Image.open(carpeta_destino / (base + "-1200.webp")) as imagen:
        return imagen.size


def imagen_para_salida(origen, alt, medida, base_es, base_en):
    """Objeto `imagen` del esquema de salida. Si hay una sola imagen, es y en apuntan a los mismos archivos."""
    return {
        "origen": origen,
        "alt": alt,
        "ancho": medida[0],
        "alto": medida[1],
        "archivos": {"es": rutas_publicas(base_es), "en": rutas_publicas(base_en)},
    }


def procesar_imagen_manual(contenido, slug, es_privado, aprobada, alt, huella_anterior, carpeta_destino):
    """Procesa una captura manual. Devuelve (imagen para la salida, huella del origen, reprocesada: bool).

    Lanza ErrorImagen si no es válida o si es de un repo privado y el hash no coincide con `aprobada`.
    """
    huella = hash_corto(contenido)
    if es_privado and aprobada != huella:
        raise ErrorImagen("imagen_sin_aprobar", "hash")
    if huella == huella_anterior and existen_variantes(carpeta_destino, slug):
        medida = medida_publicada(carpeta_destino, slug)
        return imagen_para_salida("manual", alt, medida, slug, slug), huella, False
    imagen = abrir_imagen(contenido)
    medida = guardar_variantes(imagen, carpeta_destino, slug)
    return imagen_para_salida("manual", alt, medida, slug, slug), huella, True
