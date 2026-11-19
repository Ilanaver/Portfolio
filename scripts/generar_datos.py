"""Entrada del Action `actualizar-datos` (§4.2 paso 2): arma src/datos/proyectos.json y src/datos/perfil.json.

Uso:
  python -X utf8 scripts/generar_datos.py [--evento schedule|workflow_dispatch|push|local]
                                          [--capturas si|no] [--probar-alertas no|falla_total|falla_repo]
                                          [--estado RUTA]
Variables de entorno:
  GH_TOKEN_LECTURA  token fine-grained de SOLO LECTURA (obligatorio)
  TOKEN_VENCE       AAAA-MM-DD, respaldo si la API no manda el vencimiento
  GITHUB_STEP_SUMMARY (la pone Actions) resumen de la corrida en Markdown

Salida: código 0 si se publicó (con o sin advertencias), 1 si fue falla total (no se escribe nada).
En --estado deja un JSON con el resultado para alertas.py (§4.5). Todo lo que imprime pasa por el filtro de
redacción: los repos privados se nombran solo por su clave opaca.
"""

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

from portfolio import CARPETA_CONFIG, CARPETA_DATOS, CARPETA_PUBLIC
from portfolio.api_github import ClienteGitHub, ErrorGitHub
from portfolio.archivo_estandar import ErrorArchivoEstandar, leer_archivo_estandar
from portfolio.bitacora import leer_bitacora
from portfolio.capturas_auto import ErrorCaptura, abrir_navegador, capturar_proyecto, cargar_config
from portfolio.etiquetas import cargar_catalogo
from portfolio.identidad import REDACTOR, clave_opaca, imprimir, instalar_gancho_de_excepciones
from portfolio.imagenes import ErrorImagen, procesar_imagen_manual
from portfolio.perfil import armar_perfil, escribir_perfil
from portfolio.proyectos_extra import leer_extra, leer_imagen_extra, listar_archivos
from portfolio.salida import (
    ErrorFallaTotal,
    advertencia,
    armar_proyecto,
    escribir_huellas,
    escribir_proyectos,
    leer_huellas,
    limpiar_imagenes,
    ordenar,
    proyectos_anteriores,
    resolver_resultados,
    resolver_slugs,
)

import validar_datos

RUTAS_POR_DEFECTO = {
    "proyectos": CARPETA_DATOS / "proyectos.json",
    "perfil": CARPETA_DATOS / "perfil.json",
    "huellas": CARPETA_DATOS / "huellas.json",
    "imagenes": CARPETA_PUBLIC / "proyectos",
    "cv": CARPETA_PUBLIC / "cv",
    "extras": CARPETA_CONFIG / "proyectos_extra",
    "perfil_yml": CARPETA_CONFIG / "perfil.yml",
    "esquema_salida": CARPETA_CONFIG / "esquema_salida.json",
}

# Tipos que van al issue de advertencias (§4.5). El resto (inglés faltante, etiquetas fuera del catálogo,
# bitácora sin títulos) va solo al resumen de la corrida.
TIPOS_PARA_ISSUE = {
    "no_se_pudo_leer", "no_valida", "bitacora_no_disponible", "imagen_sin_aprobar", "imagen_invalida",
    "captura_auto_fallida", "slug_repetido", "timeout", "prueba_falla_repo", "cv_pdf_fallido",
}


class Corrida:
    """Acumula advertencias y avisos de la corrida."""

    def __init__(self):
        self.advertencias = []
        self.avisos = []

    def advertir(self, clave, nombre_publico, tipo, detalle=None):
        destino = self.advertencias if tipo in TIPOS_PARA_ISSUE else self.avisos
        destino.append(advertencia(clave, nombre_publico, tipo, detalle))


# ------------------------------------------------------------------ helpers


def nombre_en_logs(clave, nombre_publico):
    return nombre_publico if nombre_publico else clave


def mes_de(fecha_iso):
    return fecha_iso[:7] if fecha_iso else None


