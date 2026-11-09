# -*- coding: utf-8 -*-
# ¤demo
# ¤rbac-tenant
"""Las seis personas de la demo, en el orden fijo de UX_DEMO_EVYDENTIA.md §2."""
from __future__ import annotations

from dataclasses import dataclass

#: Orden del ciclo que se enseña. El primero es la persona de arranque.
ORDEN_DE_ROLES: tuple[str, ...] = (
    "admin_organizacion",
    "dpo",
    "coordinador",
    "implementador",
    "responsable_area",
    "auditor",
)

ETIQUETAS: dict[str, str] = {
    "admin_organizacion": "Administrador de la organización",
    "dpo": "DPO",
    "coordinador": "Coordinador",
    "implementador": "Implementador",
    "responsable_area": "Responsable de área",
    "auditor": "Auditor",
}

ROL_INICIAL = ORDEN_DE_ROLES[0]


@dataclass(frozen=True)
class PersonaDemo:
    usuario_id: str
    nombre: str
    rol: str
    rol_etiqueta: str
    unidad: str | None = None

    def a_dict(self) -> dict[str, str | None]:
        return {
            "usuario_id": self.usuario_id,
            "nombre": self.nombre,
            "rol": self.rol,
            "rol_etiqueta": self.rol_etiqueta,
            "unidad": self.unidad,
        }


def ordenar(personas: list[PersonaDemo]) -> list[PersonaDemo]:
    """Ordena por el ciclo fijo; un rol desconocido va al final."""

    def posicion(p: PersonaDemo) -> int:
        return ORDEN_DE_ROLES.index(p.rol) if p.rol in ORDEN_DE_ROLES else len(ORDEN_DE_ROLES)

    return sorted(personas, key=posicion)
