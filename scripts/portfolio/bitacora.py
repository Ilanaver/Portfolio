"""Bitácoras (§3.3): SOLO encabezados → fecha + título. El cuerpo de las entradas nunca se lee para publicar.

Formatos soportados:
- Único (nuevo):     ## DD/MM/AAAA — Título
- A (formato viejo):   ## DD/MM/AAAA (día)          → sin título: no se publica
- B (formato viejo):   ## AAAA-MM-DD — Título
- C (formato viejo):   ### AAAA-MM-DD — Título
Entrada = '##' o '###' que empieza con una fecha válida. Los títulos sin fecha se ignoran.
"""

import datetime
import re

LARGO_MAXIMO_TITULO = 100

PATRON_ENCABEZADO = re.compile(r"^(#{2,3})\s+(.*)$")
PATRON_FECHA_DMA = re.compile(r"^(\d{2})/(\d{2})/(\d{4})(.*)$")
PATRON_FECHA_AMD = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(.*)$")
PATRON_SEPARADOR_TITULO = re.compile(r"^\s*[—–]\s*(.*)$")
PATRON_LINK_MD = re.compile(r"\[([^\]]*)\]\([^)]*\)")
PATRON_FORMATO_MD = re.compile(r"(\*\*|__|\*|_|`|~~)")


def fecha_iso(anio, mes, dia):
    """Devuelve 'AAAA-MM-DD' si la fecha existe, si no None."""
    try:
        return datetime.date(int(anio), int(mes), int(dia)).isoformat()
    except ValueError:
        return None


def separar_fecha(texto):
    """Del texto de un encabezado saca (fecha ISO, resto) o (None, None) si no empieza con fecha."""
    coincidencia = PATRON_FECHA_DMA.match(texto)
    if coincidencia:
        dia, mes, anio, resto = coincidencia.groups()
        return fecha_iso(anio, mes, dia), resto
    coincidencia = PATRON_FECHA_AMD.match(texto)
    if coincidencia:
        anio, mes, dia, resto = coincidencia.groups()
        return fecha_iso(anio, mes, dia), resto
    return None, None


def limpiar_titulo(texto):
    """Solo quita el formato Markdown y recorta a 100 caracteres. No 'limpia' contenido (§3.3)."""
    texto = PATRON_LINK_MD.sub(r"\1", texto)
    texto = PATRON_FORMATO_MD.sub("", texto)
    texto = " ".join(texto.split())
    if len(texto) > LARGO_MAXIMO_TITULO:
        texto = texto[:LARGO_MAXIMO_TITULO - 1].rstrip() + "…"
    return texto


def titulo_desde_resto(resto):
    coincidencia = PATRON_SEPARADOR_TITULO.match(resto)
    if not coincidencia:
        return None
    titulo = limpiar_titulo(coincidencia.group(1))
    if not titulo:
        return None
    return titulo


def encabezados(texto):
    """Genera los textos de los encabezados ## y ### fuera de bloques de código. No mira el cuerpo."""
    dentro_de_codigo = False
    for linea in texto.replace("\r\n", "\n").split("\n"):
        if linea.lstrip().startswith("```"):
            dentro_de_codigo = not dentro_de_codigo
            continue
        if dentro_de_codigo:
            continue
        coincidencia = PATRON_ENCABEZADO.match(linea)
        if coincidencia:
            yield coincidencia.group(2).strip()


def leer_bitacora(texto, max_entradas):
    """Devuelve {"entradas": [{fecha, titulo}] más nuevas primero (hasta max_entradas), "advertencias": [...]}."""
    entradas = []
    con_fecha = 0
    for encabezado in encabezados(texto):
        fecha, resto = separar_fecha(encabezado)
        if fecha is None:
            continue
        con_fecha += 1
        titulo = titulo_desde_resto(resto)
        if titulo is None:
            continue
        entradas.append({"fecha": fecha, "titulo": titulo})
    entradas.sort(key=lambda entrada: entrada["fecha"], reverse=True)
    advertencias = []
    if not entradas:
        advertencias.append("bitacora_sin_titulos")
    return {"entradas": entradas[:max_entradas], "advertencias": advertencias, "con_fecha": con_fecha}