def detalle_de_error_github(error):
    if error.codigo is None:
        return error.tipo
    return "HTTP " + str(error.codigo)


def imagen_anterior_de(anteriores, clave):
    anterior = anteriores.get(clave)
    if anterior is None:
        return None
    return anterior.get("imagen")


def demo_anterior_de(anteriores, clave):
    anterior = anteriores.get(clave)
    if anterior is None:
        return None
    return anterior["links"]["demo"]


# ------------------------------------------------------------------ una fuente (repo o extra)


def leer_bitacora_de_repo(cliente, repo, datos):
    """Entradas fecha + título si mostrar_bitacora. Lanza ErrorGitHub o UnicodeDecodeError."""
    if not datos["mostrar_bitacora"]:
        return [], []
    crudo = cliente.leer_archivo(repo["dueno"], repo["nombre"], datos["bitacora"]["archivo"])
    resultado = leer_bitacora(crudo.decode("utf-8"), datos["bitacora"]["max_entradas"])
    return resultado["entradas"], resultado["advertencias"]


def imagen_manual(contenido, fuente, huellas, anteriores, rutas, corrida):
    """Procesa la captura manual. Sin aprobación → queda la anterior aprobada (o ninguna) + advertencia."""
    datos = fuente["datos"]
    clave = fuente["clave"]
    try:
        imagen, huella, _ = procesar_imagen_manual(
            contenido, datos["slug"], fuente["es_privado"], datos["imagen"]["aprobada"],
            datos["imagen"]["alt"], huellas.get(clave), rutas["imagenes"],
        )
    except ErrorImagen as error:
        if error.tipo != "imagen_sin_aprobar":
            raise
        anterior = imagen_anterior_de(anteriores, clave)
        corrida.advertir(clave, fuente["nombre_publico"], "imagen_sin_aprobar", "se mantiene la captura anterior aprobada" if anterior and anterior["origen"] == "manual" else "sin captura")
        if anterior and anterior["origen"] == "manual":
            return anterior
        return None
    huellas[clave] = huella
    return imagen


def imagen_inicial(fuente, anteriores):
    """Sin captura manual: la automática anterior (si sigue habiendo demo con captura_auto) o el placeholder."""
    datos = fuente["datos"]
    anterior = imagen_anterior_de(anteriores, fuente["clave"])
    if datos["links"]["demo"] and datos["captura_auto"] and anterior and anterior["origen"] == "auto":
        return anterior
    return None


def completar_fuente(fuente, leer_imagen, bitacora, huellas, anteriores, rutas, corrida, catalogo):
    """Imagen manual + armado. Devuelve el proyecto de salida."""
    datos = fuente["datos"]
    if datos["imagen"]:
        fuente["imagen"] = imagen_manual(leer_imagen(), fuente, huellas, anteriores, rutas, corrida)
        fuente["tiene_manual"] = True
    else:
        fuente["imagen"] = imagen_inicial(fuente, anteriores)
        fuente["tiene_manual"] = False
    fuente["bitacora"] = bitacora
    proyecto, desconocidas = armar_proyecto(fuente, catalogo)
    for nombre in desconocidas:
        corrida.advertir(fuente["clave"], fuente["nombre_publico"], "etiqueta_fuera_de_catalogo", nombre if fuente["nombre_publico"] else None)
    return proyecto


