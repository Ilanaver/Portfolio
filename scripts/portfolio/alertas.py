"""Alertas por issue en el repo del portfolio (§4.5), con el mismo aviso por Telegram.

Issues (uno abierto por etiqueta como máximo):
- alerta-actualizacion  "Falló la actualización del portfolio": se abre (o se comenta) si el job falla; se
                        cierra solo con "Resuelto en la corrida X" cuando una corrida sale bien.
- alerta-datos          "Advertencias en los datos": lista de advertencias (privados solo por clave opaca). Se
                        actualiza solo si cambia la lista; se cierra cuando una corrida no tiene advertencias.
- alerta-token          "El token de lectura vence el AAAA-MM-DD": si vence en ≤ 14 días; se cierra solo con
                        una fecha nueva > 14 días.
- alerta-links          "Links caídos" (chequear_links.py).
Telegram: cuando un issue se abre, cambia su contenido, vuelve a fallar o se resuelve. Nunca en cada corrida.
Todo texto pasa por el filtro de redacción antes de salir.
"""

import datetime
import hashlib
import re

from portfolio.identidad import REDACTOR, imprimir
from portfolio import telegram

ETIQUETA_FALLA = "alerta-actualizacion"
ETIQUETA_DATOS = "alerta-datos"
ETIQUETA_TOKEN = "alerta-token"
ETIQUETA_LINKS = "alerta-links"

TITULO_FALLA = "Falló la actualización del portfolio"
TITULO_DATOS = "Advertencias en los datos"
TITULO_LINKS = "Links caídos"
DIAS_AVISO_TOKEN = 14

COLORES = {ETIQUETA_FALLA: "d73a4a", ETIQUETA_DATOS: "fbca04", ETIQUETA_TOKEN: "e99695", ETIQUETA_LINKS: "c5def5"}
PATRON_HUELLA = re.compile(r"<!-- huella: ([0-9a-f]{12}) -->")

PASOS_DE_RENOVACION = """Pasos para renovarlo:
1. GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens → `portfolio-lectura` → Regenerate token (mantiene los permisos).
2. Repo del portfolio → Settings → Secrets and variables → Actions: actualizar el secret `GH_TOKEN_LECTURA` y la variable `TOKEN_VENCE` (AAAA-MM-DD).
3. Actions → actualizar-datos → Run workflow. Este issue se cierra solo."""


# ------------------------------------------------------------------ API de issues


class Issues:
    """Operaciones sobre los issues del repo del portfolio con el GITHUB_TOKEN del job."""

    def __init__(self, api, repositorio):
        self.api = api  # objeto con .rest(metodo, ruta, json=None) (ClienteGitHub)
        self.base = "/repos/" + repositorio

    def buscar_abierto(self, etiqueta):
        lista = self.api.rest("GET", self.base + "/issues?state=open&per_page=20&labels=" + etiqueta) or []
        for issue in lista:
            if "pull_request" not in issue:
                return issue
        return None

    def asegurar_etiqueta(self, etiqueta):
        existentes = self.api.rest("GET", self.base + "/labels?per_page=100") or []
        for existente in existentes:
            if existente["name"] == etiqueta:
                return
        self.api.rest("POST", self.base + "/labels", json={"name": etiqueta, "color": COLORES.get(etiqueta, "ededed")})

    def abrir(self, titulo, cuerpo, etiqueta):
        self.asegurar_etiqueta(etiqueta)
        datos = {"title": REDACTOR.redactar(titulo), "body": REDACTOR.redactar(cuerpo), "labels": [etiqueta]}
        return self.api.rest("POST", self.base + "/issues", json=datos)

    def comentar(self, numero, texto):
        self.api.rest("POST", self.base + "/issues/" + str(numero) + "/comments", json={"body": REDACTOR.redactar(texto)})

    def editar(self, numero, titulo=None, cuerpo=None):
        datos = {}
        if titulo is not None:
            datos["title"] = REDACTOR.redactar(titulo)
        if cuerpo is not None:
            datos["body"] = REDACTOR.redactar(cuerpo)
        return self.api.rest("PATCH", self.base + "/issues/" + str(numero), json=datos)

    def cerrar(self, numero, comentario):
        self.comentar(numero, comentario)
        self.api.rest("PATCH", self.base + "/issues/" + str(numero), json={"state": "closed", "state_reason": "completed"})


# ------------------------------------------------------------------ textos


def nombre_de(item):
    return item["nombre"] if item.get("nombre") else item["clave"]


def linea_de(item):
    texto = nombre_de(item) + " — " + item["tipo"]
    if item.get("detalle"):
        texto += " (" + item["detalle"] + ")"
    return texto


def lineas_de(items):
    lineas = []
    for item in items:
        lineas.append("- " + linea_de(item))
    lineas.sort()
    return lineas


def huella_de(lineas):
    return hashlib.sha256("\n".join(lineas).encode("utf-8")).hexdigest()[:12]


def huella_del_cuerpo(cuerpo):
    coincidencia = PATRON_HUELLA.search(cuerpo or "")
    return coincidencia.group(1) if coincidencia else None


