# -*- coding: utf-8 -*-
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
            id_externo_proveedor=f"mock-resend-{uuid4().hex[:12]}",
        )


class NotificadorResendBoceto(Notificador):
    """Adaptador de diseño para Resend (Fase BBAP, paso 1).

    Documentación de referencia:
    - Sitio oficial: https://resend.com
    - Documentación API: https://resend.com/docs
    - Precios verificados (octubre 2026): https://resend.com/pricing
      · Plan Free: 3 000 correos/mes, 100 correos/día.
      · Límite diario calculado según día calendario UTC.
      · Pausa de envíos al agotar cupo sin cobros automáticos.

    Requisitos pendientes para pasar a producción (Fase de Implementación):
    1. Registro y verificación DNS de dominio remitente propio por el propietario
       (registros SPF, DKIM y DMARC validados en la consola de Resend).
    2. Configuración de variable de entorno secreta:
       RESEND_API_KEY=<PLACEHOLDER>
       RESEND_FROM_EMAIL=notificaciones@<DOMINIO_VERIFICADO_PLACEHOLDER>
    """

    def __init__(
        self,
        api_key: str = "<PLACEHOLDER>",
        remitente: str = "noreply@plataforma360.ec",
    ) -> None:
        self.api_key = api_key
        self.remitente = remitente

    async def enviar_correo(
        self, correo: CorreoLoteNotificacion
    ) -> ResultadoDespacho:
        """Boceto descriptivo de llamada REST hacia api.resend.com/emails."""
        # En fase boceto, no se realizan llamadas HTTP reales
        return ResultadoDespacho(
            despacho_id=str(uuid4()),
            lote_id=correo.lote_id,
            destinatario_email=correo.destinatario.email,
            estado=EstadoEnvio.PENDIENTE,
            id_externo_proveedor="boceto-no-conectado",
            error_detalle="Proveedor Resend en fase de diseño; requiere dominio verificado y RESEND_API_KEY",
        )