def procesar_repo(cliente, repo, anteriores, huellas, rutas, corrida, catalogo):
    """Devuelve (resultado para salida, fuente) o (None, None) si el repo no se publica."""
    clave = clave_opaca(repo["id"], repo["es_privado"])
    contexto = {"tipo": "repo", "es_privado": repo["es_privado"], "nombre_repo": repo["nombre"], "creado": repo["creado"]}
    leido = leer_archivo_estandar(repo["portfolio_md"], contexto)
    datos = leido["datos"]
    if repo["es_privado"]:
        REDACTOR.registrar_proyecto_privado(datos, clave)
    if not datos["visible"]:
        return None, None
    nombre_publico = None if repo["es_privado"] else datos["nombre"]["es"]
    fuente = {
        "clave": clave, "origen": "repo", "es_privado": repo["es_privado"], "datos": datos,
        "url_repo": repo["url"], "ultima_actividad": mes_de(repo["ultimo_push"] or repo["creado"]),
        "nombre_publico": nombre_publico,
    }
    for tipo in leido["advertencias"]:
        corrida.advertir(clave, nombre_publico, tipo)
    try:
        bitacora, avisos_bitacora = leer_bitacora_de_repo(cliente, repo, datos)
    except (ErrorGitHub, UnicodeDecodeError):
        raise ErrorArchivoEstandar("bitacora_no_disponible", []) from None
    for tipo in avisos_bitacora:
        corrida.advertir(clave, nombre_publico, tipo)

    def leer_imagen():
        return cliente.leer_archivo(repo["dueno"], repo["nombre"], datos["imagen"]["archivo"])

    proyecto = completar_fuente(fuente, leer_imagen, bitacora, huellas, anteriores, rutas, corrida, catalogo)
    return {"clave": clave, "estado": "ok", "proyecto": proyecto, "nombre_publico": nombre_publico}, fuente


def procesar_extra(ruta, anteriores, huellas, rutas, corrida, catalogo):
    extra = leer_extra(ruta)
    datos = extra["datos"]
    if not datos["visible"]:
        return None, None
    nombre_publico = datos["nombre"]["es"]
    fuente = {
        "clave": extra["clave"], "origen": "extra", "es_privado": False, "datos": datos, "url_repo": None,
        "ultima_actividad": datos["ultima_actividad"], "nombre_publico": nombre_publico,
    }
    for tipo in extra["advertencias"]:
        corrida.advertir(extra["clave"], nombre_publico, tipo)
    proyecto = completar_fuente(fuente, lambda: leer_imagen_extra(extra), [], huellas, anteriores, rutas, corrida, catalogo)
    return {"clave": extra["clave"], "estado": "ok", "proyecto": proyecto, "nombre_publico": nombre_publico}, fuente


def resultado_de_falla(clave, nombre_publico, tipo, detalle=None):
    return {"clave": clave, "estado": "fallo", "tipo": tipo, "detalle": detalle, "nombre_publico": nombre_publico}


def leer_fuentes(cliente, repos, anteriores, huellas, rutas, corrida, catalogo):
    """Cada repo con PORTFOLIO.md y cada extra, dentro de su propio try. Devuelve (resultados, fuentes por clave)."""
    resultados = []
    fuentes = {}
    for repo in repos:
        if repo["portfolio_md"] is None:
            continue
        clave = clave_opaca(repo["id"], repo["es_privado"])
        nombre_publico = None if repo["es_privado"] else repo["nombre"]
        try:
            resultado, fuente = procesar_repo(cliente, repo, anteriores, huellas, rutas, corrida, catalogo)
        except ErrorArchivoEstandar as error:
            resultados.append(resultado_de_falla(clave, nombre_publico, error.tipo))
            if not repo["es_privado"]:
                for detalle in error.detalles:
                    imprimir("  " + repo["nombre"] + ": " + detalle)
            continue
        except ErrorGitHub as error:
            resultados.append(resultado_de_falla(clave, nombre_publico, "no_se_pudo_leer", detalle_de_error_github(error)))
            continue
        except ErrorImagen as error:
            resultados.append(resultado_de_falla(clave, nombre_publico, error.tipo, error.motivo))
            continue
        if resultado is not None:
            resultados.append(resultado)
            fuentes[clave] = fuente
    for ruta in listar_archivos(rutas["extras"]):
        clave = "extra-" + ruta.stem
        try:
            resultado, fuente = procesar_extra(ruta, anteriores, huellas, rutas, corrida, catalogo)
        except ErrorArchivoEstandar as error:
            resultados.append(resultado_de_falla(clave, ruta.stem, error.tipo))
            for detalle in error.detalles:
                imprimir("  " + ruta.name + ": " + detalle)
            continue
        except ErrorImagen as error:
            resultados.append(resultado_de_falla(clave, ruta.stem, error.tipo, error.motivo))
            continue
        if resultado is not None:
            resultados.append(resultado)
            fuentes[clave] = fuente
    return resultados, fuentes


