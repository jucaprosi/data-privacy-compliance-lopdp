# -*- coding: utf-8 -*-
# ¤demo
# ¤adpa
"""Códigos de error de la sala demo (FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md §1.7, PRD §5.6.1).

Se registran en CATALOGO_ERRORES al importarse. El cuerpo de respuesta es `{codigo, mensaje}`.
"""
from __future__ import annotations

from app_core.errors import CATALOGO_ERRORES, CodigoErrorNegocio

DEMO_NO_AUTORIZADO = CodigoErrorNegocio("DEMO_NO_AUTORIZADO", 403, "No autorizado para la demo")
DEMO_OCUPADA = CodigoErrorNegocio("DEMO_OCUPADA", 409, "Demo ocupada, intenta en unos minutos")
DEMO_VENCIDA = CodigoErrorNegocio("DEMO_VENCIDA", 401, "Tu demostración terminó")
DEMO_PERSONA_AJENA = CodigoErrorNegocio("DEMO_PERSONA_AJENA", 403, "Esa persona no pertenece a tu demostración")
DEMO_NO_DISPONIBLE = CodigoErrorNegocio("DEMO_NO_DISPONIBLE", 503, "No pudimos preparar la demo; intenta de nuevo")

CODIGOS = (DEMO_NO_AUTORIZADO, DEMO_OCUPADA, DEMO_VENCIDA, DEMO_PERSONA_AJENA, DEMO_NO_DISPONIBLE)


class ErrorDemo(Exception):
    """Error de negocio de la demo; `cuerpo()` es la respuesta HTTP congelada."""

    def __init__(self, codigo: CodigoErrorNegocio) -> None:
        super().__init__(codigo.mensaje_defecto)
        self.codigo = codigo

    @property
    def status_code(self) -> int:
        return self.codigo.status_code

    def cuerpo(self) -> dict[str, str]:
        return {"codigo": self.codigo.codigo, "mensaje": self.codigo.mensaje_defecto}


def registrar(*codigos: CodigoErrorNegocio) -> None:
    """Añade los códigos al catálogo común; un código ya registrado distinto es un error de diseño."""
    for codigo in codigos:
        previo = CATALOGO_ERRORES.get(codigo.codigo)
        if previo is not None and previo != codigo:
            raise ValueError(f"Código de error duplicado: {codigo.codigo}")
        CATALOGO_ERRORES[codigo.codigo] = codigo


registrar(*CODIGOS)
