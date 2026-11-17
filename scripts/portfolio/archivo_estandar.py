"""Lectura y validación del archivo estándar PORTFOLIO.md (§2.1) y de los proyectos sin repo (§2.5).

Entrada: el texto del archivo + un contexto (repo o extra, privado o no, nombre del repo, fecha de creación).
Salida: un diccionario normalizado con los defaults aplicados y los textos en pares {es, en}, más una lista de
advertencias por TIPO (sin texto leído del repo: así se pueden imprimir aunque el repo sea privado).

Errores: ErrorArchivoEstandar con tipo "no_valida". Sus `detalles` sí pueden citar campos y valores: solo se
muestran en auditar_repos.py (local) o para repos públicos; nunca en logs de repos privados.
"""

import datetime
import json
import re

import yaml
from jsonschema import Draft202012Validator

from portfolio import CARPETA_CONFIG

RUTA_ESQUEMA = CARPETA_CONFIG / "esquema_portfolio.json"

# Secciones reconocidas del cuerpo: título exacto → (clave interna, idioma).
SECCIONES = {
    "Idea original": ("idea_original", "es"),
    "Original idea": ("idea_original", "en"),
    "Resultado": ("resultado", "es"),
    "Outcome": ("resultado", "en"),
    "Hitos": ("hitos", "es"),
    "Milestones": ("hitos", "en"),
}

# Largos orientativos del plan (§2.1): pasarse es advertencia, no error.
LARGO_SUGERIDO = {"idea_original": 600, "resultado": 900}
LARGO_SUGERIDO_ARREGLO = 220
LARGO_MAXIMO_HITO = 300
MAXIMO_HITOS = 60

MARCAS_ARREGLO = ("[arreglo]", "[fix]")
PATRON_HITO = re.compile(r"^\s*[-*]\s+(\d{4}-\d{2}-\d{2})\s+[—–-]\s+(.+?)\s*$")
PATRON_TITULO_SECCION = re.compile(r"^##\s+(.+?)\s*#*\s*$")
PATRON_COMENTARIO_HTML = re.compile(r"<!--.*?-->", re.DOTALL)
PATRON_SLUG = re.compile(r"^[a-z0-9-]+$")

MAX_ENTRADAS_BITACORA = 10
ARCHIVO_BITACORA = "BITACORA.md"


class ErrorArchivoEstandar(Exception):
    """El archivo no se pudo leer o no valida. `tipo` es apto para logs; `detalles` no siempre."""

    def __init__(self, tipo, detalles):
        super().__init__(tipo)
        self.tipo = tipo
        self.detalles = detalles


# ---------------------------------------------------------------- YAML


class CargadorSinFechas(yaml.SafeLoader):
    """SafeLoader que deja las fechas como texto (sin esto, 2026-10-17 llega como datetime.date)."""


def _quitar_resolvedor_de_fechas():
    resolvedores_nuevos = {}
    for inicial, lista in yaml.SafeLoader.yaml_implicit_resolvers.items():
        filtrados = []
        for etiqueta, patron in lista:
            if etiqueta != "tag:yaml.org,2002:timestamp":
                filtrados.append((etiqueta, patron))
        resolvedores_nuevos[inicial] = filtrados
    CargadorSinFechas.yaml_implicit_resolvers = resolvedores_nuevos


_quitar_resolvedor_de_fechas()


def separar_frontmatter(texto):
    """Devuelve (texto YAML, cuerpo). El archivo tiene que empezar con una línea '---'."""
    texto = texto.lstrip("﻿").replace("\r\n", "\n")
    lineas = texto.split("\n")
    if not lineas or lineas[0].strip() != "---":
        raise ErrorArchivoEstandar("no_valida", ["falta el frontmatter: la primera línea tiene que ser '---'"])
    for indice in range(1, len(lineas)):
        if lineas[indice].strip() == "---":
            yaml_texto = "\n".join(lineas[1:indice])
            cuerpo = "\n".join(lineas[indice + 1:])
            return yaml_texto, cuerpo
    raise ErrorArchivoEstandar("no_valida", ["el frontmatter no se cierra con '---'"])


