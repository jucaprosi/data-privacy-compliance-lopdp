# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa
# ¤roadmap
"""Implementación de prueba y adaptadores para el puerto Notificador."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from features.notificaciones.domain.models import (
    CorreoLoteNotificacion,
    EstadoEnvio,
    ResultadoDespacho,
)
from features.notificaciones.domain.puertos import Notificador


class NotificadorFalso(Notificador):
    """Implementación de prueba (In-Memory / Test Double) para el puerto Notificador.

    Permite validar la lógica de agrupación y reglas de negocio sin dependencias externas
    ni llamadas remotas de red.
    """

    def __init__(self, simular_fallo: bool = False) -> None:
        self.simular_fallo = simular_fallo
        self.correos_enviados: list[CorreoLoteNotificacion] = []

    async def enviar_correo(
        self, correo: CorreoLoteNotificacion
    ) -> ResultadoDespacho:
        # Regla de seguridad/integridad: no despachar sin destinatario o con email vacío
        if not correo.destinatario or not correo.destinatario.email.strip():
            return ResultadoDespacho(
                despacho_id=str(uuid4()),
                lote_id=correo.lote_id,
                destinatario_email="",
                estado=EstadoEnvio.DESCARTADO_SIN_DESTINATARIO,
                error_detalle="El correo no posee dirección de destinatario válida",
            )

        if self.simular_fallo:
            return ResultadoDespacho(
                despacho_id=str(uuid4()),
                lote_id=correo.lote_id,
                destinatario_email=correo.destinatario.email,
                estado=EstadoEnvio.FALLIDO,
                error_detalle="Fallo simulado en el proveedor de correo",
            )

        self.correos_enviados.append(correo)
        return ResultadoDespacho(
            despacho_id=str(uuid4()),
            lote_id=correo.lote_id,
            destinatario_email=correo.destinatario.email,
            estado=EstadoEnvio.ENVIADO,
            id_externo_proveedor=f"mock-notif-{uuid4().hex[:12]}",
        )


class NotificadorNoConfigurado(Notificador):
    """Adaptador fail-closed cuando no existe proveedor de correo configurado."""

    async def enviar_correo(
        self, correo: CorreoLoteNotificacion
    ) -> ResultadoDespacho:
        return ResultadoDespacho(
            despacho_id=str(uuid4()),
            lote_id=correo.lote_id,
            destinatario_email=correo.destinatario.email,
            estado=EstadoEnvio.PENDIENTE,
            id_externo_proveedor="sin-proveedor-configurado",
            error_detalle="proveedor de correo no configurado",
        )
