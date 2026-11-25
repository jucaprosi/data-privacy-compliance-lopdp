# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤arbitro
"""BIB-410: leyenda de redacción y aprobación de una versión publicada (governance/especificaciones/BIB-410.md).

Puro: no lee base ni reloj. Recibe los nombres visibles (nunca el correo) y la fecha de la revisión técnica aprobada.
Sin aprobación registrada no hay leyenda: nunca se escribe «aprobada por —».
"""
from __future__ import annotations

from datetime import date, datetime

MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre")
CLAVE_PIE = "_pie_plantilla"  # clave reservada de la instantánea: el pie lo decide la instantánea, no el generador
PIE_AVISO = "La aprobación es de la plantilla, no de este documento."


# ¤adpa
def fecha_larga(dia: date | datetime) -> str:
    """«25 de noviembre de 2026»."""
    return f"{dia.day} de {MESES[dia.month - 1]} de {dia.year}"


# ¤adpa
def _nombres(nombres: list[str]) -> str:
    limpios = [n.strip() for n in nombres if n and n.strip()]
    if len(limpios) <= 1:
        return "".join(limpios)
    return ", ".join(limpios[:-1]) + " y " + limpios[-1]


# ¤adpa
def leyenda_de(estado: str, redactada_por: str, autores: list[str], aprobador: str | None,
               aprobada_en: date | datetime | None) -> dict | None:
    """R1 a R3. `autores` son nombres visibles. `None` si la versión no está publicada o no tiene aprobación registrada."""
    nombre = (aprobador or "").strip()
    if estado != "publicada" or not nombre or aprobada_en is None:
        return None
    fecha = fecha_larga(aprobada_en)
    if redactada_por == "ia":
        return {"redaccion": "ia", "aprobada_por": nombre, "aprobada_en": fecha,
                "texto": f"Redactada con IA y aprobada por {nombre} el {fecha}."}
    autor = _nombres(autores)
    if not autor:
        return None
    return {"redaccion": "persona", "aprobada_por": nombre, "aprobada_en": fecha,
            "texto": f"Redactada por {autor} y aprobada por {nombre} el {fecha}."}


# ¤adpa
def pie_de_plantilla(codigo: str, version: str, leyenda: dict) -> str:
    """R4: pie de cada DOCX y XLSX generado desde una versión publicada; sale del texto de la leyenda."""
    texto = leyenda["texto"]
    return f"Plantilla del catálogo {codigo} v{version}, {texto[0].lower()}{texto[1:]} {PIE_AVISO}"