def cargar_yaml(yaml_texto):
    try:
        datos = yaml.load(yaml_texto, Loader=CargadorSinFechas)
    except yaml.YAMLError as error:
        marca = getattr(error, "problem_mark", None)
        donde = ""
        if marca is not None:
            donde = " (línea " + str(marca.line + 2) + ")"
        raise ErrorArchivoEstandar("no_valida", ["YAML inválido" + donde]) from None
    if not isinstance(datos, dict):
        raise ErrorArchivoEstandar("no_valida", ["el frontmatter no es un mapa de campos"])
    return datos


# ---------------------------------------------------------------- esquema

_validadores = {}


def validador_de(definicion):
    if definicion not in _validadores:
        with open(RUTA_ESQUEMA, encoding="utf-8") as archivo:
            esquema = json.load(archivo)
        esquema["$ref"] = "#/$defs/" + definicion
        _validadores[definicion] = Draft202012Validator(esquema)
    return _validadores[definicion]


def errores_de_esquema(datos, definicion):
    errores = []
    for error in validador_de(definicion).iter_errors(datos):
        partes = []
        for parte in error.absolute_path:
            partes.append(str(parte))
        ruta = "/".join(partes) if partes else "(raíz)"
        errores.append(ruta + ": " + error.message)
    errores.sort()
    return errores


# ---------------------------------------------------------------- cuerpo


def limpiar_parrafos(texto):
    """Quita comentarios HTML, une las líneas de cada párrafo y separa párrafos con una línea en blanco."""
    texto = PATRON_COMENTARIO_HTML.sub("", texto)
    parrafos = []
    actual = []
    for linea in texto.split("\n"):
        limpia = linea.strip()
        if limpia:
            actual.append(limpia)
        elif actual:
            parrafos.append(" ".join(actual))
            actual = []
    if actual:
        parrafos.append(" ".join(actual))
    return "\n\n".join(parrafos)


def secciones_del_cuerpo(cuerpo):
    """Divide el cuerpo en secciones '## Título'. Devuelve (dict título → texto crudo, títulos repetidos)."""
    secciones = {}
    repetidos = []
    titulo_actual = None
    lineas_actuales = []
    for linea in cuerpo.split("\n"):
        coincidencia = PATRON_TITULO_SECCION.match(linea)
        if coincidencia and not linea.startswith("###"):
            if titulo_actual is not None:
                _guardar_seccion(secciones, repetidos, titulo_actual, lineas_actuales)
            titulo_actual = coincidencia.group(1).strip()
            lineas_actuales = []
        elif titulo_actual is not None:
            lineas_actuales.append(linea)
    if titulo_actual is not None:
        _guardar_seccion(secciones, repetidos, titulo_actual, lineas_actuales)
    return secciones, repetidos


def _guardar_seccion(secciones, repetidos, titulo, lineas):
    if titulo in secciones:
        repetidos.append(titulo)
        return
    secciones[titulo] = "\n".join(lineas)


def es_fecha_valida(texto):
    try:
        datetime.date.fromisoformat(texto)
    except ValueError:
        return False
    return True


def parsear_hitos(texto_seccion, nombre_seccion):
    """Líneas '- AAAA-MM-DD — texto'. Devuelve (hitos más nuevos primero, errores, advertencias)."""
    hitos = []
    errores = []
    advertencias = []
    texto_seccion = PATRON_COMENTARIO_HTML.sub("", texto_seccion)
    numero = 0
    for linea in texto_seccion.split("\n"):
        if not linea.strip():
            continue
        numero += 1
        coincidencia = PATRON_HITO.match(linea)
        if not coincidencia or not es_fecha_valida(coincidencia.group(1)):
            errores.append(nombre_seccion + ": la línea " + str(numero) + " no tiene la forma '- AAAA-MM-DD — texto'")
            continue
        hito = hito_desde_texto(coincidencia.group(1), coincidencia.group(2))
        if len(hito["texto"]) == 0:
            errores.append(nombre_seccion + ": la línea " + str(numero) + " no tiene texto")
            continue
        if len(hito["texto"]) > LARGO_MAXIMO_HITO:
            errores.append(nombre_seccion + ": la línea " + str(numero) + " supera " + str(LARGO_MAXIMO_HITO) + " caracteres")
            continue
        if hito["tipo"] == "arreglo" and len(hito["texto"]) > LARGO_SUGERIDO_ARREGLO:
            advertencias.append("arreglo_largo")
        hitos.append(hito)
    if len(hitos) > MAXIMO_HITOS:
        errores.append(nombre_seccion + ": más de " + str(MAXIMO_HITOS) + " hitos")
    # Más nuevos primero; sort es estable, así que el mismo día conserva el orden del archivo.
    hitos.sort(key=lambda hito: hito["fecha"], reverse=True)
    return hitos, errores, advertencias


