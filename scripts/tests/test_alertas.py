"""alertas.py y telegram.py con la API de GitHub y Telegram simuladas (paso 34)."""

import datetime

import pytest
import requests

from portfolio import telegram
from portfolio.alertas import (
    ETIQUETA_DATOS,
    ETIQUETA_FALLA,
    ETIQUETA_TOKEN,
    TITULO_DATOS,
    Issues,
    gestionar_falla,
    gestionar_lista,
    gestionar_token,
)
from portfolio.identidad import REDACTOR

URL = "https://github.com/dueno/portfolio/actions/runs/1"


class ApiFalsa:
    """Issues y etiquetas en memoria, con la forma de la API REST."""

    def __init__(self):
        self.issues = []
        self.etiquetas = []
        self.comentarios = []

    def rest(self, metodo, ruta, json=None):
        if metodo == "GET" and "/issues?" in ruta:
            etiqueta = ruta.split("labels=")[1]
            abiertos = []
            for issue in self.issues:
                if issue["state"] == "open" and etiqueta in issue["labels"]:
                    abiertos.append(issue)
            return abiertos
        if metodo == "GET" and ruta.endswith("/labels?per_page=100"):
            lista = []
            for nombre in self.etiquetas:
                lista.append({"name": nombre})
            return lista
        if metodo == "POST" and ruta.endswith("/labels"):
            self.etiquetas.append(json["name"])
            return json
        if metodo == "POST" and ruta.endswith("/issues"):
            numero = len(self.issues) + 1
            issue = {
                "number": numero, "title": json["title"], "body": json["body"], "labels": json["labels"],
                "state": "open", "html_url": "https://github.com/dueno/portfolio/issues/" + str(numero),
            }
            self.issues.append(issue)
            return issue
        if metodo == "POST" and ruta.endswith("/comments"):
            self.comentarios.append(json["body"])
            return {}
        if metodo == "PATCH":
            numero = int(ruta.rsplit("/", 1)[1])
            issue = self.issues[numero - 1]
            for clave in ("title", "body", "state"):
                if clave in json:
                    issue[clave] = json[clave]
            return issue
        raise AssertionError("pedido inesperado: " + metodo + " " + ruta)


@pytest.fixture
def entorno():
    api = ApiFalsa()
    mensajes = []
    return Issues(api, "dueno/portfolio"), api, mensajes


def test_falla_abre_comenta_y_cierra(entorno):
    issues, api, mensajes = entorno
    falla = {"tipo": "lista_de_repos_token_invalido", "detalle": "HTTP 401"}
    assert gestionar_falla(issues, True, falla, "generar datos", URL, mensajes.append) == "abierto"
    assert api.issues[0]["labels"] == [ETIQUETA_FALLA]
    assert ETIQUETA_FALLA in api.etiquetas
    assert "Paso que falló: generar datos" in api.issues[0]["body"]
    assert gestionar_falla(issues, True, falla, "commit y push", URL, mensajes.append) == "comentado"
    assert len(api.issues) == 1 and "Volvió a fallar" in api.comentarios[0]
    assert gestionar_falla(issues, False, None, "", URL, mensajes.append) == "cerrado"
    assert api.issues[0]["state"] == "closed"
    assert "Resuelto en la corrida " + URL in api.comentarios[-1]
    assert len(mensajes) == 3 and "resuelto" in mensajes[2]
    assert gestionar_falla(issues, False, None, "", URL, mensajes.append) == "sin_cambios"
    assert len(mensajes) == 3


def test_advertencias_solo_avisan_si_cambia_la_lista(entorno):
    issues, api, mensajes = entorno
    items = [
        {"clave": "priv-1a2b3c4d", "nombre": None, "tipo": "captura_auto_fallida", "detalle": "HTTP 503; se mantiene la captura anterior"},
        {"clave": "pub-00000000", "nombre": "Proyecto público", "tipo": "no_valida", "detalle": None},
    ]
    gestionar = lambda lista: gestionar_lista(issues, ETIQUETA_DATOS, TITULO_DATOS, lista, "Advertencias", "Se cierra solo.", URL, mensajes.append)
    assert gestionar(items) == "abierto"
    cuerpo = api.issues[0]["body"]
    assert "- priv-1a2b3c4d — captura_auto_fallida (HTTP 503; se mantiene la captura anterior)" in cuerpo
    assert "- Proyecto público — no_valida" in cuerpo
    assert gestionar(list(reversed(items))) == "sin_cambios"  # mismo contenido en otro orden
    assert len(mensajes) == 1
    assert gestionar(items[:1]) == "actualizado"
    assert len(mensajes) == 2
    assert gestionar([]) == "cerrado"
    assert api.issues[0]["state"] == "closed"
    assert len(mensajes) == 3


