# ¤entorno-pruebas
"""Clips de video sintéticos para la videovigilancia (EP-03).

Genera un AVI sin comprimir (RIFF, BI_RGB de 24 bits) con un único flujo de video: barras de color
que se desplazan un paso por cuadro. No hay flujo de audio, ni personas, ni imágenes externas. Todo
es determinista: los mismos parámetros dan los mismos bytes.
"""
from __future__ import annotations

import struct

from scripts.datos_sinteticos.evidencias import ObjetoSintetico

BARRAS = (
    (255, 255, 255), (0, 255, 255), (255, 255, 0), (0, 255, 0),
    (255, 0, 255), (0, 0, 255), (255, 0, 0), (0, 0, 0),
)  # RGB


def _trozo(fourcc: bytes, datos: bytes) -> bytes:
    relleno = b"\0" if len(datos) % 2 else b""
    return fourcc + struct.pack("<I", len(datos)) + datos + relleno


def _lista(tipo: bytes, datos: bytes) -> bytes:
    return _trozo(b"LIST", tipo + datos)


def _cuadro(ancho: int, alto: int, desplazamiento: int) -> bytes:
    fila = bytearray()
    for x in range(ancho):
        r, g, b = BARRAS[((x + desplazamiento) * len(BARRAS) // ancho) % len(BARRAS)]
        fila += bytes((b, g, r))  # BGR
    fila += b"\0" * ((4 - len(fila) % 4) % 4)
    return bytes(fila) * alto


def clip_patron(ancho: int = 64, alto: int = 48, cuadros: int = 10, fps: int = 5) -> bytes:
    tam_cuadro = len(_cuadro(ancho, alto, 0))
    avih = struct.pack(
        "<10I4I", 1_000_000 // fps, tam_cuadro * fps, 0, 0x10, cuadros, 0, 1, tam_cuadro,
        ancho, alto, 0, 0, 0, 0,
    )
    strh = b"vids" + b"DIB " + struct.pack(
        "<IHHIIIIIIIi4h", 0, 0, 0, 0, 1, fps, 0, cuadros, tam_cuadro, 0xFFFFFFFF, 0, 0, 0, ancho, alto,
    )
    strf = struct.pack("<IiiHHIIiiII", 40, ancho, alto, 1, 24, 0, tam_cuadro, 0, 0, 0, 0)
    hdrl = _lista(b"hdrl", _trozo(b"avih", avih) + _lista(b"strl", _trozo(b"strh", strh) + _trozo(b"strf", strf)))
    movi = _lista(b"movi", b"".join(_trozo(b"00db", _cuadro(ancho, alto, i)) for i in range(cuadros)))
    cuerpo = b"AVI " + hdrl + movi
    return b"RIFF" + struct.pack("<I", len(cuerpo)) + cuerpo


def tiene_audio(datos: bytes) -> bool:
    """Verdadero si algún encabezado de flujo (`strh`) es de audio (`auds`)."""
    i = datos.find(b"strh")
    while i != -1:
        if datos[i + 8:i + 12] == b"auds":
            return True
        i = datos.find(b"strh", i + 4)
    return False


def clips_de(org_id: str) -> list[ObjetoSintetico]:
    base = f"sintetico/{org_id}/videovigilancia"
    return [
        ObjetoSintetico(f"{base}/camara-ficticia-1.avi", clip_patron(), "video/x-msvideo"),
        ObjetoSintetico(f"{base}/camara-ficticia-2.avi", clip_patron(cuadros=6, fps=3), "video/x-msvideo"),
    ]
