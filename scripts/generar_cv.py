"""CV en PDF (P4, §4.2 paso 3): /cv/cv-es.pdf y /cv/cv-en.pdf con la hoja de impresión del sitio.

1. Huella: SHA-256 de todo lo que afecta al CV (src/**, es/, en/, index.html, plugins/**, package-lock.json).
   Si coincide con public/cv/huella.txt, no hace nada.
2. Si cambió: `npm run build`, sirve dist/ en un servidor HTTP local, abre /es/ y /en/ con Playwright y
   genera los PDF A4; actualiza `cv_pdf` en src/datos/perfil.json y después huella.txt.
3. Si falla: se conservan los PDF anteriores, se avisa (::warning:: + advertencia en el estado) y sale con 0:
   el resto de los datos se publica igual.

Modo "CV propio": si existen config/cv/cv-es.pdf y config/cv/cv-en.pdf (los CV que arma Ilán aparte), no se
genera nada: se copian tal cual (mismos bytes, sin tocar metadatos) a public/cv/, se completa `cv_pdf` y se borra
huella.txt (no aplica). Pasa en los dos modos de uso, así el workflow no instala Node ni Chromium para el CV.

Uso:
  python -X utf8 scripts/generar_cv.py --chequear     → imprime y escribe en GITHUB_OUTPUT regenerar=true|false
  python -X utf8 scripts/generar_cv.py [--estado RUTA] [--carpeta-cv RUTA] [--sin-build]
"""

import argparse
import functools
import hashlib
import json
import os
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from portfolio import CARPETA_CONFIG, RAIZ
from portfolio.capturas_auto import abrir_navegador
from portfolio.identidad import imprimir, instalar_gancho_de_excepciones
from portfolio.perfil import CARPETA_CV, CV_PDF, RUTA_PERFIL_JSON
from portfolio.salida import escribir_si_cambio, json_estable

ORIGENES_DE_LA_HUELLA = ["src", "es", "en", "index.html", "plugins", "package-lock.json"]
# No afectan al CV: las huellas de capturas manuales cambian sin cambiar nada impreso.
EXCLUIDOS_DE_LA_HUELLA = {"src/datos/huellas.json"}
IDIOMAS = ("es", "en")
TOPE_MS = 30000
CARPETA_CV_PROPIO = CARPETA_CONFIG / "cv"


# ------------------------------------------------------------------ CV propio


def archivos_cv_propio(carpeta_origen):
    """{idioma: ruta} si están los dos PDF propios; None si no hay ninguno. Con uno solo, avisa y no los usa."""
    encontrados = {}
    for idioma in IDIOMAS:
        ruta = carpeta_origen / ("cv-" + idioma + ".pdf")
        if ruta.exists():
            encontrados[idioma] = ruta
    if len(encontrados) == len(IDIOMAS):
        return encontrados
    if encontrados:
        imprimir("::warning::Hay un solo CV propio en config/cv/ (faltan los dos idiomas): se sigue generando el CV")
    return None


def copiar_cv_propio(origenes, carpeta_cv, ruta_perfil):
    """Copia byte a byte los PDF propios (solo si cambiaron) y deja `cv_pdf` en el perfil. Devuelve True si copió."""
    carpeta_cv.mkdir(parents=True, exist_ok=True)
    copio = False
    for idioma in IDIOMAS:
        contenido = origenes[idioma].read_bytes()
        destino = carpeta_cv / ("cv-" + idioma + ".pdf")
        if destino.exists() and destino.read_bytes() == contenido:
            continue
        destino.write_bytes(contenido)
        copio = True
    huella = carpeta_cv / "huella.txt"
    if huella.exists():
        huella.unlink()
    if ruta_perfil.exists():
        actualizar_perfil(ruta_perfil)
    return copio


# ------------------------------------------------------------------ huella


