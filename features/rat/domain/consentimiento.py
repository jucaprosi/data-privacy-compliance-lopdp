# ¤rat ¤evidencias
"""Modelos de colectivos y consentimientos agregados (RAT-07). Nunca datos de un titular individual.

Contrato: governance/especificaciones/RAT-07.md §3 (R1 minimización, R2 agregación).
"""
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from features.rat.domain.models import BaseLegitimacion

# R1: nombres de campo que identifican a una persona; se rechazan antes de validar el modelo.
CAMPOS_IDENTIFICADORES = frozenset({
    "email", "correo", "correo_electronico", "cedula", "cedula_identidad", "identificacion", "ruc",
    "nombre_titular", "nombres", "apellidos", "telefono", "telefono_titular", "celular", "direccion",
    "titular", "titular_id", "pasaporte",
})

Canal = Literal["web", "presencial", "telefono", "otro"]


def campos_identificadores_presentes(cuerpo: dict) -> list[str]:
    """Campos del cuerpo que son identificadores de un titular (comparación sin mayúsculas ni espacios)."""
    return sorted(k for k in cuerpo if str(k).strip().lower() in CAMPOS_IDENTIFICADORES)


class ColectivoEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str = Field(min_length=1, max_length=120)
    base_legitimacion: BaseLegitimacion
    texto_version: str | None = Field(default=None, max_length=16)

    @model_validator(mode="after")
    def _version_solo_con_consentimiento(self):
        if self.base_legitimacion != BaseLegitimacion.CONSENTIMIENTO and self.texto_version:
            raise ValueError("La versión del texto solo aplica si la base es el consentimiento.")
        return self


class RegistroEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fecha: date
    canal: Canal
    cantidad: int = Field(gt=0)
    texto_version: str | None = Field(default=None, max_length=16)
