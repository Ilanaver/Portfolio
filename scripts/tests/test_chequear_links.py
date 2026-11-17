"""chequear_links.py con una sesión HTTP simulada (paso 36)."""

import requests

import chequear_links
from portfolio.identidad import REDACTOR


class Respuesta:
    def __init__(self, codigo):
        self.status_code = codigo

    def close(self):
        pass


class Sesion:
    """url → lista de respuestas (códigos o excepciones) que se devuelven en orden."""

    def __init__(self, guion):
        self.guion = guion
        self.pedidos = []

    def get(self, url, **opciones):
        self.pedidos.append(url)
        siguiente = self.guion[url].pop(0)
        if isinstance(siguiente, Exception):
            raise siguiente
        return Respuesta(siguiente)


def proyecto(clave, nombre, privado, demo=None, repo=None, otros=None):
    lista_otros = []
    for url in otros or []:
        lista_otros.append({"texto": {"es": "x", "en": None}, "url": url})
    return {
        "clave": clave, "es_privado": privado, "slug": nombre.lower().replace(" ", "-"), "slugs_anteriores": [],
        "nombre": {"es": nombre, "en": nombre}, "links": {"demo": demo, "repo": repo, "otros": lista_otros},
    }


PERFIL = {"contacto": {"email": "a@b.c", "github": "https://github.com/dueno", "linkedin": None}}


def test_clasificacion_y_privacidad():
    proyectos = [
        proyecto("pub-11111111", "Publico", False, demo="https://ok.test", repo="https://github.com/dueno/publico", otros=["https://caido.test"]),
        proyecto("priv-22222222", "Super Privado", True, demo="https://privado-demo.test"),
        proyecto("pub-33333333", "Bloquea Bots", False, demo="https://bloquea.test"),
    ]
    sesion = Sesion({
        "https://ok.test": [200],
        "https://github.com/dueno/publico": [301],
        "https://caido.test": [404],
        "https://privado-demo.test": [requests.ConnectionError("https://privado-demo.test")] * 3,
        "https://bloquea.test": [403],
        "https://github.com/dueno": [200],
    })
    esperas = []
    links = chequear_links.links_a_revisar(proyectos, PERFIL)
    assert len(links) == 6
    caidos, no_verificables = chequear_links.chequear(links, sesion, esperas.append)
    assert caidos == [
        {"clave": "pub-11111111", "nombre": "Publico — https://caido.test", "tipo": "link_caido", "detalle": "link otro — HTTP 404"},
        {"clave": "priv-22222222", "nombre": None, "tipo": "link_caido", "detalle": "link demo — error de red"},
    ]
    assert no_verificables[0]["detalle"] == "link demo — HTTP 403"
    assert esperas == [3, 3]  # 2 reintentos solo para el error de red
    # El nombre y la demo del privado quedan registrados para el filtro de redacción.
    assert "Super Privado" not in REDACTOR.redactar("falló Super Privado en https://privado-demo.test")


def test_5xx_se_reintenta_y_404_no():
    sesion = Sesion({"https://a.test": [502, 503, 200], "https://b.test": [404]})
    esperas = []
    assert chequear_links.consultar("https://a.test", sesion, esperas.append) == ("ok", None)
    assert chequear_links.consultar("https://b.test", sesion, esperas.append) == ("caido", "HTTP 404")
    assert esperas == [3, 3]


def test_timeout_agotado():
    sesion = Sesion({"https://lento.test": [requests.Timeout()] * 3})
    assert chequear_links.consultar("https://lento.test", sesion, lambda s: None) == ("caido", "timeout")


def test_cierre_con_no_verificables():
    texto = chequear_links.cierre_del_issue([{"clave": "pub-1", "nombre": "X — https://x.test", "tipo": "link_caido", "detalle": "link demo — HTTP 429"}])
    assert "No verificables" in texto and "https://x.test" in texto and "HTTP 429" in texto
