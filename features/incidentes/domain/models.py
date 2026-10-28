# ¤incidentes ¤rbac-tenant
"""Bitácora de incidentes de seguridad de la organización (INC-01).

Un incidente registrado no se edita ni se borra. Su huella SHA-256 se encadena por organización,
como la bitácora del DPO (DPO-01) y los resultados del diagnóstico (DIAG-03).

Los plazos de notificación (a la Superintendencia y a los titulares) siguen aplazados por
decisión del propietario (LEG-02): esta bitácora no calcula ninguno.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

HUELLA_GENESIS = "0" * 64
SEVERIDADES: tuple[str, ...] = ("Baja", "Media", "Alta", "Crítica")

# Decisión del coordinador (diseño propio, un solo sitio): la obligación de notificar y documentar
# es del responsable del tratamiento (art. 43 LOPDP), así que registran los roles de la
# organización; el DPO supervisa y asesora (art. 49) y consulta, sin funciones operativas (ORG-01).
ROLES_REGISTRO: tuple[str, ...] = ("admin_organizacion", "coordinador", "responsable_area", "implementador")
ROLES_CONSULTA: tuple[str, ...] = ROLES_REGISTRO + ("dpo",)


class FechaDeteccionFutura(ValueError):
    """La fecha de detección no puede ser posterior al momento del registro."""


@dataclass
class Incidente:
    id: str
    tenant_id: str
    secuencia: int
    fecha_deteccion: datetime
    titulo: str
    descripcion: str
    severidad: str
    afecta_datos_personales: bool
    categorias_datos: list[str]
    medidas_inmediatas: str
    registrado_por: str
    registrado_en: datetime
    huella_anterior: str = HUELLA_GENESIS
    huella: str = ""

    def contenido(self) -> dict[str, Any]:
        """Lo que se encadena: todo salvo la huella propia."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "secuencia": self.secuencia,
            "fecha_deteccion": self.fecha_deteccion.isoformat(),
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "severidad": self.severidad,
            "afecta_datos_personales": self.afecta_datos_personales,
            "categorias_datos": list(self.categorias_datos),
            "medidas_inmediatas": self.medidas_inmediatas,
            "registrado_por": self.registrado_por,
            "registrado_en": self.registrado_en.isoformat(),
            "huella_anterior": self.huella_anterior,
        }
