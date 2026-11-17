"""imagenes.py: tipo real, tamaño, aprobación por hash, metadatos eliminados, sin reproceso (paso 29)."""

import io

import pytest
from PIL import Image

from portfolio.imagenes import (
    BYTES_MAXIMOS,
    ErrorImagen,
    hash_corto,
    procesar_imagen_manual,
    tipo_real,
)

ALT = {"es": "Captura de prueba", "en": "Test screenshot"}


def imagen_en_bytes(formato, ancho=1600, alto=1000, exif=None, color=(30, 90, 160)):
    imagen = Image.new("RGB", (ancho, alto), color)
    salida = io.BytesIO()
    if exif is not None:
        imagen.save(salida, format=formato, exif=exif)
    else:
        imagen.save(salida, format=formato)
    return salida.getvalue()


def exif_con_gps():
    exif = Image.Exif()
    exif[0x010F] = "Fabricante inventado"  # Make
    exif[0x0110] = "Telefono de Ilan"  # Model
    exif[0x8825] = {1: "S", 2: (34.0, 36.0, 0.0)}  # GPSInfo
    return exif.tobytes()


def procesar(contenido, carpeta, privado=False, aprobada=None, huella_anterior=None):
    return procesar_imagen_manual(contenido, "prueba", privado, aprobada, ALT, huella_anterior, carpeta)


def test_tipo_real_por_bytes():
    assert tipo_real(imagen_en_bytes("PNG")) == "png"
    assert tipo_real(imagen_en_bytes("JPEG")) == "jpeg"
    assert tipo_real(imagen_en_bytes("WEBP")) == "webp"
    assert tipo_real(b"GIF89a....") is None
    assert tipo_real(b"<svg></svg>") is None


def test_publico_genera_webp_1200_y_600_sin_metadatos(tmp_path):
    contenido = imagen_en_bytes("JPEG", exif=exif_con_gps())
    with Image.open(io.BytesIO(contenido)) as original:
        assert original.getexif()  # el origen sí tiene EXIF
    salida, huella, reprocesada = procesar(contenido, tmp_path)
    assert reprocesada is True
    assert huella == hash_corto(contenido)
    assert salida["origen"] == "manual"
    assert (salida["ancho"], salida["alto"]) == (1200, 750)
    assert salida["archivos"]["es"] == {"1200": "/proyectos/prueba-1200.webp", "600": "/proyectos/prueba-600.webp"}
    assert salida["archivos"]["en"] == salida["archivos"]["es"]
    for ancho in (1200, 600):
        crudo = (tmp_path / ("prueba-" + str(ancho) + ".webp")).read_bytes()
        assert b"Telefono" not in crudo and b"Exif" not in crudo and b"XMP" not in crudo
        with Image.open(io.BytesIO(crudo)) as webp:
            assert webp.format == "WEBP"
            assert webp.width == ancho
            assert not webp.getexif()
            assert "icc_profile" not in webp.info


def test_extension_no_importa_solo_los_bytes(tmp_path):
    with pytest.raises(ErrorImagen) as error:
        procesar(b"no soy una imagen aunque me llame captura.png", tmp_path)
    assert error.value.tipo == "imagen_invalida" and error.value.motivo == "formato"


def test_mas_de_5_mb_es_invalida(tmp_path):
    contenido = imagen_en_bytes("PNG") + b"\0" * BYTES_MAXIMOS
    with pytest.raises(ErrorImagen) as error:
        procesar(contenido, tmp_path)
    assert error.value.motivo == "tamaño"


def test_angosta_es_invalida(tmp_path):
    with pytest.raises(ErrorImagen) as error:
        procesar(imagen_en_bytes("PNG", ancho=640, alto=400), tmp_path)
    assert error.value.motivo == "ancho"


def test_privado_sin_aprobacion_o_con_hash_viejo(tmp_path):
    contenido = imagen_en_bytes("PNG")
    for aprobada in (None, "000000000000"):
        with pytest.raises(ErrorImagen) as error:
            procesar(contenido, tmp_path, privado=True, aprobada=aprobada)
        assert error.value.tipo == "imagen_sin_aprobar"
    assert list(tmp_path.iterdir()) == []


def test_privado_aprobado(tmp_path):
    contenido = imagen_en_bytes("PNG")
    salida, _, _ = procesar(contenido, tmp_path, privado=True, aprobada=hash_corto(contenido))
    assert salida["ancho"] == 1200


def test_sin_reproceso_si_el_origen_no_cambio(tmp_path):
    contenido = imagen_en_bytes("PNG")
    _, huella, _ = procesar(contenido, tmp_path)
    archivo = tmp_path / "prueba-1200.webp"
    archivo.write_bytes(archivo.read_bytes())  # mismo contenido; se fija que no se vuelva a escribir
    marca = archivo.stat().st_mtime_ns
    salida, _, reprocesada = procesar(contenido, tmp_path, huella_anterior=huella)
    assert reprocesada is False
    assert archivo.stat().st_mtime_ns == marca
    assert salida["ancho"] == 1200


def test_salida_deterministica(tmp_path):
    contenido = imagen_en_bytes("PNG", color=(200, 10, 10))
    procesar(contenido, tmp_path / "a")
    procesar(contenido, tmp_path / "b")
    for nombre in ("prueba-1200.webp", "prueba-600.webp"):
        assert (tmp_path / "a" / nombre).read_bytes() == (tmp_path / "b" / nombre).read_bytes()


def test_no_agranda_imagenes_entre_800_y_1200(tmp_path):
    salida, _, _ = procesar(imagen_en_bytes("PNG", ancho=1000, alto=625), tmp_path)
    assert (salida["ancho"], salida["alto"]) == (1000, 625)