# ------------------------------------------------------------------ capturas automáticas


def toca_captura_diaria(evento, capturas, ahora, config):
    if capturas == "si":
        return True
    if evento != "schedule":
        return False
    # Los cron de GitHub se pueden atrasar: la corrida de las 09:23 UTC puede arrancar hasta las 10:59.
    return ahora.hour in (config["hora_utc_diaria"], config["hora_utc_diaria"] + 1)


def pendientes_de_captura(resultados, fuentes, anteriores, diaria):
    """Proyectos ok sin captura manual, con demo y captura_auto efectivo; todos si es la diaria, si no solo
    los que cambiaron de demo (o no tienen captura todavía)."""
    pendientes = []
    for resultado in resultados:
        if resultado["estado"] != "ok":
            continue
        fuente = fuentes[resultado["clave"]]
        datos = fuente["datos"]
        if fuente["tiene_manual"] or not datos["links"]["demo"] or not datos["captura_auto"]:
            continue
        cambio_demo = demo_anterior_de(anteriores, resultado["clave"]) != datos["links"]["demo"]
        if diaria or cambio_demo:
            pendientes.append(resultado)
    return pendientes


def sacar_capturas(pendientes, fuentes, rutas, corrida, config, abrir=abrir_navegador):
    if not pendientes:
        return
    imprimir("Capturas automáticas: " + str(len(pendientes)) + " proyecto(s)")
    try:
        with abrir() as navegador:
            for resultado in pendientes:
                capturar_uno(navegador, resultado, fuentes[resultado["clave"]], rutas, corrida, config)
    except ErrorCaptura:
        raise
    except Exception:
        # No se pudo abrir el navegador: todas quedan con su captura anterior.
        for resultado in pendientes:
            corrida.advertir(resultado["clave"], resultado["nombre_publico"], "captura_auto_fallida", "navegador; se mantiene la captura anterior")


def capturar_uno(navegador, resultado, fuente, rutas, corrida, config):
    proyecto = resultado["proyecto"]
    try:
        imagen, cambio = capturar_proyecto(
            navegador, proyecto["slug"], fuente["datos"]["links"]["demo"], proyecto["imagen"], rutas["imagenes"], config
        )
    except ErrorCaptura as error:
        detalle = ("HTTP " + str(error.codigo)) if error.codigo else error.motivo
        corrida.advertir(resultado["clave"], resultado["nombre_publico"], "captura_auto_fallida", detalle + "; se mantiene la captura anterior")
        return
    proyecto["imagen"] = imagen
    estado = "actualizada" if cambio else "sin cambio visible"
    imprimir("  " + nombre_en_logs(resultado["clave"], resultado["nombre_publico"]) + ": captura " + estado)


# ------------------------------------------------------------------ simulacros (input probar_alertas)


def simular_falla_repo(resultados):
    """Marca como fallido el primer proyecto ok (prefiere uno privado, para probar la redacción)."""
    elegido = None
    for resultado in resultados:
        if resultado["estado"] == "ok" and (elegido is None or resultado["nombre_publico"] is None):
            elegido = resultado
            if resultado["nombre_publico"] is None:
                break
    if elegido is None:
        return None
    elegido["estado"] = "fallo"
    elegido["tipo"] = "prueba_falla_repo"
    elegido["detalle"] = "simulada con probar_alertas"
    elegido["simulada"] = True
    return elegido["clave"]


# ------------------------------------------------------------------ validación final


