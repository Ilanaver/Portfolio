"""identidad.py: claves opacas y filtro de redacción, con errores forzados en repos privados de prueba (paso 27)."""

import io
import subprocess
import sys

from portfolio import RAIZ
from portfolio.identidad import REDACTOR, Redactor, clave_extra, clave_opaca, es_clave_privada, imprimir

ID_PRIVADO = "R_kgDOPruebaPrivada"
ID_PUBLICO = "R_kgDOPruebaPublica"


def test_formato_de_claves():
    privada = clave_opaca(ID_PRIVADO, True)
    publica = clave_opaca(ID_PUBLICO, False)
    assert privada.startswith("priv-") and len(privada) == 13
    assert publica.startswith("pub-") and len(publica) == 12
    assert clave_extra("mi-extra") == "extra-mi-extra"
    assert es_clave_privada(privada) and not es_clave_privada(publica)


def test_publica_y_privada_usan_el_mismo_hash():
    assert clave_opaca(ID_PRIVADO, True)[5:] == clave_opaca(ID_PRIVADO, False)[4:]


def redactor_de_prueba():
    redactor = Redactor()
    clave = clave_opaca(ID_PRIVADO, True)
    redactor.registrar_repo_privado("repo-secreto", clave, dueno="Dueno")
    redactor.registrar_proyecto_privado(
        {
            "slug": "secreto-app",
            "nombre": {"es": "App Secreta", "en": "Secret App"},
            "links": {"demo": "https://secreto.ejemplo.test/panel"},
            "slugs_anteriores": ["viejo-secreto"],
        },
        clave,
    )
    return redactor, clave


def test_redacta_nombres_urls_y_slugs_sin_importar_mayusculas():
    redactor, clave = redactor_de_prueba()
    texto = (
        "Error en Repo-Secreto (https://github.com/Dueno/repo-secreto/blob/main/PORTFOLIO.md); "
        "demo https://secreto.ejemplo.test/panel caída; slug secreto-app; viejo-secreto; APP SECRETA; Secret App"
    )
    salida = redactor.redactar(texto)
    for sensible in ["repo-secreto", "secreto.ejemplo", "secreto-app", "viejo-secreto", "app secreta", "secret app"]:
        assert sensible not in salida.lower()
    assert clave in salida


def test_tapa_tokens_aunque_no_esten_registrados():
    redactor = Redactor()
    texto = (
        "ghp_" + "a" * 36 + " github_pat_" + "B" * 40 + " 123456789:" + "c" * 35
        + " Authorization: Bearer xyz123"
    )
    salida = redactor.redactar(texto)
    for sensible in ["ghp_", "github_pat_", "ccccc", "xyz123"]:
        assert sensible not in salida


def test_textos_cortos_no_se_registran():
    redactor = Redactor()
    redactor.registrar("ab", "priv-00000000")
    assert redactor.redactar("abc") == "abc"


def test_imprimir_redacta():
    clave = clave_opaca(ID_PRIVADO, True)
    REDACTOR.registrar("nombre-privado-global", clave)
    salida = io.StringIO()
    imprimir("falló nombre-privado-global", salida)
    assert salida.getvalue() == "falló " + clave + "\n"


CODIGO_TRACEBACK = """
import sys
sys.path.insert(0, 'scripts')
from portfolio.identidad import REDACTOR, instalar_gancho_de_excepciones
REDACTOR.registrar('repo-super-secreto', 'priv-12345678')
instalar_gancho_de_excepciones()
raise RuntimeError('timeout leyendo https://api.github.com/repos/Dueno/repo-super-secreto/contents')
"""


def test_traceback_no_previsto_sale_redactado():
    proceso = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", CODIGO_TRACEBACK],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proceso.returncode != 0
    assert "repo-super-secreto" not in proceso.stderr + proceso.stdout
    assert "priv-12345678" in proceso.stderr
