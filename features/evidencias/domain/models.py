"""Modelos de dominio del Módulo de Evidencias (Bóveda de Evidencias)."""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum

CONTROL_ID_MIN: int = 1
CONTROL_ID_MAX: int = 80
NORMATIVA_POR_DEFECTO: str = "LOPDP"
TIPO_MIME_POR_DEFECTO: str = "application/octet-stream"

_PATRON_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


def gen_id() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NivelCalidadEvidencia(str, Enum):
    E0_SIN_EVIDENCIA = "E0_SIN_EVIDENCIA"
    E1_DOCUMENTADA = "E1_DOCUMENTADA"
    E2_IMPLEMENTADA = "E2_IMPLEMENTADA"
    E3_PROBADA = "E3_PROBADA"


class EvidenciaError(Exception):
    """Error base de la sala de evidencias."""


class EvidenciaNoEncontrada(EvidenciaError):
    """La evidencia no existe o pertenece a otro tenant."""


class ControlFueraDeRango(EvidenciaError, ValueError):
    """Identificador de control del assessment fuera del rango permitido."""


class HashInvalido(EvidenciaError, ValueError):
    """El valor no es un SHA-256 hexadecimal de 64 caracteres."""


def es_sha256_valido(valor: str) -> bool:
    return bool(_PATRON_SHA256.fullmatch(valor.strip()))


def normalizar_sha256(valor: str) -> str:
    """Valida y normaliza un SHA-256 hexadecimal a minúsculas."""
    limpio = valor.strip()
    if not _PATRON_SHA256.fullmatch(limpio):
        raise HashInvalido("sha256_hash debe tener exactamente 64 caracteres hexadecimales")
    return limpio.lower()


def validar_control_id(control_id: int) -> int:
    if isinstance(control_id, bool) or not isinstance(control_id, int):
        raise ControlFueraDeRango(f"Identificador de control inválido: {control_id!r}")
    if not CONTROL_ID_MIN <= control_id <= CONTROL_ID_MAX:
        raise ControlFueraDeRango(
            f"El control {control_id} está fuera del rango {CONTROL_ID_MIN}..{CONTROL_ID_MAX}"
        )
    return control_id


def normalizar_controles(controles: list[int]) -> list[int]:
    """Valida el rango de cada control y devuelve la lista ordenada sin duplicados."""
    return sorted({validar_control_id(c) for c in controles})


@dataclass
class EvidenciaRegistro:
    id: str = field(default_factory=gen_id)
    tenant_id: str = ""
    codigo: str = ""  # EVD-AAAA-NNNN
    nombre_archivo: str = ""
    sha256_hash: str = ""
    storage_path: str = ""
    calidad: NivelCalidadEvidencia = NivelCalidadEvidencia.E1_DOCUMENTADA
    fecha_vigencia: date = field(default_factory=date.today)
    propietario_id: str = ""
    controles_vinculados: list[int] = field(default_factory=list)
    normativa: str = NORMATIVA_POR_DEFECTO
    tamano_bytes: int = 0
    tipo_mime: str = TIPO_MIME_POR_DEFECTO
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        self.controles_vinculados = normalizar_controles(self.controles_vinculados)
        if self.sha256_hash:
            self.sha256_hash = normalizar_sha256(self.sha256_hash)
        self.normativa = self.normativa.strip() or NORMATIVA_POR_DEFECTO
        if self.tamano_bytes < 0:
            raise ValueError("tamano_bytes no puede ser negativo")