def archivos_de_la_huella(raiz=RAIZ):
    """Rutas relativas (con '/') de los archivos que afectan al CV, en orden."""
    rutas = []
    for origen in ORIGENES_DE_LA_HUELLA:
        ruta = raiz / origen
        if ruta.is_file():
            rutas.append(origen)
            continue
        if not ruta.is_dir():
            continue
        for archivo in ruta.rglob("*"):
            if archivo.is_file():
                relativa = archivo.relative_to(raiz).as_posix()
                if relativa not in EXCLUIDOS_DE_LA_HUELLA:
                    rutas.append(relativa)
    rutas.sort()
    return rutas


def calcular_huella(raiz=RAIZ):
    """SHA-256 de (ruta + contenido) de cada archivo. Los finales de línea se normalizan a LF."""
    resumen = hashlib.sha256()
    for relativa in archivos_de_la_huella(raiz):
        contenido = (raiz / relativa).read_bytes().replace(b"\r\n", b"\n")
        resumen.update(relativa.encode("utf-8") + b"\0")
        resumen.update(hashlib.sha256(contenido).digest())
    return resumen.hexdigest()


def huella_guardada(carpeta_cv):
    ruta = carpeta_cv / "huella.txt"
    if not ruta.exists():
        return None
    return ruta.read_text(encoding="utf-8").strip()


def pdfs_presentes(carpeta_cv):
    for idioma in IDIOMAS:
        if not (carpeta_cv / ("cv-" + idioma + ".pdf")).exists():
            return False
    return True


def hay_que_regenerar(carpeta_cv, raiz=RAIZ):
    return not pdfs_presentes(carpeta_cv) or huella_guardada(carpeta_cv) != calcular_huella(raiz)


# ------------------------------------------------------------------ build, servidor y PDF


def correr_build():
    comando = "npm.cmd" if os.name == "nt" else "npm"
    proceso = subprocess.run([comando, "run", "build"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
    if proceso.returncode != 0:
        imprimir(proceso.stdout[-3000:])
        imprimir(proceso.stderr[-3000:])
        raise RuntimeError("build")


class ManejadorSilencioso(SimpleHTTPRequestHandler):
    def log_message(self, *argumentos):
        pass


def iniciar_servidor(carpeta):
    manejador = functools.partial(ManejadorSilencioso, directory=str(carpeta))
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), manejador)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    return servidor


def imprimir_pdf(navegador, url, destino):
    contexto = navegador.new_context(locale="es-AR" if "/es/" in url else "en-US")
    try:
        pagina = contexto.new_page()
        respuesta = pagina.goto(url, wait_until="networkidle", timeout=TOPE_MS)
        if respuesta is None or respuesta.status >= 400:
            raise RuntimeError("pagina")
        pagina.evaluate("document.fonts.ready")
        pagina.pdf(path=str(destino), format="A4", prefer_css_page_size=True, print_background=False)
    finally:
        contexto.close()


def contar_paginas(ruta):
    """Cantidad aproximada de páginas (objetos /Type /Page) para el log."""
    return ruta.read_bytes().count(b"/Type /Page") - ruta.read_bytes().count(b"/Type /Pages")


def generar_pdfs(carpeta_dist, carpeta_cv):
    """Genera los PDF en archivos temporales y recién al final reemplaza los publicados."""
    carpeta_cv.mkdir(parents=True, exist_ok=True)
    servidor = iniciar_servidor(carpeta_dist)
    base = "http://127.0.0.1:" + str(servidor.server_port)
    temporales = {}
    try:
        with abrir_navegador() as navegador:
            for idioma in IDIOMAS:
                temporal = carpeta_cv / ("cv-" + idioma + ".pdf.tmp")
                imprimir_pdf(navegador, base + "/" + idioma + "/", temporal)
                temporales[idioma] = temporal
    finally:
        servidor.shutdown()
    for idioma in IDIOMAS:
        final = carpeta_cv / ("cv-" + idioma + ".pdf")
        temporales[idioma].replace(final)
        imprimir("  cv-" + idioma + ".pdf: " + str(contar_paginas(final)) + " página(s)")


