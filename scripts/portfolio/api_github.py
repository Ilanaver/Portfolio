"""Cliente de la API de GitHub (§4.2): GraphQL para listar repos + PORTFOLIO.md, REST para el resto.

- Reintentos ante 5xx, 429, límite de uso (403 con x-ratelimit-remaining: 0 o límite secundario) y errores de
  red, con espera exponencial (o la que pida Retry-After, con tope).
- Lee el header `github-authentication-token-expiration` (vencimiento del token) de cualquier respuesta.
- Los errores salen como ErrorGitHub(tipo, código HTTP), NUNCA con el texto de la excepción original: las de
  requests incluyen la URL, que puede nombrar un repo privado.
"""

import time

import requests

URL_API = "https://api.github.com"
URL_GRAPHQL = URL_API + "/graphql"
VERSION_API = "2022-11-28"
TIEMPO_ESPERA = (10, 30)  # conexión, lectura (segundos)
REINTENTOS = 3
ESPERA_BASE = 2
ESPERA_MAXIMA = 60
REPOS_POR_PAGINA = 50

CONSULTA_REPOS = """
query($cursor: String) {
  viewer {
    login
    repositories(ownerAffiliations: OWNER, first: %d, after: $cursor, orderBy: {field: NAME, direction: ASC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        name
        isPrivate
        isArchived
        createdAt
        pushedAt
        url
        owner { login }
        archivo: object(expression: "HEAD:PORTFOLIO.md") {
          ... on Blob { text isBinary byteSize }
        }
      }
    }
  }
}
""" % REPOS_POR_PAGINA


class ErrorGitHub(Exception):
    """Error de la API por tipo y código. str() nunca incluye URLs ni texto de la respuesta."""

    def __init__(self, tipo, codigo=None):
        self.tipo = tipo
        self.codigo = codigo
        super().__init__(self.descripcion())

    def descripcion(self):
        if self.codigo is None:
            return self.tipo
        return self.tipo + " (HTTP " + str(self.codigo) + ")"


def tipo_por_codigo(codigo):
    if codigo == 401:
        return "token_invalido"
    if codigo == 404:
        return "no_encontrado"
    if codigo in (403, 429):
        return "sin_permiso_o_limite"
    if codigo >= 500:
        return "error_del_servidor"
    return "no_se_pudo_leer"


def es_limite_de_uso(respuesta):
    if respuesta.status_code == 429:
        return True
    if respuesta.status_code != 403:
        return False
    if respuesta.headers.get("x-ratelimit-remaining") == "0":
        return True
    return "secondary rate limit" in respuesta.text.lower()


def es_reintentable(respuesta):
    return respuesta.status_code >= 500 or es_limite_de_uso(respuesta)


def segundos_de_espera(respuesta, intento):
    espera = ESPERA_BASE * (2 ** intento)
    if respuesta is not None:
        pedido = respuesta.headers.get("retry-after")
        if pedido and pedido.isdigit():
            espera = int(pedido)
    return min(espera, ESPERA_MAXIMA)


def fecha_de_vencimiento(valor):
    """'2027-11-17 12:00:00 UTC' → '2027-11-17'. None si no viene o no se entiende."""
    if not valor or len(valor) < 10:
        return None
    fecha = valor[:10]
    if fecha[4] != "-" or fecha[7] != "-":
        return None
    return fecha


class ClienteGitHub:
    def __init__(self, token, sesion=None, dormir=time.sleep):
        self._sesion = sesion if sesion is not None else requests.Session()
        self._dormir = dormir
        self._encabezados = {
            "Authorization": "Bearer " + token,
            "X-GitHub-Api-Version": VERSION_API,
            "User-Agent": "portfolio-actualizar-datos",
        }
        self.vencimiento_token = None

    # ------------------------------------------------------------ base

    def _pedir(self, metodo, url, json=None, aceptar="application/vnd.github+json"):
        """Hace el pedido con reintentos. Devuelve la respuesta 2xx o lanza ErrorGitHub."""
        encabezados = dict(self._encabezados)
        encabezados["Accept"] = aceptar
        respuesta = None
        for intento in range(REINTENTOS + 1):
            try:
                respuesta = self._sesion.request(metodo, url, headers=encabezados, json=json, timeout=TIEMPO_ESPERA)
            except requests.Timeout:
                respuesta = None
                tipo_falla = "timeout"
            except requests.RequestException:
                respuesta = None
                tipo_falla = "error_de_red"
            else:
                self._anotar_vencimiento(respuesta)
                if respuesta.status_code < 400:
                    return respuesta
                if not es_reintentable(respuesta):
                    raise ErrorGitHub(tipo_por_codigo(respuesta.status_code), respuesta.status_code) from None
                tipo_falla = None
            if intento < REINTENTOS:
                self._dormir(segundos_de_espera(respuesta, intento))
        if respuesta is None:
            raise ErrorGitHub(tipo_falla) from None
        raise ErrorGitHub(tipo_por_codigo(respuesta.status_code), respuesta.status_code) from None

    def _anotar_vencimiento(self, respuesta):
        fecha = fecha_de_vencimiento(respuesta.headers.get("github-authentication-token-expiration"))
        if fecha:
            self.vencimiento_token = fecha

    def rest(self, metodo, ruta, json=None, aceptar="application/vnd.github+json"):
        """Pedido REST. `ruta` empieza con '/'. Devuelve el JSON (o None si no hay cuerpo)."""
        respuesta = self._pedir(metodo, URL_API + ruta, json=json, aceptar=aceptar)
        if not respuesta.content:
            return None
        try:
            return respuesta.json()
        except ValueError:
            raise ErrorGitHub("respuesta_invalida", respuesta.status_code) from None

    def graphql(self, consulta, variables):
        respuesta = self._pedir("POST", URL_GRAPHQL, json={"query": consulta, "variables": variables})
        try:
            cuerpo = respuesta.json()
        except ValueError:
            raise ErrorGitHub("respuesta_invalida", respuesta.status_code) from None
        if cuerpo.get("errors") or not cuerpo.get("data"):
            raise ErrorGitHub("error_graphql", respuesta.status_code)
        return cuerpo["data"]

    # ------------------------------------------------------------ operaciones

    def listar_repos(self):
        """Todos los repos del dueño del token con el texto de HEAD:PORTFOLIO.md (o None)."""
        repos = []
        cursor = None
        while True:
            datos = self.graphql(CONSULTA_REPOS, {"cursor": cursor})
            pagina = datos["viewer"]["repositories"]
            for nodo in pagina["nodes"]:
                repos.append(repo_desde_nodo(nodo))
            if not pagina["pageInfo"]["hasNextPage"]:
                break
            cursor = pagina["pageInfo"]["endCursor"]
        return repos

    def leer_archivo(self, dueno, repo, ruta):
        """Bytes de un archivo de la rama por defecto (bitácora, captura manual)."""
        ruta_api = "/repos/" + dueno + "/" + repo + "/contents/" + ruta
        respuesta = self._pedir("GET", URL_API + ruta_api, aceptar="application/vnd.github.raw+json")
        return respuesta.content


def repo_desde_nodo(nodo):
    archivo = nodo.get("archivo") or {}
    texto = None
    if archivo and not archivo.get("isBinary"):
        texto = archivo.get("text")
    return {
        "id": nodo["id"],
        "nombre": nodo["name"],
        "dueno": nodo["owner"]["login"],
        "es_privado": nodo["isPrivate"],
        "archivado": nodo["isArchived"],
        "creado": nodo["createdAt"],
        "ultimo_push": nodo["pushedAt"],
        "url": nodo["url"],
        "portfolio_md": texto,
    }
