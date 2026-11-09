# -*- coding: utf-8 -*-
# ¤demo
"""Forma congelada de `GET /api/v1/demo/estado` y del 201 de `POST /api/v1/demo/entrar`.

Nunca lleva el correo ni el `sub` del vendedor (pilar 10): solo la organización ficticia, la
persona activa, las seis personas y el vencimiento.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from features.demo.domain.personas import PersonaDemo, ordenar

CAMPOS_ESTADO: tuple[str, ...] = ("demo", "organizacion", "persona_activa", "personas", "vence_en")
CAMPOS_ORGANIZACION: tuple[str, ...] = ("tenant_id", "nombre")
CAMPOS_PERSONA: tuple[str, ...] = ("usuario_id", "nombre", "rol", "rol_etiqueta", "unidad")


@dataclass(frozen=True)
class EstadoDemo:
    tenant_id: str
    nombre_organizacion: str
    persona_activa: PersonaDemo
    personas: tuple[PersonaDemo, ...]
    vence_en: datetime | None = None

    def a_dict(self) -> dict:
        return {
            "demo": True,
            "organizacion": {"tenant_id": self.tenant_id, "nombre": self.nombre_organizacion},
            "persona_activa": self.persona_activa.a_dict(),
            "personas": [p.a_dict() for p in ordenar(list(self.personas))],
            "vence_en": self.vence_en.isoformat() if self.vence_en else None,
        }
