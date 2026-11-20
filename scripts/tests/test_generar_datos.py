"""generar_datos.py de punta a punta con una API simulada (paso 33).

Repos inventados: uno público completo (bitácora + captura manual), uno privado válido, uno privado cuya
bitácora no se puede leer, uno privado sin PORTFOLIO.md. Se verifica la salida, que ningún nombre privado
aparece en logs, resumen ni estado, la corrida sin cambios, y los simulacros de falla.
"""

import argparse
import io
import json
from contextlib import redirect_stdout

import pytest
from PIL import Image

import generar_datos
from portfolio.api_github import ErrorGitHub
from portfolio.identidad import REDACTOR, clave_opaca

from tests.utiles import FIXTURES

NOMBRES_PRIVADOS = ["repo-secreto", "bitacora-secreta", "sin-archivo-secreto", "Solo Español", "solo-espanol"]


def png_de_prueba():
    salida = io.BytesIO()
    Image.new("RGB", (1000, 625), (10, 120, 200)).save(salida, format="PNG")
    return salida.getvalue()


def repo(nombre, privado, portfolio_md):
    return {
        "id": "R_" + nombre, "nombre": nombre, "dueno": "dueno", "es_privado": privado, "archivado": False,
        "creado": "2025-01-01T00:00:00Z", "ultimo_push": "2026-11-16T10:00:00Z",
        "url": "https://github.com/dueno/" + nombre, "portfolio_md": portfolio_md,
    }


class ClienteFalso:
    def __init__(self, repos, archivos, falla_lista=None):
        self.repos = repos
        self.archivos = archivos
        self.falla_lista = falla_lista
        self.vencimiento_token = "2027-11-01"

    def listar_repos(self):
        if self.falla_lista:
            raise self.falla_lista
        return self.repos

    def leer_archivo(self, dueno, nombre, ruta):
        clave = nombre + "/" + ruta
        if clave not in self.archivos:
            raise ErrorGitHub("no_encontrado", 404)
        return self.archivos[clave]


def leer(nombre):
    return (FIXTURES / "portfolio" / nombre).read_text(encoding="utf-8")


def cliente_de_prueba():
    privado_con_bitacora = leer("sin_ingles.md").replace("mostrar_bitacora: false", "mostrar_bitacora: true").replace(
        "nombre: Solo Español", "nombre: Bitácora Secreta\nslug: bitacora-secreta"
    )
    repos = [
        repo("inventado", False, leer("valido.md")),
        repo("solo-espanol", True, leer("sin_ingles.md")),
        repo("bitacora-secreta", True, privado_con_bitacora),
        repo("sin-archivo-secreto", True, None),
    ]
    archivos = {
        "inventado/docs/BITACORA.md": (FIXTURES / "bitacoras" / "unico.md").read_bytes(),
        "inventado/docs/captura.png": png_de_prueba(),
    }
    return ClienteFalso(repos, archivos)


@pytest.fixture(autouse=True)
def sin_resumen_de_actions(monkeypatch):
    # En Actions existe GITHUB_STEP_SUMMARY: el resumen iría a ese archivo y no al log que miran los tests.
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)


@pytest.fixture
def rutas(tmp_path):
    (tmp_path / "extras").mkdir()
    return {
        "proyectos": tmp_path / "datos" / "proyectos.json",
        "perfil": tmp_path / "datos" / "perfil.json",
        "huellas": tmp_path / "datos" / "huellas.json",
        "imagenes": tmp_path / "public" / "proyectos",
        "cv": tmp_path / "public" / "cv",
        "extras": tmp_path / "extras",
    }


def opciones(probar="no", capturas="no", evento="local"):
    return argparse.Namespace(probar_alertas=probar, capturas=capturas, evento=evento, estado=None)


def correr(cliente, rutas, probar="no"):
    salida = io.StringIO()
    with redirect_stdout(salida):
        estado = generar_datos.ejecutar(cliente, opciones(probar), rutas)
        generar_datos.escribir_resumen(estado)
    return estado, salida.getvalue()