def hito_desde_texto(fecha, texto):
    tipo = "hito"
    minusculas = texto.lower()
    for marca in MARCAS_ARREGLO:
        if minusculas.startswith(marca):
            tipo = "arreglo"
            texto = texto[len(marca):].strip()
            break
    return {"fecha": fecha, "texto": texto, "tipo": tipo}


# ---------------------------------------------------------------- defaults


def slug_desde_nombre_repo(nombre_repo):
    """Default del slug: nombre del repo en minúsculas, con lo que no sea [a-z0-9] convertido en guiones."""
    slug = re.sub(r"[^a-z0-9]+", "-", nombre_repo.lower()).strip("-")
    return slug


def texto_es_en(es, en):
    return {"es": es, "en": en}


def links_otros(lista):
    resultado = []
    for link in lista or []:
        resultado.append({"texto": texto_es_en(link["texto"], link.get("texto_en")), "url": link["url"]})
    return resultado


def captura_auto_efectiva(datos, es_privado):
    """§2.1: default true en públicos y extras, false en privados; un valor explícito siempre gana."""
    if "captura_auto" in datos:
        return bool(datos["captura_auto"])
    return not es_privado


def imagen_normalizada(imagen):
    if not imagen:
        return None
    return {
        "archivo": imagen["archivo"],
        "alt": texto_es_en(imagen["alt"], imagen.get("alt_en")),
        "aprobada": imagen.get("aprobada"),
    }


def bitacora_normalizada(datos):
    bitacora = datos.get("bitacora") or {}
    return {
        "archivo": bitacora.get("archivo", ARCHIVO_BITACORA),
        "max_entradas": bitacora.get("max_entradas", MAX_ENTRADAS_BITACORA),
    }


# ---------------------------------------------------------------- advertencias de inglés


def advertencias_de_ingles(datos, textos):
    """Tipos de inglés faltante (§2.1: es advertencia, no error)."""
    faltantes = []
    if "descripcion_en" not in datos:
        faltantes.append("descripcion_en")
    if textos["idea_original"]["en"] is None:
        faltantes.append("original_idea")
    if textos["resultado"]["en"] is None:
        faltantes.append("outcome")
    if textos["hitos"]["es"] and textos["hitos"]["en"] is None:
        faltantes.append("milestones")
    imagen = datos.get("imagen")
    if imagen and "alt_en" not in imagen:
        faltantes.append("imagen_alt_en")
    links = datos.get("links") or {}
    for link in links.get("otros") or []:
        if "texto_en" not in link:
            faltantes.append("link_texto_en")
            break
    resultado = []
    for campo in faltantes:
        resultado.append("falta_ingles:" + campo)
    return resultado


# ---------------------------------------------------------------- armado


def textos_del_cuerpo(cuerpo):
    """Lee las secciones reconocidas. Devuelve (textos, errores, advertencias)."""
    secciones, repetidos = secciones_del_cuerpo(cuerpo)
    errores = []
    advertencias = []
    for titulo in repetidos:
        if titulo in SECCIONES:
            advertencias.append("seccion_repetida")
    textos = {
        "idea_original": {"es": None, "en": None},
        "resultado": {"es": None, "en": None},
        "hitos": {"es": [], "en": None},
    }
    for titulo, (clave, idioma) in SECCIONES.items():
        if titulo not in secciones:
            continue
        crudo = secciones[titulo]
        if clave == "hitos":
            hitos, errores_hitos, advertencias_hitos = parsear_hitos(crudo, titulo)
            errores.extend(errores_hitos)
            advertencias.extend(advertencias_hitos)
            if idioma == "es" or hitos:
                textos["hitos"][idioma] = hitos
            continue
        limpio = limpiar_parrafos(crudo)
        if limpio:
            textos[clave][idioma] = limpio
            if len(limpio) > LARGO_SUGERIDO[clave]:
                advertencias.append(clave + "_largo")
    if textos["idea_original"]["es"] is None:
        errores.append("falta la sección '## Idea original' (o está vacía)")
    if textos["resultado"]["es"] is None:
        errores.append("falta la sección '## Resultado' (o está vacía)")
    return textos, errores, advertencias


