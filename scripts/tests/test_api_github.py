"""api_github.py con una sesión simulada (sin red): paginado, reintentos, vencimiento y errores sin URL (paso 28)."""

import json

import pytest
import requests

from portfolio.api_github import ClienteGitHub, ErrorGitHub, fecha_de_vencimiento


class RespuestaFalsa:
    def __init__(self, codigo=200, cuerpo=None, encabezados=None, contenido=None):
        self.status_code = codigo
        self.headers = encabezados or {}
        if contenido is not None:
            self.content = contenido
        elif cuerpo is not None:
            self.content = json.dumps(cuerpo).encode("utf-8")
        else:
            self.content = b""
        self.text = self.content.decode("utf-8", errors="replace")

    def json(self):
        return json.loads(self.content)


class SesionFalsa:
    """Devuelve las respuestas (o lanza las excepciones) en orden y guarda los pedidos."""

    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.pedidos = []

    def request(self, metodo, url, headers=None, json=None, timeout=None):
        self.pedidos.append({"metodo": metodo, "url": url, "headers": headers, "json": json})
        siguiente = self.respuestas.pop(0)
        if isinstance(siguiente, Exception):
            raise siguiente
        return siguiente


def nodo(nombre, privado, texto=None):
    return {
        "id": "R_" + nombre,
        "name": nombre,
        "isPrivate": privado,
        "isArchived": False,
        "createdAt": "2025-01-01T00:00:00Z",
        "pushedAt": "2026-11-16T10:00:00Z",
        "url": "https://github.com/dueno/" + nombre,
        "owner": {"login": "dueno"},
        "archivo": {"text": texto, "isBinary": False, "byteSize": 10} if texto else None,
    }


def pagina(nodos, siguiente=None):
    return {
        "data": {
            "viewer": {
                "login": "dueno",
                "repositories": {
                    "pageInfo": {"hasNextPage": siguiente is not None, "endCursor": siguiente},
                    "nodes": nodos,
                },
            }
        }
    }


def cliente(respuestas):
    esperas = []
    sesion = SesionFalsa(respuestas)
    return ClienteGitHub("token-de-prueba", sesion=sesion, dormir=esperas.append), sesion, esperas


def test_lista_paginada_y_vencimiento():
    vence = {"github-authentication-token-expiration": "2027-11-17 12:00:00 UTC"}
    api, sesion, _ = cliente([
        RespuestaFalsa(200, pagina([nodo("uno", False, "---\n")], siguiente="c1"), vence),
        RespuestaFalsa(200, pagina([nodo("dos", True)])),
    ])
    repos = api.listar_repos()
    assert [repo["nombre"] for repo in repos] == ["uno", "dos"]
    assert repos[0]["portfolio_md"] == "---\n"
    assert repos[1]["portfolio_md"] is None
    assert repos[1]["es_privado"] is True
    assert sesion.pedidos[1]["json"]["variables"] == {"cursor": "c1"}
    assert sesion.pedidos[0]["headers"]["Authorization"] == "Bearer token-de-prueba"
    assert api.vencimiento_token == "2027-11-17"


def test_reintenta_ante_5xx_y_limite():
    api, _, esperas = cliente([
        RespuestaFalsa(502),
        RespuestaFalsa(403, encabezados={"x-ratelimit-remaining": "0", "retry-after": "5"}),
        RespuestaFalsa(200, pagina([])),
    ])
    assert api.listar_repos() == []
    assert esperas == [2, 5]


def test_agota_reintentos():
    api, _, esperas = cliente([RespuestaFalsa(503)] * 4)
    with pytest.raises(ErrorGitHub) as error:
        api.listar_repos()
    assert error.value.tipo == "error_del_servidor" and error.value.codigo == 503
    assert len(esperas) == 3


def test_timeout_y_red_por_tipo_sin_url():
    url_privada = "https://api.github.com/repos/dueno/repo-secreto/contents/BITACORA.md"
    api, _, _ = cliente([requests.Timeout(url_privada)] * 4)
    with pytest.raises(ErrorGitHub) as error:
        api.leer_archivo("dueno", "repo-secreto", "BITACORA.md")
    assert error.value.tipo == "timeout"
    assert "repo-secreto" not in str(error.value)
    assert error.value.__cause__ is None and error.value.__suppress_context__


def test_404_no_se_reintenta():
    api, _, esperas = cliente([RespuestaFalsa(404, {"message": "Not Found", "url": "repo-secreto"})])
    with pytest.raises(ErrorGitHub) as error:
        api.leer_archivo("dueno", "repo-secreto", "BITACORA.md")
    assert error.value.tipo == "no_encontrado"
    assert str(error.value) == "no_encontrado (HTTP 404)"
    assert esperas == []


def test_401_token_invalido():
    api, _, _ = cliente([RespuestaFalsa(401)])
    with pytest.raises(ErrorGitHub) as error:
        api.listar_repos()
    assert error.value.tipo == "token_invalido"


def test_errores_graphql_son_falla():
    api, _, _ = cliente([RespuestaFalsa(200, {"data": None, "errors": [{"message": "repo-secreto"}]})])
    with pytest.raises(ErrorGitHub) as error:
        api.listar_repos()
    assert "repo-secreto" not in str(error.value)


def test_leer_archivo_devuelve_bytes_raw():
    api, sesion, _ = cliente([RespuestaFalsa(200, contenido=b"\x89PNG...")])
    assert api.leer_archivo("dueno", "repo", "docs/a.png") == b"\x89PNG..."
    assert sesion.pedidos[0]["headers"]["Accept"] == "application/vnd.github.raw+json"
    assert sesion.pedidos[0]["url"].endswith("/repos/dueno/repo/contents/docs/a.png")


def test_fecha_de_vencimiento():
    assert fecha_de_vencimiento("2027-01-02 03:04:05 -0300") == "2027-01-02"
    assert fecha_de_vencimiento(None) is None
    assert fecha_de_vencimiento("cualquier cosa") is None
