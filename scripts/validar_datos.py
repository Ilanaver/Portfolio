"""Valida los datos del sitio antes de publicarlos.

Chequea:
1. src/datos/proyectos.json y src/datos/perfil.json contra config/esquema_salida.json (lista blanca).
2. Que src/i18n/es.json y src/i18n/en.json tengan exactamente las mismas claves.
3. Que ningún slug (actual o anterior) se repita entre proyectos, ni dentro de un mismo proyecto.
4. Que ninguna clave opaca se repita.

Uso: python -X utf8 scripts/validar_datos.py
Sale con código 1 si encuentra algún error.
"""

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

RAIZ = Path(__file__).resolve().parent.parent
RUTA_ESQUEMA = RAIZ / "config" / "esquema_salida.json"
RUTA_PROYECTOS = RAIZ / "src" / "datos" / "proyectos.json"
RUTA_PERFIL = RAIZ / "src" / "datos" / "perfil.json"
RUTA_ES = RAIZ / "src" / "i18n" / "es.json"
RUTA_EN = RAIZ / "src" / "i18n" / "en.json"


def leer_json(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


def validador_para(esquema, definicion):
    """Arma un validador que apunta a una definición de $defs del mismo esquema."""
    esquema_con_raiz = dict(esquema)
    esquema_con_raiz["$ref"] = "#/$defs/" + definicion
    return Draft202012Validator(esquema_con_raiz)


def ruta_legible(error):
    partes = []
    for parte in error.absolute_path:
        partes.append(str(parte))
    if not partes:
        return "(raíz)"
    return "/".join(partes)


def errores_de_esquema(esquema, definicion, datos, nombre_archivo):
    validador = validador_para(esquema, definicion)
    errores = []
    for error in sorted(validador.iter_errors(datos), key=lambda e: list(e.absolute_path)):
        errores.append(nombre_archivo + " → " + ruta_legible(error) + ": " + error.message)
    return errores


def claves_planas(diccionario, prefijo=""):
    """Devuelve el conjunto de claves 'a.b.c' de un diccionario anidado."""
    claves = set()
    for clave, valor in diccionario.items():
        clave_completa = prefijo + clave
        if isinstance(valor, dict):
            claves.update(claves_planas(valor, clave_completa + "."))
        else:
            claves.add(clave_completa)
    return claves


def errores_de_paridad(es, en):
    claves_es = claves_planas(es)
    claves_en = claves_planas(en)
    errores = []
    for clave in sorted(claves_es - claves_en):
        errores.append("i18n → falta en en.json: " + clave)
    for clave in sorted(claves_en - claves_es):
        errores.append("i18n → falta en es.json: " + clave)
    return errores


def slugs_de(proyecto):
    """Todos los slugs que ocupa un proyecto: el actual y los anteriores."""
    slugs = [proyecto.get("slug")]
    for anterior in proyecto.get("slugs_anteriores", []):
        slugs.append(anterior)
    return slugs


def errores_de_slugs(proyectos):
    errores = []
    dueno_de_slug = {}
    for proyecto in proyectos:
        clave = proyecto.get("clave", "?")
        vistos_en_este = set()
        for slug in slugs_de(proyecto):
            if slug in vistos_en_este:
                errores.append("slugs → " + clave + ": el slug '" + str(slug) + "' se repite en el mismo proyecto")
                continue
            vistos_en_este.add(slug)
            if slug in dueno_de_slug:
                errores.append(
                    "slugs → '" + str(slug) + "' lo usan " + dueno_de_slug[slug] + " y " + clave
                )
            else:
                dueno_de_slug[slug] = clave
    return errores


def errores_de_claves_opacas(proyectos):
    errores = []
    vistas = set()
    for proyecto in proyectos:
        clave = proyecto.get("clave")
        if clave in vistas:
            errores.append("claves → la clave opaca '" + str(clave) + "' se repite")
        vistas.add(clave)
    return errores


def main():
    esquema = leer_json(RUTA_ESQUEMA)
    datos_proyectos = leer_json(RUTA_PROYECTOS)
    datos_perfil = leer_json(RUTA_PERFIL)

    errores = []
    errores.extend(errores_de_esquema(esquema, "archivo_proyectos", datos_proyectos, "proyectos.json"))
    errores.extend(errores_de_esquema(esquema, "archivo_perfil", datos_perfil, "perfil.json"))
    errores.extend(errores_de_paridad(leer_json(RUTA_ES), leer_json(RUTA_EN)))

    proyectos = datos_proyectos.get("proyectos", [])
    if isinstance(proyectos, list):
        errores.extend(errores_de_slugs(proyectos))
        errores.extend(errores_de_claves_opacas(proyectos))

    if errores:
        print("validar_datos: " + str(len(errores)) + " error(es)")
        for error in errores:
            print("  - " + error)
        return 1

    print("validar_datos: OK (" + str(len(proyectos)) + " proyectos, i18n con las mismas claves)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