def errores_de_contexto(datos, slug):
    errores = []
    if slug in (datos.get("slugs_anteriores") or []):
        errores.append("slugs_anteriores incluye el slug actual '" + slug + "'")
    if not slug or not PATRON_SLUG.match(slug) or len(slug) > 60:
        errores.append("no se pudo armar un slug válido: definí 'slug' en el frontmatter")
    return errores


def leer_archivo_estandar(texto, contexto):
    """Parsea y valida un PORTFOLIO.md o un proyecto extra.

    contexto: {"tipo": "repo" | "extra", "es_privado": bool, "nombre_repo": str | None,
               "creado": "AAAA-MM-DD..." | None}
    Devuelve {"datos": dict normalizado, "advertencias": [tipos]}.
    Lanza ErrorArchivoEstandar si no valida.
    """
    yaml_texto, cuerpo = separar_frontmatter(texto)
    datos = cargar_yaml(yaml_texto)

    definicion = "proyecto_extra" if contexto["tipo"] == "extra" else "portfolio_repo"
    errores = errores_de_esquema(datos, definicion)
    if errores:
        raise ErrorArchivoEstandar("no_valida", errores)

    textos, errores_cuerpo, advertencias = textos_del_cuerpo(cuerpo)
    es_privado = bool(contexto.get("es_privado"))
    slug = datos.get("slug") or slug_desde_nombre_repo(contexto.get("nombre_repo") or "")
    errores = errores_cuerpo + errores_de_contexto(datos, slug)
    if errores:
        raise ErrorArchivoEstandar("no_valida", errores)

    fecha_inicio = datos.get("fecha_inicio")
    if fecha_inicio is None and contexto.get("creado"):
        fecha_inicio = contexto["creado"][:10]
    if fecha_inicio is None:
        raise ErrorArchivoEstandar("no_valida", ["falta fecha_inicio y no hay fecha de creación del repo"])

    links = datos.get("links") or {}
    repo_link = links.get("repo", "auto")
    if es_privado or contexto["tipo"] == "extra":
        repo_link = None

    normalizado = {
        "visible": datos["visible"],
        "mostrar_bitacora": datos["mostrar_bitacora"] and contexto["tipo"] == "repo",
        "nombre": texto_es_en(datos["nombre"], datos.get("nombre_en", datos["nombre"])),
        "slug": slug,
        "slugs_anteriores": list(datos.get("slugs_anteriores") or []),
        "descripcion": texto_es_en(datos["descripcion"], datos.get("descripcion_en")),
        "estado": datos["estado"],
        "fecha_inicio": fecha_inicio,
        "fecha_fin": datos.get("fecha_fin"),
        "ultima_actividad": datos.get("ultima_actividad"),
        "destacado": bool(datos.get("destacado", False)),
        "tecnologias": list(datos["tecnologias"]),
        "servicios": list(datos.get("servicios") or []),
        "links": {"demo": links.get("demo"), "repo": repo_link, "otros": links_otros(links.get("otros"))},
        "captura_auto": captura_auto_efectiva(datos, es_privado),
        "imagen": imagen_normalizada(datos.get("imagen")),
        "bitacora": bitacora_normalizada(datos),
        "idea_original": textos["idea_original"],
        "resultado": textos["resultado"],
        "hitos": textos["hitos"],
    }
    advertencias = advertencias + advertencias_de_ingles(datos, textos)
    return {"datos": normalizado, "advertencias": advertencias}
