"""Paso final de `actualizar-datos` (if: always()): issues + Telegram según el resultado de la corrida (§4.5).

Uso (en el workflow):
  python -X utf8 scripts/enviar_alertas.py --estado RUTA --pasos "datos=success,cv=success,commit=failure"
Variables: GITHUB_TOKEN (permiso issues: write), GITHUB_REPOSITORY, GITHUB_SERVER_URL, GITHUB_RUN_ID,
           TELEGRAM_TOKEN_ALERTAS y TELEGRAM_CHAT_ALERTAS (opcionales), TOKEN_VENCE (respaldo).
Nunca hace fallar el job por sí mismo: si algo de las alertas falla, deja un ::warning::.
"""

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

from portfolio.alertas import (
    ETIQUETA_DATOS,
    TITULO_DATOS,
    Issues,
    gestionar_falla,
    gestionar_lista,
    gestionar_token,
)
from portfolio.api_github import ClienteGitHub, ErrorGitHub
from portfolio.identidad import imprimir, instalar_gancho_de_excepciones

NOMBRES_DE_PASOS = {
    "datos": "generar datos",
    "cv": "generar CV en PDF",
    "commit": "commit y push",
    "instalar": "instalar dependencias",
}


def url_de_corrida():
    servidor = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    return servidor + "/" + os.environ.get("GITHUB_REPOSITORY", "?") + "/actions/runs/" + os.environ.get("GITHUB_RUN_ID", "?")


def leer_pasos(texto):
    """'datos=success,cv=skipped' → [("datos", "success"), ("cv", "skipped")] en orden."""
    pasos = []
    for parte in (texto or "").split(","):
        if "=" in parte:
            nombre, resultado = parte.split("=", 1)
            pasos.append((nombre.strip(), resultado.strip()))
    return pasos


def primer_paso_fallido(pasos):
    for nombre, resultado in pasos:
        if resultado == "failure":
            return NOMBRES_DE_PASOS.get(nombre, nombre)
    return None


def leer_estado(ruta):
    if ruta and Path(ruta).exists():
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    return None


def main():
    instalar_gancho_de_excepciones()
    parser = argparse.ArgumentParser()
    parser.add_argument("--estado", default=None)
    parser.add_argument("--pasos", default="")
    opciones = parser.parse_args()

    estado = leer_estado(opciones.estado)
    paso_fallido = primer_paso_fallido(leer_pasos(opciones.pasos))
    if estado is not None and estado["resultado"] == "falla" and paso_fallido is None:
        paso_fallido = NOMBRES_DE_PASOS["datos"]
    fallo = paso_fallido is not None
    url = url_de_corrida()
    issues = Issues(ClienteGitHub(os.environ.get("GITHUB_TOKEN", "")), os.environ.get("GITHUB_REPOSITORY", ""))
    falla = estado["falla"] if estado else None

    acciones = []
    try:
        acciones.append(("falla", gestionar_falla(issues, fallo, falla, paso_fallido or "", url)))
        # Advertencias y token: solo si generar_datos llegó a publicar (si no, no hay lista confiable).
        if estado is not None and estado["resultado"] == "ok":
            advertencias = estado["advertencias"]
            acciones.append(("datos", gestionar_lista(
                issues, ETIQUETA_DATOS, TITULO_DATOS, advertencias,
                "Advertencias de la última corrida", "Se cierra solo cuando una corrida no tiene advertencias.", url,
            )))
        if estado is not None:
            vencimiento = estado.get("vencimiento_token") or os.environ.get("TOKEN_VENCE") or None
            acciones.append(("token", gestionar_token(issues, vencimiento, datetime.date.today())))
    except ErrorGitHub as error:
        imprimir("::warning::No se pudieron gestionar los issues de alerta: " + error.descripcion())
    for nombre, accion in acciones:
        imprimir("alerta " + nombre + ": " + accion)
    return 0


if __name__ == "__main__":
    sys.exit(main())
