"""Armado de src/datos/proyectos.json (§4.2 pasos 4–10 y §4.3).

- Lista blanca: cada proyecto se arma campo por campo con lo que permite config/esquema_salida.json.
- Falla de un proyecto → queda su última versión publicada (buscada por clave opaca); si no tenía, no entra.
- Más de la mitad de los proyectos intentados fallan → falla total (sin escribir nada).
- Choque de slugs → el proyecto que lo introdujo vuelve a su versión anterior (o sale si es nuevo).
- Semilla (transitoria, Fase 2 → fin de Fase 3): proyectos de config/proyectos_semilla.json cuyo slug y clave
  no publicó ningún repo.
- Orden: destacados, activos, después ultima_actividad descendente (desempate por slug).
- Escritura determinística: claves ordenadas, sangría 2, UTF-8, sin fecha de generación; si el contenido no
  cambió, el archivo no se toca.
"""

import json

from portfolio import CARPETA_CONFIG, CARPETA_DATOS, CARPETA_PUBLIC
from portfolio.etiquetas import normalizar_lista

RUTA_PROYECTOS = CARPETA_DATOS / "proyectos.json"
RUTA_HUELLAS = CARPETA_DATOS / "huellas.json"
RUTA_SEMILLA = CARPETA_CONFIG / "proyectos_semilla.json"
CARPETA_IMAGENES = CARPETA_PUBLIC / "proyectos"
VERSION = 1


class ErrorFallaTotal(Exception):
    """La corrida no puede publicar: el job termina en rojo y sin commit."""

    def __init__(self, tipo, detalle=None):
        super().__init__(tipo)
        self.tipo = tipo
        self.detalle = detalle


# ------------------------------------------------------------------ advertencias


def advertencia(clave, nombre_publico, tipo, detalle=None):
    """Advertencia para el resumen, el issue y Telegram. `nombre_publico` es None en repos privados."""
    return {"clave": clave, "nombre": nombre_publico, "tipo": tipo, "detalle": detalle}


# ------------------------------------------------------------------ lectura y escritura


def leer_json(ruta, por_defecto=None):
    if not ruta.exists():
        return por_defecto
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


def json_estable(datos):
    return json.dumps(datos, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def escribir_si_cambio(ruta, texto):
    """Escribe solo si el contenido es distinto. Devuelve True si escribió."""
    if ruta.exists() and ruta.read_text(encoding="utf-8") == texto:
        return False
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="\n") as archivo:
        archivo.write(texto)
    return True


def proyectos_anteriores(ruta=RUTA_PROYECTOS):
    """dict clave → proyecto publicado (para §4.3)."""
    datos = leer_json(ruta, {"proyectos": []})
    anteriores = {}
    for proyecto in datos.get("proyectos", []):
        anteriores[proyecto["clave"]] = proyecto
    return anteriores


def leer_semilla(ruta=RUTA_SEMILLA):
    datos = leer_json(ruta, None)
    if datos is None:
        return []
    return list(datos.get("proyectos", []))


# ------------------------------------------------------------------ armado (lista blanca)


def links_de_salida(links, url_repo, es_privado):
    repo = None
    if links["repo"] == "auto" and not es_privado and url_repo:
        repo = url_repo
    otros = []
    for link in links["otros"]:
        otros.append({"texto": {"es": link["texto"]["es"], "en": link["texto"]["en"]}, "url": link["url"]})
    return {"demo": links["demo"], "repo": repo, "otros": otros}


def hitos_de_salida(hitos):
    es = []
    for hito in hitos["es"]:
        es.append({"fecha": hito["fecha"], "texto": hito["texto"], "tipo": hito["tipo"]})
    en = None
    if hitos["en"] is not None:
        en = []
        for hito in hitos["en"]:
            en.append({"fecha": hito["fecha"], "texto": hito["texto"], "tipo": hito["tipo"]})
    return {"es": es, "en": en}


def bitacora_de_salida(entradas):
    salida = []
    for entrada in entradas:
        salida.append({"fecha": entrada["fecha"], "titulo": entrada["titulo"]})
    return salida


