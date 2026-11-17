"""Auditoría LOCAL de repos y proyectos extra (usa tu `gh`; nunca corre en el Action).

Muestra, para cada repo: clave opaca → nombre, visibilidad, si tiene PORTFOLIO.md, si valida (con el detalle),
si es visible, inglés faltante y el estado de la captura manual (aprobada / sin aprobar / cambió). Para los
proyectos extra: si validan y si están desactualizados (activos sin actividad hace más de 6 meses).
Esta salida SÍ nombra repos privados: es solo para tu terminal. No la pegues en issues ni en logs públicos.

Uso:
  python -X utf8 scripts/auditar_repos.py                 tabla completa
  python -X utf8 scripts/auditar_repos.py --con-archivo   solo repos con PORTFOLIO.md
  python -X utf8 scripts/auditar_repos.py --hash-imagen <repo>
      descarga la captura manual de <repo> a una carpeta temporal para que la mires y te da el hash
      (12 caracteres) para `imagen.aprobada`. Completarlo solo después de revisarla.
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from portfolio.api_github import CONSULTA_REPOS, repo_desde_nodo
from portfolio.archivo_estandar import ErrorArchivoEstandar, leer_archivo_estandar
from portfolio.identidad import clave_opaca
from portfolio.imagenes import hash_corto, tipo_real
from portfolio.proyectos_extra import esta_desactualizado, leer_extra, listar_archivos


# ------------------------------------------------------------------ gh


def correr_gh(argumentos, binario=False):
    proceso = subprocess.run(["gh"] + argumentos, capture_output=True)
    if proceso.returncode != 0:
        raise RuntimeError("gh " + " ".join(argumentos[:2]) + ": " + proceso.stderr.decode("utf-8", "replace").strip())
    if binario:
        return proceso.stdout
    return proceso.stdout.decode("utf-8")


def listar_repos_con_gh():
    repos = []
    cursor = None
    with tempfile.TemporaryDirectory() as carpeta:
        ruta_consulta = Path(carpeta) / "consulta.graphql"
        ruta_consulta.write_text(CONSULTA_REPOS, encoding="utf-8")
        while True:
            argumentos = ["api", "graphql", "-F", "query=@" + str(ruta_consulta)]
            if cursor:
                argumentos.extend(["-F", "cursor=" + cursor])
            datos = json.loads(correr_gh(argumentos))["data"]["viewer"]["repositories"]
            for nodo in datos["nodes"]:
                repos.append(repo_desde_nodo(nodo))
            if not datos["pageInfo"]["hasNextPage"]:
                break
            cursor = datos["pageInfo"]["endCursor"]
    return repos


def descargar_archivo(repo, ruta):
    return correr_gh(
        ["api", "-H", "Accept: application/vnd.github.raw+json", "/repos/" + repo["dueno"] + "/" + repo["nombre"] + "/contents/" + ruta],
        binario=True,
    )


# ------------------------------------------------------------------ estado de cada repo


def estado_de_imagen(repo, datos):
    imagen = datos["imagen"]
    if not imagen:
        return "-"
    try:
        contenido = descargar_archivo(repo, imagen["archivo"])
    except RuntimeError:
        return "no se pudo leer"
    huella = hash_corto(contenido)
    if tipo_real(contenido) is None:
        return "formato inválido"
    if not repo["es_privado"]:
        return "pública (" + huella + ")"
    if imagen["aprobada"] is None:
        return "SIN APROBAR (" + huella + ")"
    if imagen["aprobada"] != huella:
        return "CAMBIÓ: aprobada " + imagen["aprobada"] + ", actual " + huella
    return "aprobada"


def fila_de_repo(repo):
    clave = clave_opaca(repo["id"], repo["es_privado"])
    fila = {
        "clave": clave,
        "repo": repo["nombre"],
        "visibilidad": "privado" if repo["es_privado"] else "público",
        "archivo": "no",
        "estado": "",
        "detalles": [],
    }
    if repo["portfolio_md"] is None:
        return fila
    fila["archivo"] = "sí"
    contexto = {"tipo": "repo", "es_privado": repo["es_privado"], "nombre_repo": repo["nombre"], "creado": repo["creado"]}
    try:
        leido = leer_archivo_estandar(repo["portfolio_md"], contexto)
    except ErrorArchivoEstandar as error:
        fila["estado"] = "NO VALIDA"
        fila["detalles"] = list(error.detalles)
        return fila
    datos = leido["datos"]
    fila["estado"] = "visible" if datos["visible"] else "oculto"
    for advertencia in leido["advertencias"]:
        fila["detalles"].append(advertencia)
    fila["detalles"].append("imagen: " + estado_de_imagen(repo, datos))
    fila["detalles"].append("slug: " + datos["slug"] + "; captura_auto: " + str(datos["captura_auto"]).lower() + "; bitácora: " + str(datos["mostrar_bitacora"]).lower())
    return fila


def fila_de_extra(ruta):
    fila = {"clave": "extra-" + ruta.stem, "repo": ruta.name, "visibilidad": "extra", "archivo": "sí", "estado": "", "detalles": []}
    try:
        extra = leer_extra(ruta)
    except ErrorArchivoEstandar as error:
        fila["estado"] = "NO VALIDA"
        fila["detalles"] = list(error.detalles)
        return fila
    datos = extra["datos"]
    fila["estado"] = "visible" if datos["visible"] else "oculto"
    fila["detalles"].extend(extra["advertencias"])
    if esta_desactualizado(datos):
        fila["detalles"].append("DESACTUALIZADO: activo sin actividad desde " + datos["ultima_actividad"])
    return fila


# ------------------------------------------------------------------ salida


def imprimir_tabla(filas):
    columnas = ("clave", "repo", "visibilidad", "archivo", "estado")
    anchos = {}
    for columna in columnas:
        anchos[columna] = len(columna)
        for fila in filas:
            anchos[columna] = max(anchos[columna], len(fila[columna]))
    encabezado = []
    for columna in columnas:
        encabezado.append(columna.upper().ljust(anchos[columna]))
    print("  ".join(encabezado))
    for fila in filas:
        celdas = []
        for columna in columnas:
            celdas.append(fila[columna].ljust(anchos[columna]))
        print("  ".join(celdas))
        for detalle in fila["detalles"]:
            print("      · " + detalle)


def hash_de_imagen(repos, nombre):
    for repo in repos:
        if repo["nombre"].lower() != nombre.lower():
            continue
        if repo["portfolio_md"] is None:
            print("El repo no tiene PORTFOLIO.md.")
            return 1
        contexto = {"tipo": "repo", "es_privado": repo["es_privado"], "nombre_repo": repo["nombre"], "creado": repo["creado"]}
        datos = leer_archivo_estandar(repo["portfolio_md"], contexto)["datos"]
        if not datos["imagen"]:
            print("El PORTFOLIO.md no tiene `imagen`.")
            return 1
        contenido = descargar_archivo(repo, datos["imagen"]["archivo"])
        destino = Path(tempfile.mkdtemp(prefix="portfolio-captura-")) / Path(datos["imagen"]["archivo"]).name
        destino.write_bytes(contenido)
        print("Captura descargada para revisar: " + str(destino))
        print("Tipo real: " + str(tipo_real(contenido)) + "; " + str(len(contenido)) + " bytes")
        print("Hash (imagen.aprobada): " + hash_corto(contenido))
        print("Revisá que no tenga montos, posiciones, nombres ni datos personales (también pestañas y barras)")
        print("antes de completar `aprobada`. Si la imagen cambia, el hash deja de coincidir.")
        return 0
    print("No encontré el repo '" + nombre + "'.")
    return 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--con-archivo", dest="con_archivo", action="store_true")
    parser.add_argument("--hash-imagen", dest="hash_imagen", default=None, metavar="REPO")
    opciones = parser.parse_args()
    repos = listar_repos_con_gh()
    if opciones.hash_imagen:
        return hash_de_imagen(repos, opciones.hash_imagen)
    filas = []
    for repo in repos:
        if opciones.con_archivo and repo["portfolio_md"] is None:
            continue
        filas.append(fila_de_repo(repo))
    for ruta in listar_archivos():
        filas.append(fila_de_extra(ruta))
    print("Repos: " + str(len(repos)) + " · con PORTFOLIO.md: " + str(contar_con_archivo(repos)) + " · extras: " + str(len(listar_archivos())))
    print("(salida LOCAL: nombra repos privados)")
    print()
    imprimir_tabla(filas)
    return 0


def contar_con_archivo(repos):
    cantidad = 0
    for repo in repos:
        if repo["portfolio_md"] is not None:
            cantidad += 1
    return cantidad


if __name__ == "__main__":
    sys.exit(main())
