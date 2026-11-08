# ¤entorno-pruebas
"""Evidencias inventadas para el entorno de pruebas (EP-03): un PDF y un texto por organización.

Los bytes son deterministas: la misma organización produce siempre el mismo archivo y el mismo hash,
y eso hace idempotente la subida al bucket.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ObjetoSintetico:
    clave: str
    datos: bytes
    tipo: str


def _escapar_pdf(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def pdf_minimo(lineas: list[str]) -> bytes:
    """PDF 1.4 de una página con texto en Helvetica, sin dependencias. Solo caracteres ASCII."""
    contenido = "BT /F1 12 Tf 72 720 Td 16 TL\n"
    contenido += "".join(f"({_escapar_pdf(l)}) Tj T*\n" for l in lineas)
    contenido += "ET"
    flujo = contenido.encode("ascii", "replace")
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(flujo)).encode() + b" >>\nstream\n" + flujo + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    salida = bytearray(b"%PDF-1.4\n")
    desplazamientos = []
    for i, obj in enumerate(objetos, start=1):
        desplazamientos.append(len(salida))
        salida += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(salida)
    salida += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    salida += "".join(f"{d:010d} 00000 n \n" for d in desplazamientos).encode()
    salida += f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(salida)


def evidencias_de(org_id: str, nombre: str) -> list[ObjetoSintetico]:
    lineas = [
        "DOCUMENTO FICTICIO - ENTORNO DE PRUEBAS",
        f"Organizacion: {org_id}",
        "Politica de proteccion de datos (texto inventado).",
        "No contiene datos personales reales.",
    ]
    texto = (
        "DOCUMENTO FICTICIO - ENTORNO DE PRUEBAS\n"
        f"Organización: {nombre}\n"
        "Registro de actividades de tratamiento de ejemplo. Todo su contenido es inventado.\n"
    ).encode("utf-8")
    base = f"sintetico/{org_id}/evidencias"
    return [
        ObjetoSintetico(f"{base}/politica-ficticia.pdf", pdf_minimo(lineas), "application/pdf"),
        ObjetoSintetico(f"{base}/rat-ficticio.txt", texto, "text/plain; charset=utf-8"),
    ]