def armar_proyecto(fuente, catalogo):
    """Proyecto de salida desde una fuente ya leída. Devuelve (proyecto, etiquetas fuera del catálogo).

    fuente: {"clave", "origen", "es_privado", "datos" (normalizado por archivo_estandar), "url_repo",
             "ultima_actividad", "imagen" (objeto de salida o None), "bitacora" (entradas fecha + título)}
    """
    datos = fuente["datos"]
    tecnologias, desconocidas_t = normalizar_lista(datos["tecnologias"], catalogo)
    servicios, desconocidas_s = normalizar_lista(datos["servicios"], catalogo)
    proyecto = {
        "clave": fuente["clave"],
        "origen": fuente["origen"],
        "es_privado": fuente["es_privado"],
        "slug": datos["slug"],
        "slugs_anteriores": list(datos["slugs_anteriores"]),
        "nombre": {"es": datos["nombre"]["es"], "en": datos["nombre"]["en"]},
        "descripcion": {"es": datos["descripcion"]["es"], "en": datos["descripcion"]["en"]},
        "estado": datos["estado"],
        "fecha_inicio": datos["fecha_inicio"],
        "fecha_fin": datos["fecha_fin"],
        "ultima_actividad": fuente["ultima_actividad"],
        "destacado": datos["destacado"],
        "tecnologias": tecnologias,
        "servicios": servicios,
        "links": links_de_salida(datos["links"], fuente.get("url_repo"), fuente["es_privado"]),
        "imagen": fuente.get("imagen"),
        "idea_original": {"es": datos["idea_original"]["es"], "en": datos["idea_original"]["en"]},
        "resultado": {"es": datos["resultado"]["es"], "en": datos["resultado"]["en"]},
        "hitos": hitos_de_salida(datos["hitos"]),
        "bitacora": bitacora_de_salida(fuente.get("bitacora") or []),
    }
    return proyecto, desconocidas_t + desconocidas_s


# ------------------------------------------------------------------ fallas (§4.3)


def resolver_resultados(resultados, anteriores):
    """resultados: [{"clave", "estado": "ok" | "fallo", "proyecto"?, "tipo"?, "detalle"?, "nombre_publico"}].

    Devuelve (proyectos, advertencias). Lanza ErrorFallaTotal si fallan más de la mitad de los intentados.
    Una falla simulada (input probar_alertas, "simulada": True) no cuenta para ese umbral.
    """
    if supera_umbral(resultados):
        fallidos, intentados = conteo_real(resultados)
        raise ErrorFallaTotal("mas_de_la_mitad_fallaron", str(fallidos) + " de " + str(intentados))
    proyectos = []
    advertencias = []
    for resultado in resultados:
        if resultado["estado"] == "ok":
            proyectos.append(resultado["proyecto"])
            continue
        clave = resultado["clave"]
        anterior = anteriores.get(clave)
        if anterior is not None:
            proyectos.append(anterior)
            detalle = "se mantiene la versión anterior"
        else:
            detalle = "proyecto nuevo: no entra"
        advertencias.append(
            advertencia(clave, resultado.get("nombre_publico"), resultado["tipo"], combinar(resultado.get("detalle"), detalle))
        )
    return proyectos, advertencias


def conteo_real(resultados):
    """(fallidos, intentados) sin contar las fallas simuladas."""
    fallidos = 0
    intentados = 0
    for resultado in resultados:
        if resultado.get("simulada"):
            continue
        intentados += 1
        if resultado["estado"] != "ok":
            fallidos += 1
    return fallidos, intentados


def supera_umbral(resultados):
    fallidos, intentados = conteo_real(resultados)
    return intentados > 0 and fallidos * 2 > intentados


def combinar(primero, segundo):
    if not primero:
        return segundo
    return primero + "; " + segundo


# ------------------------------------------------------------------ slugs


def slugs_de(proyecto):
    slugs = [proyecto["slug"]]
    for anterior in proyecto["slugs_anteriores"]:
        slugs.append(anterior)
    return slugs


def choques(proyectos):
    """Lista de pares (índice a, índice b) que comparten algún slug (actual o anterior)."""
    dueno = {}
    pares = []
    for indice, proyecto in enumerate(proyectos):
        for slug in slugs_de(proyecto):
            if slug in dueno and dueno[slug] != indice:
                pares.append((dueno[slug], indice))
            else:
                dueno[slug] = indice
    return pares