def sin_nombres_privados(texto):
    for nombre in NOMBRES_PRIVADOS:
        assert nombre.lower() not in texto.lower(), nombre


def test_corrida_completa(rutas, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    estado, log = correr(cliente_de_prueba(), rutas)
    assert estado["resultado"] == "ok", estado
    assert estado["cambios"] is True
    datos = json.loads(rutas["proyectos"].read_text(encoding="utf-8"))
    slugs = []
    for proyecto in datos["proyectos"]:
        slugs.append(proyecto["slug"])
    # Orden: el destacado (inventado) primero. El privado de bitácora ilegible no tenía versión anterior: no entra.
    assert slugs == ["proyecto-inventado", "solo-espanol"]
    inventado = datos["proyectos"][0]
    assert inventado["bitacora"][0] == {"fecha": "2026-02-03", "titulo": "Tercera entrada con link"}
    assert inventado["imagen"]["origen"] == "manual"
    assert (rutas["imagenes"] / "proyecto-inventado-1200.webp").exists()
    assert inventado["links"]["repo"] == "https://github.com/dueno/inventado"
    assert inventado["ultima_actividad"] == "2025-09"  # terminado: el mes de fecha_fin
    privado = None
    for proyecto in datos["proyectos"]:
        if proyecto["slug"] == "solo-espanol":
            privado = proyecto
    assert privado["clave"] == clave_opaca("R_solo-espanol", True)
    assert privado["links"]["repo"] is None
    perfil = json.loads(rutas["perfil"].read_text(encoding="utf-8"))
    assert perfil["cv_pdf"] is None and perfil["version"] == 1
    assert json.loads(rutas["huellas"].read_text(encoding="utf-8")) == {inventado["clave"]: inventado_huella(rutas)}

    tipos = []
    for item in estado["advertencias"]:
        tipos.append(item["tipo"])
    assert tipos == ["bitacora_no_disponible"]
    assert estado["advertencias"][0]["nombre"] is None
    assert estado["advertencias"][0]["clave"].startswith("priv-")
    avisos = []
    for item in estado["avisos"]:
        avisos.append(item["tipo"])
    assert "falta_ingles:descripcion_en" in avisos
    assert estado["vencimiento_token"] == "2027-11-01"

    sin_nombres_privados(log)
    sin_nombres_privados(REDACTOR.redactar(json.dumps(estado, ensure_ascii=False)))


def inventado_huella(rutas):
    from portfolio.imagenes import hash_corto
    return hash_corto(png_de_prueba())


def test_segunda_corrida_sin_cambios_no_toca_archivos(rutas):
    correr(cliente_de_prueba(), rutas)
    marcas = {}
    for clave in ("proyectos", "perfil", "huellas"):
        marcas[clave] = rutas[clave].stat().st_mtime_ns
    imagen = rutas["imagenes"] / "proyecto-inventado-1200.webp"
    marca_imagen = imagen.stat().st_mtime_ns
    estado, _ = correr(cliente_de_prueba(), rutas)
    assert estado["cambios"] is False
    for clave in marcas:
        assert rutas[clave].stat().st_mtime_ns == marcas[clave]
    assert imagen.stat().st_mtime_ns == marca_imagen


def test_falla_de_un_repo_mantiene_su_version(rutas):
    correr(cliente_de_prueba(), rutas)
    antes = json.loads(rutas["proyectos"].read_text(encoding="utf-8"))
    cliente = cliente_de_prueba()
    cliente.archivos["bitacora-secreta/BITACORA.md"] = "## 01/01/2026 — Entrada\n".encode("utf-8")
    cliente.repos[0]["portfolio_md"] = "---\nroto: [\n---\n"
    cliente.repos[1]["portfolio_md"] = cliente.repos[1]["portfolio_md"].replace("Sin nada en inglés.", "Descripción nueva.")
    estado, log = correr(cliente, rutas)
    assert estado["resultado"] == "ok"
    despues = json.loads(rutas["proyectos"].read_text(encoding="utf-8"))
    assert despues["proyectos"][0] == antes["proyectos"][0]  # el público roto queda igual
    assert despues["proyectos"][0]["slug"] == "proyecto-inventado"
    descripciones = []
    for proyecto in despues["proyectos"]:
        descripciones.append(proyecto["descripcion"]["es"])
    assert "Descripción nueva." in descripciones
    sin_nombres_privados(log)


def test_probar_falla_repo(rutas):
    correr(cliente_de_prueba(), rutas)
    estado, log = correr(cliente_de_prueba(), rutas, probar="falla_repo")
    assert estado["resultado"] == "ok"
    tipos = []
    for item in estado["advertencias"]:
        tipos.append((item["tipo"], item["nombre"]))
    assert ("prueba_falla_repo", None) in tipos  # elige un privado: sin nombre
    sin_nombres_privados(log)


def test_probar_falla_total_no_escribe(rutas):
    estado, log = correr(cliente_de_prueba(), rutas, probar="falla_total")
    assert estado["resultado"] == "falla"
    assert estado["falla"]["tipo"] == "prueba_falla_total"
    assert not rutas["proyectos"].exists()
    assert "Falla total" in log


def test_falla_de_la_lista_es_falla_total(rutas):
    cliente = ClienteFalso([], {}, falla_lista=ErrorGitHub("token_invalido", 401))
    estado, _ = correr(cliente, rutas)
    assert estado["resultado"] == "falla"
    assert estado["falla"] == {"tipo": "lista_de_repos_token_invalido", "detalle": "HTTP 401"}
    assert not rutas["proyectos"].exists()


def test_lista_vacia_es_falla_total(rutas):
    estado, _ = correr(ClienteFalso([], {}), rutas)
    assert estado["falla"]["tipo"] == "lista_de_repos_vacia"


def test_mas_de_la_mitad_fallan(rutas):
    cliente = cliente_de_prueba()
    cliente.repos[0]["portfolio_md"] = "roto"
    cliente.repos[1]["portfolio_md"] = "roto"
    estado, _ = correr(cliente, rutas)
    assert estado["falla"]["tipo"] == "mas_de_la_mitad_fallaron"
    assert not rutas["proyectos"].exists()


def test_proyectos_extra_se_suman(rutas):
    rutas["extras"] = FIXTURES / "extras"
    estado, log = correr(cliente_de_prueba(), rutas)
    datos = json.loads(rutas["proyectos"].read_text(encoding="utf-8"))
    claves = []
    for proyecto in datos["proyectos"]:
        claves.append(proyecto["clave"])
    assert "extra-automatizacion-inventada" in claves
    # el extra con el nombre de archivo equivocado falla y se nombra (es público)
    fallidos = []
    for item in estado["advertencias"]:
        fallidos.append(item["nombre"])
    assert "nombre-equivocado" in fallidos
    assert (rutas["imagenes"] / "automatizacion-inventada-1200.webp").exists()


def test_terminado_muestra_su_fecha_de_fin(rutas):
    # inventado: terminado con fecha_fin 2025-09 y último push 2026-11 → ultima_actividad 2025-09.
    correr(cliente_de_prueba(), rutas)
    datos = json.loads(rutas["proyectos"].read_text(encoding="utf-8"))
    meses = {}
    for proyecto in datos["proyectos"]:
        meses[proyecto["slug"]] = proyecto["ultima_actividad"]
    assert meses["proyecto-inventado"] == "2025-09"
    assert meses["solo-espanol"] == "2026-11"  # activo: sigue el último push


def test_ultima_actividad_de():
    assert generar_datos.ultima_actividad_de({"estado": "terminado", "fecha_fin": "2025-04-03"}, "2026-11") == "2025-04"
    assert generar_datos.ultima_actividad_de({"estado": "pausado", "fecha_fin": None}, "2026-11") == "2026-11"
    assert generar_datos.ultima_actividad_de({"estado": "activo", "fecha_fin": None}, "2026-10") == "2026-10"
