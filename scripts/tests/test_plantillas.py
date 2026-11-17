"""Las plantillas son válidas: el template de PORTFOLIO.md completado valida y trae los defaults seguros."""

from portfolio import RAIZ
from portfolio.archivo_estandar import leer_archivo_estandar
from portfolio.bitacora import leer_bitacora

CONTEXTO = {"tipo": "repo", "es_privado": False, "nombre_repo": "repo-nuevo", "creado": "2026-11-17T00:00:00Z"}


def leer_plantilla(nombre):
    return (RAIZ / "plantillas" / nombre).read_text(encoding="utf-8")


def completar(texto):
    reemplazos = [
        ("COMPLETAR nombre del proyecto (1–60 caracteres)", "Repo nuevo"),
        ("COMPLETAR qué hace, en una línea (1–160 caracteres).", "Hace algo útil."),
        ("TO DO what it does, in one line (1–160 characters).", "Does something useful."),
        ("COMPLETAR: qué se quería hacer al arrancar (máx. ~600 caracteres).", "Hacer algo útil."),
        ("<!-- TO DO: what the goal was when it started. -->", "To do something useful."),
    ]
    for viejo, nuevo in reemplazos:
        assert viejo in texto
        texto = texto.replace(viejo, nuevo)
    return texto


def test_template_completado_valida_con_defaults_seguros():
    resultado = leer_archivo_estandar(completar(leer_plantilla("PORTFOLIO.md")), CONTEXTO)
    datos = resultado["datos"]
    assert datos["visible"] is False
    assert datos["mostrar_bitacora"] is False
    assert datos["slugs_anteriores"] == []
    assert datos["imagen"] is None
    assert datos["slug"] == "repo-nuevo"
    assert datos["idea_original"] == {"es": "Hacer algo útil.", "en": "To do something useful."}
    # El resultado en inglés y los milestones quedan vacíos en el template: solo advertencias.
    assert "falta_ingles:outcome" in resultado["advertencias"]


def test_template_sin_completar_tambien_parsea():
    datos = leer_archivo_estandar(leer_plantilla("PORTFOLIO.md"), CONTEXTO)["datos"]
    assert datos["visible"] is False


def test_template_de_bitacora_no_tiene_entradas_con_fecha_real():
    assert leer_bitacora(leer_plantilla("BITACORA.md"), 10)["entradas"] == []
