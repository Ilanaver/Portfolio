"""config/perfil.yml → src/datos/perfil.json (+ `version` y `cv_pdf`)."""

import yaml

from portfolio import CARPETA_CONFIG, CARPETA_DATOS, CARPETA_PUBLIC
from portfolio.archivo_estandar import CargadorSinFechas
from portfolio.salida import escribir_si_cambio, json_estable

RUTA_PERFIL_YML = CARPETA_CONFIG / "perfil.yml"
RUTA_PERFIL_JSON = CARPETA_DATOS / "perfil.json"
CARPETA_CV = CARPETA_PUBLIC / "cv"
CV_PDF = {"es": "/cv/cv-es.pdf", "en": "/cv/cv-en.pdf"}


def cv_pdf_disponible(carpeta_cv=CARPETA_CV):
    """`cv_pdf` solo si existen los dos PDF (los genera generar_cv.py); si no, el botón imprime."""
    for idioma in ("es", "en"):
        if not (carpeta_cv / ("cv-" + idioma + ".pdf")).exists():
            return None
    return dict(CV_PDF)


def armar_perfil(ruta_yml=RUTA_PERFIL_YML, carpeta_cv=CARPETA_CV):
    with open(ruta_yml, encoding="utf-8") as archivo:
        datos = yaml.load(archivo, Loader=CargadorSinFechas)
    perfil = dict(datos)
    perfil["version"] = 1
    perfil["cv_pdf"] = cv_pdf_disponible(carpeta_cv)
    return perfil


def escribir_perfil(perfil, ruta=RUTA_PERFIL_JSON):
    return escribir_si_cambio(ruta, json_estable(perfil))
