"""generar_cv.py: huella, decisión de regenerar y falla que conserva los PDF (paso 35).
La generación real (build + Playwright) se prueba a mano y en la corrida del Action."""

import json

import generar_cv


def armar_raiz(tmp_path):
    for relativa, texto in {
        "src/App.jsx": "app",
        "src/datos/perfil.json": "{}",
        "src/datos/huellas.json": "{}",
        "es/index.html": "es",
        "en/index.html": "en",
        "index.html": "raiz",
        "plugins/meta.js": "meta",
        "package-lock.json": "{}",
        "public/proyectos/x.webp": "no cuenta",
        "README.md": "no cuenta",
    }.items():
        ruta = tmp_path / relativa
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(texto, encoding="utf-8")
    return tmp_path


def test_archivos_de_la_huella(tmp_path):
    raiz = armar_raiz(tmp_path)
    assert generar_cv.archivos_de_la_huella(raiz) == [
        "en/index.html", "es/index.html", "index.html", "package-lock.json", "plugins/meta.js",
        "src/App.jsx", "src/datos/perfil.json",
    ]


def test_huella_cambia_solo_con_lo_que_afecta_al_cv(tmp_path):
    raiz = armar_raiz(tmp_path)
    inicial = generar_cv.calcular_huella(raiz)
    (raiz / "README.md").write_text("otro", encoding="utf-8")
    (raiz / "src/datos/huellas.json").write_text('{"a": "b"}', encoding="utf-8")
    (raiz / "public/proyectos/x.webp").write_text("otra", encoding="utf-8")
    assert generar_cv.calcular_huella(raiz) == inicial
    (raiz / "src/App.jsx").write_bytes(b"app")  # mismo contenido
    assert generar_cv.calcular_huella(raiz) == inicial
    (raiz / "es/index.html").write_bytes(b"es\r\n")
    (raiz / "en/index.html").write_bytes(b"en\n")
    cambiada = generar_cv.calcular_huella(raiz)
    assert cambiada != inicial
    (raiz / "es/index.html").write_bytes(b"es\n")  # CRLF y LF dan la misma huella
    assert generar_cv.calcular_huella(raiz) == cambiada


def test_hay_que_regenerar(tmp_path):
    raiz = armar_raiz(tmp_path / "repo")
    carpeta_cv = tmp_path / "cv"
    carpeta_cv.mkdir()
    assert generar_cv.hay_que_regenerar(carpeta_cv, raiz) is True  # sin PDF
    for idioma in ("es", "en"):
        (carpeta_cv / ("cv-" + idioma + ".pdf")).write_bytes(b"%PDF")
    assert generar_cv.hay_que_regenerar(carpeta_cv, raiz) is True  # sin huella
    (carpeta_cv / "huella.txt").write_text(generar_cv.calcular_huella(raiz) + "\n", encoding="utf-8")
    assert generar_cv.hay_que_regenerar(carpeta_cv, raiz) is False
    (raiz / "src/App.jsx").write_text("cambio", encoding="utf-8")
    assert generar_cv.hay_que_regenerar(carpeta_cv, raiz) is True


def test_falla_anota_advertencia_y_conserva(tmp_path, capsys):
    estado = tmp_path / "estado.json"
    estado.write_text(json.dumps({"advertencias": []}), encoding="utf-8")
    carpeta_cv = tmp_path / "cv"
    carpeta_cv.mkdir()
    (carpeta_cv / "cv-es.pdf").write_bytes(b"%PDF viejo")
    (carpeta_cv / "cv-es.pdf.tmp").write_bytes(b"a medias")
    generar_cv.limpiar_temporales(carpeta_cv)
    generar_cv.anotar_falla(str(estado), "build")
    assert (carpeta_cv / "cv-es.pdf").read_bytes() == b"%PDF viejo"
    assert not (carpeta_cv / "cv-es.pdf.tmp").exists()
    advertencias = json.loads(estado.read_text(encoding="utf-8"))["advertencias"]
    assert advertencias[0]["tipo"] == "cv_pdf_fallido"
    assert "::warning::" in capsys.readouterr().out
