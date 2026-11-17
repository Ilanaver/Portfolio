"""Normalización de tecnologías y servicios con config/etiquetas.yml (§2.6)."""

import yaml

from portfolio import CARPETA_CONFIG

RUTA_CATALOGO = CARPETA_CONFIG / "etiquetas.yml"
CATEGORIAS = ("lenguaje", "frontend", "backend", "datos", "infra", "automatizacion", "mensajeria", "ia")


class ErrorCatalogo(Exception):
    pass


def clave_de(texto):
    """Clave de comparación: minúsculas y espacios simples."""
    return " ".join(str(texto).lower().split())


def cargar_catalogo(ruta=RUTA_CATALOGO):
    """Devuelve dict clave normalizada (nombre o alias) → {"nombre", "categoria"}. Valida el catálogo."""
    with open(ruta, encoding="utf-8") as archivo:
        crudo = yaml.safe_load(archivo) or {}
    catalogo = {}
    for nombre, definicion in crudo.items():
        nombre = str(nombre)
        definicion = definicion or {}
        categoria = definicion.get("categoria")
        if categoria is not None and categoria not in CATEGORIAS:
            raise ErrorCatalogo("categoría desconocida en '" + nombre + "': " + str(categoria))
        etiqueta = {"nombre": nombre, "categoria": categoria}
        claves = [nombre]
        for alias in definicion.get("alias") or []:
            claves.append(alias)
        for clave in claves:
            normalizada = clave_de(clave)
            if normalizada in catalogo:
                raise ErrorCatalogo("el nombre o alias '" + str(clave) + "' aparece dos veces")
            catalogo[normalizada] = etiqueta
    return catalogo


def normalizar(texto, catalogo):
    """Devuelve ({"nombre", "categoria"}, conocida). Fuera del catálogo: tal cual y sin categoría."""
    etiqueta = catalogo.get(clave_de(texto))
    if etiqueta is not None:
        return {"nombre": etiqueta["nombre"], "categoria": etiqueta["categoria"]}, True
    return {"nombre": " ".join(str(texto).split()), "categoria": None}, False


def normalizar_lista(textos, catalogo):
    """Normaliza una lista sin repetir nombres canónicos. Devuelve (etiquetas, nombres fuera del catálogo)."""
    etiquetas = []
    vistas = set()
    desconocidas = []
    for texto in textos:
        etiqueta, conocida = normalizar(texto, catalogo)
        if not conocida:
            desconocidas.append(etiqueta["nombre"])
        clave = clave_de(etiqueta["nombre"])
        if clave in vistas:
            continue
        vistas.add(clave)
        etiquetas.append(etiqueta)
    return etiquetas, desconocidas
