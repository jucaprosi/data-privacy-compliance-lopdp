# -*- coding: utf-8 -*-
# ¤adpa
# ¤entorno-pruebas
# ¤seguridad
"""Guardia de destinatarios del entorno de pruebas (EP-08, PRD EVYDENTIA §5.5 e invariante 54).

En los entornos aislados (`APP_ENV=pruebas` y `APP_ENV=demo`, PRD §5.6) un correo solo sale si su
destinatario figura en `ENTORNO_CORREOS_PERMITIDOS`: direcciones exactas o `@dominio`, separadas por
comas. Con la lista vacía no sale ninguno. Fuera de esos entornos se delega sin cambios.
"""
from __future__ import annotations

import logging
import os
from enum import Enum
from uuid import uuid4

from features.notificaciones.domain.models import CorreoLoteNotificacion, ResultadoDespacho
from features.notificaciones.domain.puertos import Notificador

logger = logging.getLogger(__name__)

ENTORNOS_CON_GUARDIA = frozenset({"pruebas", "demo"})


class EstadoEntorno(str, Enum):
    """Estado propio del correo retenido por la guardia; nunca es igual a `EstadoEnvio.ENVIADO`."""
    RETENIDO_POR_ENTORNO = "retenido_por_entorno"


def _normalizar(texto: str) -> str:
    return texto.strip().lower()


def leer_permitidos(valor: str | None) -> frozenset[str]:
    """Interpreta `ENTORNO_CORREOS_PERMITIDOS`; entradas vacías se descartan."""
    return frozenset(e for e in (_normalizar(p) for p in (valor or "").split(",")) if e)


def destinatario_permitido(email: str, permitidos: frozenset[str]) -> bool:
    """Coincidencia exacta de dirección o de dominio completo (`@a.test` no admite `@a.test.com`)."""
    direccion = _normalizar(email)
    if not direccion or direccion.count("@") != 1:
        return False
    dominio = "@" + direccion.split("@", 1)[1]
    return direccion in permitidos or dominio in permitidos


class NotificadorEntornoPermitido(Notificador):
    """Envuelve otro `Notificador` y retiene los destinatarios no permitidos en los entornos aislados."""

    def __init__(
        self,
        interno: Notificador,
        *,
        entorno: str | None = None,
        permitidos: str | None = None,
    ) -> None:
        self.interno = interno
        self.entorno = _normalizar(entorno if entorno is not None else os.environ.get("APP_ENV", ""))
        self.permitidos = leer_permitidos(
            permitidos if permitidos is not None else os.environ.get("ENTORNO_CORREOS_PERMITIDOS", "")
        )

    @property
    def con_guardia(self) -> bool:
        return self.entorno in ENTORNOS_CON_GUARDIA

    async def enviar_correo(self, correo: CorreoLoteNotificacion) -> ResultadoDespacho:
        if not self.con_guardia or destinatario_permitido(correo.destinatario.email, self.permitidos):
            return await self.interno.enviar_correo(correo)
        # El registro no lleva la dirección retenida (invariante 29: observabilidad sin datos personales).
        logger.info("Correo retenido por el entorno %s; lote %s", self.entorno, correo.lote_id)
        return ResultadoDespacho(
            despacho_id=str(uuid4()),
            lote_id=correo.lote_id,
            destinatario_email=correo.destinatario.email,
            estado=EstadoEntorno.RETENIDO_POR_ENTORNO,  # type: ignore[arg-type]
            error_detalle="Destinatario fuera de ENTORNO_CORREOS_PERMITIDOS",
        )