def test_token(entorno):
    issues, api, mensajes = entorno
    hoy = datetime.date(2027, 11, 1)
    assert gestionar_token(issues, "2027-12-31", hoy, mensajes.append) == "sin_cambios"
    assert gestionar_token(issues, "2027-11-10", hoy, mensajes.append) == "abierto"
    assert api.issues[0]["title"] == "El token de lectura vence el 2027-11-10"
    assert "Regenerate token" in api.issues[0]["body"]
    assert gestionar_token(issues, "2027-11-10", hoy, mensajes.append) == "sin_cambios"
    assert gestionar_token(issues, "2027-11-12", hoy, mensajes.append) == "actualizado"
    assert gestionar_token(issues, "2028-11-12", hoy, mensajes.append) == "cerrado"
    assert gestionar_token(issues, None, hoy, mensajes.append) == "sin_fecha"
    assert len(mensajes) == 2


def test_ningun_nombre_privado_en_issues_ni_telegram(entorno):
    issues, api, _ = entorno
    REDACTOR.registrar("repo-privadisimo", "priv-99999999")
    enviados = []

    class SesionTelegram:
        def post(self, url, json=None, timeout=None):
            enviados.append(json["text"])
            return type("R", (), {"status_code": 200})()

    def avisar(texto):
        return telegram.enviar(texto, token="123:abc", chat="1", sesion=SesionTelegram())

    falla = {"tipo": "no_se_pudo_leer", "detalle": "repo-privadisimo HTTP 502"}
    gestionar_falla(issues, True, falla, "generar datos", URL, avisar)
    items = [{"clave": "priv-99999999", "nombre": "repo-privadisimo", "tipo": "timeout", "detalle": None}]
    gestionar_lista(issues, ETIQUETA_DATOS, TITULO_DATOS, items, "Advertencias", "Se cierra solo.", URL, avisar)
    salidas = []
    for issue in api.issues:
        salidas.append(issue["title"] + issue["body"])
    salidas.extend(api.comentarios)
    salidas.extend(enviados)
    assert len(enviados) == 2
    for texto in salidas:
        assert "repo-privadisimo" not in texto
    assert "priv-99999999" in enviados[1]
    assert "priv-99999999" in api.issues[0]["body"]


def test_telegram_falla_no_lanza(capsys):
    class SesionCaida:
        def post(self, url, json=None, timeout=None):
            raise requests.ConnectionError("https://api.telegram.org/bot123:secreto/sendMessage")

    class SesionRechazo:
        def post(self, url, json=None, timeout=None):
            return type("R", (), {"status_code": 401})()

    assert telegram.enviar("hola", token="123:secreto", chat="1", sesion=SesionCaida()) is False
    assert telegram.enviar("hola", token="123:secreto", chat="1", sesion=SesionRechazo()) is False
    salida = capsys.readouterr().out
    assert "::warning::" in salida and "secreto" not in salida and "HTTP 401" in salida


def test_telegram_sin_configurar(monkeypatch, capsys):
    monkeypatch.delenv("TELEGRAM_TOKEN_ALERTAS", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ALERTAS", raising=False)
    assert telegram.enviar("hola") is False
    assert "Telegram sin configurar" in capsys.readouterr().out


def test_paso_fallido_desde_los_resultados_del_workflow():
    import enviar_alertas

    pasos = enviar_alertas.leer_pasos("datos=success, cv=failure ,commit=skipped")
    assert pasos == [("datos", "success"), ("cv", "failure"), ("commit", "skipped")]
    assert enviar_alertas.primer_paso_fallido(pasos) == "generar CV en PDF"
    assert enviar_alertas.primer_paso_fallido(enviar_alertas.leer_pasos("datos=success")) is None