def actualizar_perfil(ruta_perfil):
    perfil = json.loads(ruta_perfil.read_text(encoding="utf-8"))
    perfil["cv_pdf"] = dict(CV_PDF)
    escribir_si_cambio(ruta_perfil, json_estable(perfil))


def limpiar_temporales(carpeta_cv):
    if not carpeta_cv.exists():
        return
    for temporal in carpeta_cv.glob("*.pdf.tmp"):
        temporal.unlink()


# ------------------------------------------------------------------ estado y salida


def anotar_falla(ruta_estado, motivo):
    imprimir("::warning::No se pudo generar el CV en PDF (" + motivo + "); se conservan los anteriores")
    if not ruta_estado or not Path(ruta_estado).exists():
        return
    estado = json.loads(Path(ruta_estado).read_text(encoding="utf-8"))
    estado["advertencias"].append({"clave": "portfolio", "nombre": "CV en PDF", "tipo": "cv_pdf_fallido", "detalle": motivo + "; se conservan los PDF anteriores"})
    Path(ruta_estado).write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


def escribir_salida_de_github(nombre, valor):
    ruta = os.environ.get("GITHUB_OUTPUT")
    if ruta:
        with open(ruta, "a", encoding="utf-8") as archivo:
            archivo.write(nombre + "=" + valor + "\n")


def regenerar(opciones):
    carpeta_cv = Path(opciones.carpeta_cv)
    ruta_perfil = Path(opciones.perfil)
    try:
        if not opciones.sin_build:
            imprimir("CV: npm run build")
            correr_build()
        imprimir("CV: generando PDF")
        generar_pdfs(RAIZ / "dist", carpeta_cv)
        actualizar_perfil(ruta_perfil)
    except Exception as error:  # cualquier falla: se conservan los PDF anteriores
        limpiar_temporales(carpeta_cv)
        motivo = str(error) if str(error) in ("build", "pagina") else type(error).__name__
        anotar_falla(opciones.estado, motivo)
        return 0
    # La huella se calcula DESPUÉS de actualizar perfil.json: así la próxima corrida no regenera de nuevo.
    (carpeta_cv / "huella.txt").write_text(calcular_huella() + "\n", encoding="utf-8", newline="\n")
    imprimir("CV: listo")
    return 0


def main():
    instalar_gancho_de_excepciones()
    parser = argparse.ArgumentParser()
    parser.add_argument("--chequear", action="store_true")
    parser.add_argument("--estado", default=None)
    parser.add_argument("--carpeta-cv", dest="carpeta_cv", default=str(CARPETA_CV))
    parser.add_argument("--perfil", default=str(RUTA_PERFIL_JSON))
    parser.add_argument("--sin-build", dest="sin_build", action="store_true")
    parser.add_argument("--cv-propio", dest="cv_propio", default=str(CARPETA_CV_PROPIO))
    opciones = parser.parse_args()
    origenes = archivos_cv_propio(Path(opciones.cv_propio))
    if origenes is not None:
        copio = copiar_cv_propio(origenes, Path(opciones.carpeta_cv), Path(opciones.perfil))
        imprimir("CV propio: " + ("copiado a public/cv/" if copio else "sin cambios"))
        if opciones.chequear:
            imprimir("regenerar=false")
            escribir_salida_de_github("regenerar", "false")
        return 0
    if opciones.chequear:
        valor = "true" if hay_que_regenerar(Path(opciones.carpeta_cv)) else "false"
        imprimir("regenerar=" + valor)
        escribir_salida_de_github("regenerar", valor)
        return 0
    if not hay_que_regenerar(Path(opciones.carpeta_cv)):
        imprimir("CV: sin cambios (misma huella)")
        return 0
    return regenerar(opciones)


if __name__ == "__main__":
    sys.exit(main())