def errores_de_salida(proyectos, perfil, ruta_esquema):
    esquema = validar_datos.leer_json(ruta_esquema)
    datos = {"version": 1, "proyectos": proyectos}
    errores = validar_datos.errores_de_esquema(esquema, "archivo_proyectos", datos, "proyectos.json")
    errores.extend(validar_datos.errores_de_esquema(esquema, "archivo_perfil", perfil, "perfil.json"))
    errores.extend(validar_datos.errores_de_slugs(proyectos))
    errores.extend(validar_datos.errores_de_claves_opacas(proyectos))
    return errores


# ------------------------------------------------------------------ resumen y estado


def linea_de_advertencia(item):
    texto = nombre_en_logs(item["clave"], item["nombre"]) + " — " + item["tipo"]
    if item["detalle"]:
        texto += " (" + item["detalle"] + ")"
    return texto


def escribir_resumen(estado):
    """Resumen de la corrida en GITHUB_STEP_SUMMARY (si existe) y anotaciones ::warning::."""
    lineas = ["## Actualización del portfolio", ""]
    if estado["resultado"] == "falla":
        lineas.append("**Falla total:** " + estado["falla"]["tipo"] + (" (" + estado["falla"]["detalle"] + ")" if estado["falla"]["detalle"] else ""))
    else:
        lineas.append("Proyectos publicados: " + str(estado["proyectos"]) + ". Cambios en los datos: " + ("sí" if estado["cambios"] else "no") + ".")
    if estado["advertencias"]:
        lineas.extend(["", "### Advertencias", ""])
        for item in estado["advertencias"]:
            lineas.append("- " + linea_de_advertencia(item))
            imprimir("::warning::" + linea_de_advertencia(item))
    if estado["avisos"]:
        lineas.extend(["", "### Avisos (solo resumen)", ""])
        for item in estado["avisos"]:
            lineas.append("- " + linea_de_advertencia(item))
    lineas.extend(["", "Vencimiento del token: " + (estado["vencimiento_token"] or "desconocido")])
    texto = REDACTOR.redactar("\n".join(lineas) + "\n")
    ruta = os.environ.get("GITHUB_STEP_SUMMARY")
    if ruta:
        with open(ruta, "a", encoding="utf-8") as archivo:
            archivo.write(texto)
    else:
        imprimir(texto)


def guardar_estado(estado, ruta):
    if not ruta:
        return
    Path(ruta).write_text(REDACTOR.redactar(json.dumps(estado, ensure_ascii=False, indent=2)), encoding="utf-8")


def estado_vacio(vencimiento):
    return {
        "resultado": "ok", "falla": None, "advertencias": [], "avisos": [], "vencimiento_token": vencimiento,
        "proyectos": 0, "cambios": False,
    }


# ------------------------------------------------------------------ corrida completa


