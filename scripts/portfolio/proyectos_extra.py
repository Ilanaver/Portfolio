"""Proyectos sin repo (P2, §2.5): config/proyectos_extra/<slug>.md, mismo formato que PORTFOLIO.md.

Diferencias con un repo: slug, fecha_inicio y ultima_actividad obligatorios; sin link a repo ni bitácora;
la imagen manual vive en config/proyectos_extra/imagenes/. Son públicos (están en el repo del portfolio).
El nombre del archivo tiene que ser el slug: así la clave `extra-<slug>` es estable.
"""

import datetime

from portfolio import CARPETA_CONFIG
from portfolio.archivo_estandar import ErrorArchivoEstandar, leer_archivo_estandar
from portfolio.identidad import clave_extra

CARPETA_EXTRAS = CARPETA_CONFIG / "proyectos_extra"
MESES_SIN_ACTIVIDAD = 6

CONTEXTO_EXTRA = {"tipo": "extra", "es_privado": False, "nombre_repo": None, "creado": None}


def listar_archivos(carpeta=CARPETA_EXTRAS):
    """Rutas de los .md de proyectos extra, en orden alfabético (la carpeta puede no existir)."""
    if not carpeta.exists():
        return []
    rutas = []
    for ruta in carpeta.glob("*.md"):
        if ruta.is_file():
            rutas.append(ruta)
    rutas.sort()
    return rutas


def leer_extra(ruta):
    """Devuelve {"clave", "nombre_archivo", "datos", "advertencias", "carpeta"}. Lanza ErrorArchivoEstandar."""
    try:
        texto = ruta.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        raise ErrorArchivoEstandar("no_se_pudo_leer", ["no se pudo leer el archivo como UTF-8"]) from None
    resultado = leer_archivo_estandar(texto, CONTEXTO_EXTRA)
    datos = resultado["datos"]
    if datos["slug"] != ruta.stem:
        raise ErrorArchivoEstandar(
            "no_valida", ["el archivo se llama '" + ruta.name + "' pero el slug es '" + datos["slug"] + "'"]
        )
    return {
        "clave": clave_extra(datos["slug"]),
        "nombre_archivo": ruta.name,
        "datos": datos,
        "advertencias": resultado["advertencias"],
        "carpeta": ruta.parent,
    }


def leer_imagen_extra(extra):
    """Bytes de la captura manual de un proyecto extra (ruta relativa a su carpeta, dentro de imagenes/)."""
    imagen = extra["datos"]["imagen"]
    ruta = (extra["carpeta"] / imagen["archivo"]).resolve()
    carpeta_imagenes = (extra["carpeta"] / "imagenes").resolve()
    if carpeta_imagenes not in ruta.parents:
        raise ErrorArchivoEstandar("imagen_invalida", ["la imagen tiene que estar dentro de imagenes/"])
    if not ruta.exists():
        raise ErrorArchivoEstandar("imagen_invalida", ["no existe la imagen"])
    return ruta.read_bytes()


def meses_entre(mes_aaaa_mm, hoy):
    anio, mes = mes_aaaa_mm.split("-")
    return (hoy.year - int(anio)) * 12 + (hoy.month - int(mes))


def esta_desactualizado(datos, hoy=None):
    """§2.5: un extra 'activo' con ultima_actividad de hace más de 6 meses (lo avisa auditar_repos.py)."""
    if hoy is None:
        hoy = datetime.date.today()
    if datos["estado"] != "activo":
        return False
    return meses_entre(datos["ultima_actividad"], hoy) > MESES_SIN_ACTIVIDAD
