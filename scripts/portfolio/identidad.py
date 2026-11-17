"""Claves opacas y filtro de redacción (§4.4).

Clave opaca: prefijo + los primeros 8 caracteres de sha256(id de nodo de GitHub).
- Repo privado → 'priv-xxxxxxxx'. Es lo ÚNICO con lo que se nombra un privado fuera del sitio.
- Repo público → 'pub-xxxxxxxx'. Mismo cálculo: la clave no cambia si el repo se renombra (el id de nodo se
  mantiene), así §4.3 encuentra su versión anterior aunque cambie el nombre o el slug.
- Proyecto sin repo → 'extra-<slug>'.

Red de seguridad: todo lo que los scripts imprimen o envían (logs, resumen, issues, Telegram) pasa por
Redactor.redactar(), que reemplaza cualquier nombre de repo privado (y sus textos registrados) por su clave,
y tapa tokens con forma conocida.
"""

import hashlib
import re
import sys
import traceback

PREFIJO_PRIVADO = "priv-"
PREFIJO_PUBLICO = "pub-"
PREFIJO_EXTRA = "extra-"

# Formas de secretos que nunca tienen que salir, aunque nadie los haya registrado.
PATRONES_SECRETOS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{30,}\b"),  # token de bot de Telegram
    re.compile(r"(?i)(authorization:\s*)(?:bearer|token)\s+\S+"),
]
SECRETO_TAPADO = "[secreto]"

# Textos más cortos que esto no se registran como sensibles (evita tapar palabras comunes de 1–3 letras).
LARGO_MINIMO_REGISTRABLE = 4


def hash_corto(id_nodo):
    return hashlib.sha256(id_nodo.encode("utf-8")).hexdigest()[:8]


def clave_opaca(id_nodo, es_privado):
    prefijo = PREFIJO_PRIVADO if es_privado else PREFIJO_PUBLICO
    return prefijo + hash_corto(id_nodo)


def clave_extra(slug):
    return PREFIJO_EXTRA + slug


def es_clave_privada(clave):
    return clave.startswith(PREFIJO_PRIVADO)


class Redactor:
    """Reemplaza textos sensibles registrados por su clave opaca."""

    def __init__(self):
        self._reemplazos = {}
        self._patron = None

    def registrar(self, texto, clave):
        """Registra un texto sensible (nombre de repo privado, su slug, nombre, URL de demo…)."""
        if texto is None:
            return
        texto = str(texto).strip()
        if len(texto) < LARGO_MINIMO_REGISTRABLE:
            return
        self._reemplazos[texto.lower()] = clave
        self._patron = None

    def registrar_repo_privado(self, nombre_repo, clave, dueno=None):
        self.registrar(nombre_repo, clave)
        if dueno:
            self.registrar(dueno + "/" + nombre_repo, clave)

    def registrar_proyecto_privado(self, datos, clave):
        """Registra los textos identificables de un PORTFOLIO.md privado ya parseado."""
        self.registrar(datos.get("slug"), clave)
        nombre = datos.get("nombre") or {}
        self.registrar(nombre.get("es"), clave)
        self.registrar(nombre.get("en"), clave)
        links = datos.get("links") or {}
        self.registrar(links.get("demo"), clave)
        for anterior in datos.get("slugs_anteriores") or []:
            self.registrar(anterior, clave)

    def _patron_compilado(self):
        if self._patron is None and self._reemplazos:
            # Los más largos primero: 'mi-app-v2' se tapa entero antes que 'mi-app'.
            textos = sorted(self._reemplazos.keys(), key=len, reverse=True)
            partes = []
            for texto in textos:
                partes.append(re.escape(texto))
            self._patron = re.compile("|".join(partes), re.IGNORECASE)
        return self._patron

    def redactar(self, texto):
        texto = str(texto)
        for patron in PATRONES_SECRETOS:
            texto = patron.sub(_tapar_secreto, texto)
        patron = self._patron_compilado()
        if patron is None:
            return texto
        return patron.sub(self._reemplazo_de, texto)

    def _reemplazo_de(self, coincidencia):
        return self._reemplazos[coincidencia.group(0).lower()]


def _tapar_secreto(coincidencia):
    if coincidencia.re.groups:
        return coincidencia.group(1) + SECRETO_TAPADO
    return SECRETO_TAPADO


# Redactor global del proceso: lo usan imprimir(), el resumen, las alertas y Telegram.
REDACTOR = Redactor()


def imprimir(texto, salida=None):
    """print() con redacción. Usar SIEMPRE esto en los scripts del Action, nunca print() directo."""
    destino = salida if salida is not None else sys.stdout
    destino.write(REDACTOR.redactar(texto) + "\n")
    destino.flush()


def _gancho_de_excepciones(tipo, valor, rastro):
    """Tracebacks no previstos: se imprimen redactados (los de requests y Playwright incluyen URLs)."""
    texto = "".join(traceback.format_exception(tipo, valor, rastro))
    sys.stderr.write(REDACTOR.redactar(texto))
    sys.stderr.flush()


def instalar_gancho_de_excepciones():
    sys.excepthook = _gancho_de_excepciones