def ejecutar(cliente, opciones, rutas=None, ahora=None, abrir=abrir_navegador):
    """Corre todo y devuelve el estado (dict). No sale del proceso: lo hace main()."""
    rutas = dict(RUTAS_POR_DEFECTO, **(rutas or {}))
    ahora = ahora or datetime.datetime.now(datetime.timezone.utc)
    corrida = Corrida()
    estado = estado_vacio(None)
    try:
        repos = cliente.listar_repos()
        estado["vencimiento_token"] = cliente.vencimiento_token or os.environ.get("TOKEN_VENCE") or None
        if not repos:
            raise ErrorFallaTotal("lista_de_repos_vacia")
        for repo in repos:
            if repo["es_privado"]:
                REDACTOR.registrar_repo_privado(repo["nombre"], clave_opaca(repo["id"], True), repo["dueno"])
        if opciones.probar_alertas == "falla_total":
            raise ErrorFallaTotal("prueba_falla_total", "simulada con probar_alertas")

        anteriores = proyectos_anteriores(rutas["proyectos"])
        huellas = leer_huellas(rutas["huellas"])
        catalogo = cargar_catalogo()
        resultados, fuentes = leer_fuentes(cliente, repos, anteriores, huellas, rutas, corrida, catalogo)

        config = cargar_config()
        diaria = toca_captura_diaria(opciones.evento, opciones.capturas, ahora, config)
        sacar_capturas(pendientes_de_captura(resultados, fuentes, anteriores, diaria), fuentes, rutas, corrida, config, abrir)

        if opciones.probar_alertas == "falla_repo":
            simular_falla_repo(resultados)
        proyectos, advertencias = resolver_resultados(resultados, anteriores)
        corrida.advertencias.extend(advertencias)

        nombres = {}
        for resultado in resultados:
            nombres[resultado["clave"]] = resultado.get("nombre_publico")
        proyectos, advertencias = resolver_slugs(proyectos, anteriores, nombres)
        corrida.advertencias.extend(advertencias)
        proyectos = ordenar(proyectos)

        perfil = armar_perfil(rutas["perfil_yml"], rutas["cv"])
        errores = errores_de_salida(proyectos, perfil, rutas["esquema_salida"])
        if errores:
            for error in errores:
                imprimir("  " + error)
            raise ErrorFallaTotal("salida_no_valida", str(len(errores)) + " error(es)")

        cambios = escribir_proyectos(proyectos, rutas["proyectos"])
        cambios = escribir_perfil(perfil, rutas["perfil"]) or cambios
        cambios = escribir_huellas(huellas_vigentes(huellas, proyectos), rutas["huellas"]) or cambios
        if limpiar_imagenes(proyectos, rutas["imagenes"]):
            cambios = True
        estado["proyectos"] = len(proyectos)
        estado["cambios"] = cambios
    except ErrorFallaTotal as error:
        estado["resultado"] = "falla"
        estado["falla"] = {"tipo": error.tipo, "detalle": error.detalle}
    except ErrorGitHub as error:
        estado["resultado"] = "falla"
        estado["falla"] = {"tipo": "lista_de_repos_" + error.tipo, "detalle": detalle_de_error_github(error)}
        estado["vencimiento_token"] = cliente.vencimiento_token or os.environ.get("TOKEN_VENCE") or None
    estado["advertencias"] = corrida.advertencias
    estado["avisos"] = corrida.avisos
    return estado


def huellas_vigentes(huellas, proyectos):
    """Solo las huellas de proyectos publicados con captura manual (el resto se descarta)."""
    vigentes = {}
    for proyecto in proyectos:
        imagen = proyecto.get("imagen")
        if imagen and imagen["origen"] == "manual" and proyecto["clave"] in huellas:
            vigentes[proyecto["clave"]] = huellas[proyecto["clave"]]
    return vigentes


def leer_opciones(argumentos=None):
    parser = argparse.ArgumentParser(description="Genera los datos del portfolio desde los repos.")
    parser.add_argument("--evento", default="local", choices=["schedule", "workflow_dispatch", "push", "repository_dispatch", "local"])
    parser.add_argument("--capturas", default="no", choices=["si", "no"])
    parser.add_argument("--probar-alertas", dest="probar_alertas", default="no", choices=["no", "falla_total", "falla_repo"])
    parser.add_argument("--estado", default=None, help="ruta del JSON de estado para alertas.py")
    return parser.parse_args(argumentos)


def main():
    instalar_gancho_de_excepciones()
    opciones = leer_opciones()
    token = os.environ.get("GH_TOKEN_LECTURA")
    if not token:
        imprimir("Falta la variable de entorno GH_TOKEN_LECTURA.")
        estado = estado_vacio(os.environ.get("TOKEN_VENCE"))
        estado["resultado"] = "falla"
        estado["falla"] = {"tipo": "falta_token", "detalle": None}
    else:
        estado = ejecutar(ClienteGitHub(token), opciones)
    escribir_resumen(estado)
    guardar_estado(estado, opciones.estado)
    if estado["resultado"] == "falla":
        imprimir("Falla total: " + estado["falla"]["tipo"])
        return 1
    imprimir("OK: " + str(estado["proyectos"]) + " proyectos; cambios: " + ("sí" if estado["cambios"] else "no"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
