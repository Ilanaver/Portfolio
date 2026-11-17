"""Chequeo semanal de links caídos (P11, §4.5). Sin token de lectura: solo lee el JSON publicado.

- Links: demo, repo y otros de cada proyecto; GitHub y LinkedIn del perfil.
- GET con timeout de 15 s y 2 reintentos (errores de red, timeout, 5xx).
- 403/429 (bloqueo a bots) → lista aparte "no verificables", no cuentan como caídos.
- Issue `Links caídos` (etiqueta alerta-links) + Telegram al abrirse o cambiar; se cierra solo cuando todo
  responde. Público por URL; privado como `priv-1a2b3c4d — link_caido (link demo — HTTP 404)`.

Uso: python -X utf8 scripts/chequear_links.py [--sin-issues]
Variables (en el Action): GITHUB_TOKEN, GITHUB_REPOSITORY, GITHUB_RUN_ID, TELEGRAM_TOKEN_ALERTAS, TELEGRAM_CHAT_ALERTAS.
"""

import argparse
import json
import os
import sys
import time

import requests

from portfolio import CARPETA_DATOS
from portfolio.alertas import ETIQUETA_LINKS, TITULO_LINKS, Issues, gestionar_lista
from portfolio.api_github import ClienteGitHub, ErrorGitHub
from portfolio.identidad import REDACTOR, imprimir, instalar_gancho_de_excepciones

TIEMPO_ESPERA = 15
REINTENTOS = 2
ESPERA_ENTRE_REINTENTOS = 3
CODIGOS_NO_VERIFICABLES = (403, 429)
ENCABEZADOS = {"User-Agent": "Mozilla/5.0 (compatible; portfolio-chequear-links)"}


# ------------------------------------------------------------------ links publicados


def links_de_proyecto(proyecto):
    """[(tipo de link, url)] de un proyecto."""
    links = []
    if proyecto["links"]["demo"]:
        links.append(("demo", proyecto["links"]["demo"]))
    if proyecto["links"]["repo"]:
        links.append(("repo", proyecto["links"]["repo"]))
    for otro in proyecto["links"]["otros"]:
        links.append(("otro", otro["url"]))
    return links


def links_a_revisar(proyectos, perfil):
    """[{"clave", "nombre" (None si es privado), "tipo_link", "url"}]."""
    revisar = []
    for proyecto in proyectos:
        nombre = None if proyecto["es_privado"] else proyecto["nombre"]["es"]
        if proyecto["es_privado"]:
            registrar_privado(proyecto)
        for tipo_link, url in links_de_proyecto(proyecto):
            revisar.append({"clave": proyecto["clave"], "nombre": nombre, "tipo_link": tipo_link, "url": url})
    contacto = perfil["contacto"]
    for tipo_link in ("github", "linkedin"):
        if contacto.get(tipo_link):
            revisar.append({"clave": "perfil", "nombre": "Perfil", "tipo_link": tipo_link, "url": contacto[tipo_link]})
    return revisar


def registrar_privado(proyecto):
    REDACTOR.registrar_proyecto_privado(
        {"slug": proyecto["slug"], "nombre": proyecto["nombre"], "links": proyecto["links"], "slugs_anteriores": proyecto["slugs_anteriores"]},
        proyecto["clave"],
    )


# ------------------------------------------------------------------ chequeo


def consultar(url, sesion, dormir=time.sleep):
    """Devuelve ("ok" | "no_verificable" | "caido", detalle). Nunca lanza excepciones."""
    detalle = None
    for intento in range(REINTENTOS + 1):
        try:
            respuesta = sesion.get(url, timeout=TIEMPO_ESPERA, allow_redirects=True, headers=ENCABEZADOS, stream=True)
            respuesta.close()
        except requests.Timeout:
            detalle = "timeout"
        except requests.RequestException:
            detalle = "error de red"
        else:
            codigo = respuesta.status_code
            if codigo < 400:
                return "ok", None
            if codigo in CODIGOS_NO_VERIFICABLES:
                return "no_verificable", "HTTP " + str(codigo)
            detalle = "HTTP " + str(codigo)
            if codigo < 500:
                return "caido", detalle
        if intento < REINTENTOS:
            dormir(ESPERA_ENTRE_REINTENTOS)
    return "caido", detalle


def item_de(link, detalle):
    """Ítem para el issue. Público: con la URL; privado: solo clave y tipo de link."""
    if link["nombre"] is None:
        return {"clave": link["clave"], "nombre": None, "tipo": "link_caido", "detalle": "link " + link["tipo_link"] + " — " + detalle}
    return {"clave": link["clave"], "nombre": link["nombre"] + " — " + link["url"], "tipo": "link_caido", "detalle": "link " + link["tipo_link"] + " — " + detalle}


def chequear(links, sesion, dormir=time.sleep):
    """Devuelve (caídos, no verificables) como ítems para el issue."""
    caidos = []
    no_verificables = []
    for link in links:
        resultado, detalle = consultar(link["url"], sesion, dormir)
        if resultado == "caido":
            caidos.append(item_de(link, detalle))
        elif resultado == "no_verificable":
            no_verificables.append(item_de(link, detalle))
    return caidos, no_verificables


def lineas_no_verificables(items):
    lineas = []
    for item in items:
        nombre = item["nombre"] if item["nombre"] else item["clave"]
        lineas.append("- " + nombre + " (" + item["detalle"] + ")")
    lineas.sort()
    return lineas


def cierre_del_issue(no_verificables):
    texto = "Se cierra solo cuando todos los links responden."
    if not no_verificables:
        return texto
    return "\n".join(["No verificables (el sitio bloquea a bots con 403/429; no cuentan como caídos):", ""] + lineas_no_verificables(no_verificables) + ["", texto])


# ------------------------------------------------------------------ entrada


def leer_json(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


def url_de_corrida():
    servidor = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    return servidor + "/" + os.environ.get("GITHUB_REPOSITORY", "?") + "/actions/runs/" + os.environ.get("GITHUB_RUN_ID", "local")


def main():
    instalar_gancho_de_excepciones()
    parser = argparse.ArgumentParser()
    parser.add_argument("--sin-issues", dest="sin_issues", action="store_true")
    opciones = parser.parse_args()

    proyectos = leer_json(CARPETA_DATOS / "proyectos.json")["proyectos"]
    perfil = leer_json(CARPETA_DATOS / "perfil.json")
    links = links_a_revisar(proyectos, perfil)
    caidos, no_verificables = chequear(links, requests.Session())
    imprimir("Links revisados: " + str(len(links)) + "; caídos: " + str(len(caidos)) + "; no verificables: " + str(len(no_verificables)))
    for item in caidos:
        imprimir("::warning::" + (item["nombre"] or item["clave"]) + " — " + item["detalle"])
    if opciones.sin_issues:
        return 0
    issues = Issues(ClienteGitHub(os.environ.get("GITHUB_TOKEN", "")), os.environ.get("GITHUB_REPOSITORY", ""))
    try:
        accion = gestionar_lista(
            issues, ETIQUETA_LINKS, TITULO_LINKS, caidos, "Links caídos en el chequeo semanal",
            cierre_del_issue(no_verificables), url_de_corrida(),
        )
        imprimir("alerta links: " + accion)
    except ErrorGitHub as error:
        imprimir("::warning::No se pudo gestionar el issue de links: " + error.descripcion())
    return 0


if __name__ == "__main__":
    sys.exit(main())
