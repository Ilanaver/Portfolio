"""archivo_estandar.py: un archivo válido, uno sin inglés y 7 inválidos (paso 23)."""

import pytest

from portfolio.archivo_estandar import ErrorArchivoEstandar, leer_archivo_estandar, slug_desde_nombre_repo

from tests.utiles import FIXTURES

CONTEXTO_PUBLICO = {"tipo": "repo", "es_privado": False, "nombre_repo": "Proyecto_Inventado", "creado": "2025-02-01T10:00:00Z"}
CONTEXTO_PRIVADO = {"tipo": "repo", "es_privado": True, "nombre_repo": "Secreto", "creado": "2025-02-01T10:00:00Z"}


def leer_fixture(nombre):
    return (FIXTURES / "portfolio" / nombre).read_text(encoding="utf-8")


def test_valido_completo():
    resultado = leer_archivo_estandar(leer_fixture("valido.md"), CONTEXTO_PUBLICO)
    datos = resultado["datos"]
    assert resultado["advertencias"] == []
    assert datos["nombre"] == {"es": "Proyecto Inventado", "en": "Made-up Project"}
    assert datos["fecha_inicio"] == "2025-03-01"  # texto, no datetime.date
    assert datos["fecha_fin"] == "2025-09"
    assert datos["links"]["repo"] == "auto"
    assert datos["links"]["otros"][0]["texto"] == {"es": "Artículo", "en": "Article"}
    assert datos["captura_auto"] is True
    assert datos["imagen"]["aprobada"] == "0123456789ab"
    assert datos["bitacora"] == {"archivo": "docs/BITACORA.md", "max_entradas": 5}
    assert datos["idea_original"]["es"] == "Una idea de prueba en dos líneas."
    assert datos["resultado"]["es"] == "Quedó algo distinto.\n\nSegundo párrafo."
    assert datos["hitos"]["es"][0] == {
        "fecha": "2025-05-10",
        "texto": "Falla rara → causa inventada → arreglo inventado.",
        "tipo": "arreglo",
    }
    assert datos["hitos"]["es"][1]["tipo"] == "hito"
    assert datos["hitos"]["en"][0]["tipo"] == "arreglo"


def test_seccion_no_reconocida_se_ignora():
    datos = leer_archivo_estandar(leer_fixture("valido.md"), CONTEXTO_PUBLICO)["datos"]
    assert "secreto" not in repr(datos).lower()


def test_sin_ingles_es_advertencia_y_aplica_defaults():
    resultado = leer_archivo_estandar(leer_fixture("sin_ingles.md"), CONTEXTO_PUBLICO)
    datos = resultado["datos"]
    assert sorted(resultado["advertencias"]) == [
        "falta_ingles:descripcion_en",
        "falta_ingles:milestones",
        "falta_ingles:original_idea",
        "falta_ingles:outcome",
    ]
    assert datos["nombre"] == {"es": "Solo Español", "en": "Solo Español"}
    assert datos["descripcion"]["en"] is None
    assert datos["hitos"]["en"] is None
    assert datos["slug"] == "proyecto-inventado"  # del nombre del repo
    assert datos["fecha_inicio"] == "2025-02-01"  # createdAt del repo
    assert datos["destacado"] is False
    assert datos["links"] == {"demo": None, "repo": "auto", "otros": []}


def test_privado_fuerza_repo_null_y_captura_auto_false():
    datos = leer_archivo_estandar(leer_fixture("valido.md"), CONTEXTO_PRIVADO)["datos"]
    assert datos["links"]["repo"] is None
    assert datos["captura_auto"] is False


def test_privado_con_captura_auto_explicita():
    texto = leer_fixture("sin_ingles.md").replace("estado: activo", "estado: activo\ncaptura_auto: true")
    datos = leer_archivo_estandar(texto, CONTEXTO_PRIVADO)["datos"]
    assert datos["captura_auto"] is True


def reemplazar(texto, viejo, nuevo):
    assert viejo in texto
    return texto.replace(viejo, nuevo)


CASOS_INVALIDOS = [
    ("falta campo obligatorio", "descripcion: Un proyecto de prueba que no existe.\n", ""),
    ("estado raro", "estado: terminado", "estado: en_pausa"),
    ("terminado sin fecha_fin", "fecha_fin: 2025-09\n", ""),
    ("URL http://", "demo: https://inventado.ejemplo.test", "demo: http://inventado.ejemplo.test"),
    ("slug inválido", "slug: proyecto-inventado", "slug: Proyecto_Inventado"),
    ("imagen sin alt", "  alt: Pantalla principal inventada.\n", ""),
    ("slugs_anteriores con el slug actual", "slugs_anteriores: [nombre-viejo]", "slugs_anteriores: [proyecto-inventado]"),
]


@pytest.mark.parametrize("nombre,viejo,nuevo", CASOS_INVALIDOS)
def test_invalidos(nombre, viejo, nuevo):
    texto = reemplazar(leer_fixture("valido.md"), viejo, nuevo)
    with pytest.raises(ErrorArchivoEstandar) as error:
        leer_archivo_estandar(texto, CONTEXTO_PUBLICO)
    assert error.value.tipo == "no_valida", nombre
    assert error.value.detalles, nombre


def test_otros_invalidos():
    base = leer_fixture("valido.md")
    casos = [
        "sin frontmatter\n",
        "---\nversion: 1\n",  # sin cierre
        reemplazar(base, "- 2025-03-01 — Primera versión.", "- 2025-13-01 — Fecha imposible."),
        reemplazar(base, "## Idea original\nUna idea de prueba\nen dos líneas.", "## Idea original\n"),
        "---\n: : :\n---\n",
    ]
    for texto in casos:
        with pytest.raises(ErrorArchivoEstandar):
            leer_archivo_estandar(texto, CONTEXTO_PUBLICO)


def test_slug_desde_nombre_repo():
    assert slug_desde_nombre_repo("Proyecto_BD") == "proyecto-bd"
    assert slug_desde_nombre_repo("mi-repo-viejo") == "mi-repo-viejo"
    assert slug_desde_nombre_repo("TP5 Sala.de escape") == "tp5-sala-de-escape"