def cuerpo_con_lista(introduccion, lineas, cierre):
    return "\n".join([introduccion, ""] + lineas + ["", cierre, "", "<!-- huella: " + huella_de(lineas) + " -->"])


def texto_de_falla(falla, paso, url_corrida):
    lineas = ["La actualización automática del portfolio falló.", "", "- Corrida: " + url_corrida, "- Paso que falló: " + paso]
    if falla:
        tipo = falla["tipo"]
        if falla.get("detalle"):
            tipo += " (" + falla["detalle"] + ")"
        lineas.append("- Tipo: " + tipo)
    lineas.extend(["", "El sitio sigue con los datos anteriores. Este issue se cierra solo cuando una corrida sale bien."])
    return "\n".join(lineas)


def mensaje_telegram(titulo, detalle, url_issue):
    return "Portfolio — " + titulo + "\n" + detalle + "\n" + (url_issue or "")


def dias_hasta(fecha_iso, hoy):
    return (datetime.date.fromisoformat(fecha_iso) - hoy).days


# ------------------------------------------------------------------ decisiones


def gestionar_falla(issues, fallo, falla, paso, url_corrida, avisar=telegram.enviar):
    """Abre/comenta el issue de falla si el job falló; lo cierra si salió bien."""
    abierto = issues.buscar_abierto(ETIQUETA_FALLA)
    if fallo:
        texto = texto_de_falla(falla, paso, url_corrida)
        if abierto is None:
            issue = issues.abrir(TITULO_FALLA, texto, ETIQUETA_FALLA)
            url = issue["html_url"] if issue else None
        else:
            issues.comentar(abierto["number"], "Volvió a fallar.\n\n" + texto)
            url = abierto["html_url"]
        avisar(mensaje_telegram(TITULO_FALLA, "Paso: " + paso + (" — " + falla["tipo"] if falla else ""), url))
        return "abierto" if abierto is None else "comentado"
    if abierto is not None:
        issues.cerrar(abierto["number"], "Resuelto en la corrida " + url_corrida)
        avisar(mensaje_telegram("resuelto: " + TITULO_FALLA.lower(), "Corrida: " + url_corrida, abierto["html_url"]))
        return "cerrado"
    return "sin_cambios"


def gestionar_lista(issues, etiqueta, titulo, items, introduccion, cierre, url_corrida, avisar=telegram.enviar):
    """Issue de lista (advertencias o links): abre, actualiza si cambió la lista, o cierra si está vacía."""
    abierto = issues.buscar_abierto(etiqueta)
    if not items:
        if abierto is not None:
            issues.cerrar(abierto["number"], "Sin pendientes en la corrida " + url_corrida + ".")
            avisar(mensaje_telegram("resuelto: " + titulo.lower(), "Corrida: " + url_corrida, abierto["html_url"]))
            return "cerrado"
        return "sin_cambios"
    lineas = lineas_de(items)
    cuerpo = cuerpo_con_lista(introduccion + " (corrida " + url_corrida + "):", lineas, cierre)
    resumen = str(len(lineas)) + " pendiente(s):\n" + "\n".join(lineas[:10])
    if abierto is None:
        issue = issues.abrir(titulo, cuerpo, etiqueta)
        avisar(mensaje_telegram(titulo, resumen, issue["html_url"] if issue else None))
        return "abierto"
    if huella_del_cuerpo(abierto.get("body")) == huella_de(lineas):
        return "sin_cambios"
    issues.editar(abierto["number"], cuerpo=cuerpo)
    avisar(mensaje_telegram(titulo + " (cambió)", resumen, abierto["html_url"]))
    return "actualizado"


def gestionar_token(issues, vencimiento, hoy, avisar=telegram.enviar):
    """Issue de vencimiento del token. Sin fecha conocida → solo advertencia en el log."""
    abierto = issues.buscar_abierto(ETIQUETA_TOKEN)
    if not vencimiento:
        imprimir("::warning::No se conoce el vencimiento del token (ni header ni variable TOKEN_VENCE)")
        return "sin_fecha"
    dias = dias_hasta(vencimiento, hoy)
    titulo = "El token de lectura vence el " + vencimiento
    if dias > DIAS_AVISO_TOKEN:
        if abierto is not None:
            issues.cerrar(abierto["number"], "Token renovado: ahora vence el " + vencimiento + ".")
            return "cerrado"
        return "sin_cambios"
    cuerpo = "El token `GH_TOKEN_LECTURA` vence el " + vencimiento + " (en " + str(dias) + " días).\n\n" + PASOS_DE_RENOVACION
    if abierto is None:
        issue = issues.abrir(titulo, cuerpo, ETIQUETA_TOKEN)
        avisar(mensaje_telegram(titulo, "Faltan " + str(dias) + " días.", issue["html_url"] if issue else None))
        return "abierto"
    if abierto["title"] != titulo:
        issues.editar(abierto["number"], titulo=titulo, cuerpo=cuerpo)
        avisar(mensaje_telegram(titulo, "Faltan " + str(dias) + " días.", abierto["html_url"]))
        return "actualizado"
    return "sin_cambios"