def introdujo_choque(proyecto, anteriores):
    """Un proyecto 'introduce' un choque si es nuevo o si sus slugs cambiaron respecto de lo publicado."""
    anterior = anteriores.get(proyecto["clave"])
    if anterior is None:
        return True
    return sorted(slugs_de(anterior)) != sorted(slugs_de(proyecto))


def resolver_slugs(proyectos, anteriores, nombres_publicos):
    """Revierte (o saca) a los proyectos que introdujeron un choque de slugs. Devuelve (proyectos, advertencias)."""
    proyectos = list(proyectos)
    advertencias = []
    for _ in range(len(proyectos) + 1):
        pares = choques(proyectos)
        if not pares:
            break
        culpables = set()
        for a, b in pares:
            for indice in (a, b):
                if introdujo_choque(proyectos[indice], anteriores):
                    culpables.add(indice)
            if a not in culpables and b not in culpables:
                culpables.add(b)
        nuevos = []
        for indice, proyecto in enumerate(proyectos):
            if indice not in culpables:
                nuevos.append(proyecto)
                continue
            clave = proyecto["clave"]
            anterior = anteriores.get(clave)
            detalle = "se mantiene la versión anterior" if anterior is not None else "proyecto nuevo: no entra"
            advertencias.append(advertencia(clave, nombres_publicos.get(clave), "slug_repetido", detalle))
            if anterior is not None and anterior is not proyecto:
                nuevos.append(anterior)
        proyectos = nuevos
    return proyectos, advertencias


# ------------------------------------------------------------------ semilla y orden


def sumar_semilla(proyectos, semilla):
    """Suma los proyectos de la semilla cuyo slug y clave no publicó ningún repo ni extra."""
    slugs = set()
    claves = set()
    for proyecto in proyectos:
        claves.add(proyecto["clave"])
        for slug in slugs_de(proyecto):
            slugs.add(slug)
    resultado = list(proyectos)
    for proyecto in semilla:
        if proyecto["clave"] in claves:
            continue
        ocupado = False
        for slug in slugs_de(proyecto):
            if slug in slugs:
                ocupado = True
        if ocupado:
            continue
        resultado.append(proyecto)
    return resultado


def clave_de_orden(proyecto):
    # sort ascendente: destacados (0) antes, activos (0) antes, después ultima_actividad descendente.
    mes = proyecto["ultima_actividad"]
    anio, numero = mes.split("-")
    mes_invertido = -(int(anio) * 12 + int(numero))
    return (
        0 if proyecto["destacado"] else 1,
        0 if proyecto["estado"] == "activo" else 1,
        mes_invertido,
        proyecto["slug"],
    )


def ordenar(proyectos):
    return sorted(proyectos, key=clave_de_orden)


# ------------------------------------------------------------------ imágenes publicadas


def archivos_referenciados(proyectos):
    nombres = set()
    for proyecto in proyectos:
        imagen = proyecto.get("imagen")
        if not imagen:
            continue
        for idioma in ("es", "en"):
            for ruta in imagen["archivos"][idioma].values():
                nombres.add(ruta.rsplit("/", 1)[-1])
    return nombres


def limpiar_imagenes(proyectos, carpeta=CARPETA_IMAGENES):
    """Borra de public/proyectos/ los WebP que ningún proyecto usa (proyecto quitado, slug cambiado…)."""
    if not carpeta.exists():
        return []
    usados = archivos_referenciados(proyectos)
    borrados = []
    for ruta in sorted(carpeta.glob("*.webp")):
        if ruta.name not in usados:
            ruta.unlink()
            borrados.append(ruta.name)
    return borrados


# ------------------------------------------------------------------ escritura


def archivo_de_proyectos(proyectos):
    return {"version": VERSION, "proyectos": proyectos}


def escribir_proyectos(proyectos, ruta=RUTA_PROYECTOS):
    return escribir_si_cambio(ruta, json_estable(archivo_de_proyectos(proyectos)))


def escribir_huellas(huellas, ruta=RUTA_HUELLAS):
    """huellas: dict clave → huella del origen de la captura manual (para no reprocesar)."""
    return escribir_si_cambio(ruta, json_estable(huellas))


def leer_huellas(ruta=RUTA_HUELLAS):
    return leer_json(ruta, {})
