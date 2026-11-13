# ¤evidencias ¤evidencias-vigencia
"""Vigencia y visibilidad de un documento de evidencia (EVI-02): reglas puras, sin base ni almacén."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from features.evidencias.domain.models import ROLES_CONSULTA_DOCUMENTOS

ROL_DPO = "dpo"
ROLES_VISIBILIDAD_POSIBLES: tuple[str, ...] = tuple(ROLES_CONSULTA_DOCUMENTOS)


@dataclass
class AtributosDocumento:
    """Documento registrado con su vigencia y visibilidad (los documentos sin fila usan los valores por omisión)."""

    documento_id: str
    codigo: str
    nombre_archivo: str
    tipo_mime: str
    tamano_bytes: int
    sha256: str
    subido_en: datetime
    vence_en: Optional[date] = None
    visible_para: list[str] = field(default_factory=lambda: list(ROLES_VISIBILIDAD_POSIBLES))
    controles: list[int] = field(default_factory=list)
    clave_almacen: str = ""

    def vigente(self, hoy: date) -> bool:
        return esta_vigente(self.vence_en, hoy)


def esta_vigente(vence_en: Optional[date], hoy: date) -> bool:
    """Sin fecha de vencimiento siempre vigente; con ella, vigente hasta el día del vencimiento inclusive."""
    return vence_en is None or vence_en >= hoy


def mensaje_documentos_vencidos(vencidos: list[dict]) -> str:
    """Texto del rechazo al sellar: nombra cada documento vencido y los controles que dejó sin respaldo."""
    partes = []
    for d in vencidos:
        fecha = d["vence_en"].strftime("%d/%m/%Y")
        controles = ", ".join(f"P{c}" for c in d["controles"])
        partes.append(f"{d['nombre_archivo']} ({d['codigo']}), vencido el {fecha}, respaldaba {controles}")
    return (
        "No se puede sellar: hay controles cuyo único respaldo es un documento vencido. Renueva o reemplaza: "
        + "; ".join(partes)
        + "."
    )


def puede_ver(rol: str, visible_para: list[str] | tuple[str, ...]) -> bool:
    return rol in visible_para


def normalizar_visibilidad(roles: list[str]) -> list[str]:
    """Roles únicos y ordenados; el DPO siempre ve. Lanza ValueError si hay un rol que no consulta evidencias."""
    desconocidos = sorted(set(roles) - set(ROLES_VISIBILIDAD_POSIBLES))
    if desconocidos:
        raise ValueError(f"Roles sin acceso a las evidencias: {', '.join(desconocidos)}")
    return sorted(set(roles) | {ROL_DPO})
