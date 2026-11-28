# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa
# ¤roadmap
"""Implementación de prueba y adaptadores para el puerto Notificador."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import smtplib
import ssl
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.message import EmailMessage
from enum import Enum
from typing import Callable
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


# === NOTIF-03 ===
# ¤seguridad Adaptador SMTP genérico: no conoce al proveedor; cambiar de proveedor es cambiar el secreto.
logger = logging.getLogger(__name__)

TOPE_HORA_POR_DEFECTO = 50
VENTANA_TOPE_S = 3600.0
TIMEOUT_SMTP_S = 10.0
CAMPOS_SMTP = ("host", "puerto", "usuario", "contrasena", "remitente")


class EstadoSmtp(str, Enum):
    """Estado propio del correo frenado por el tope; nunca es igual a `EstadoEnvio.ENVIADO` (como EstadoEntorno)."""
    TOPE = "tope"


class ErrorConfiguracionSmtp(Exception):
    """El puerto no admite TLS, el servidor no ofrece STARTTLS o el certificado no se verifica: no se envía nada."""


@dataclass(frozen=True)
class ConfigSmtp:
    """Contenido de `NOTIF_SMTP_CONFIG`. La contraseña no sale en `repr`."""
    host: str
    puerto: int
    usuario: str
    contrasena: str = field(repr=False)
    remitente: str
    tope_hora: int = TOPE_HORA_POR_DEFECTO


class VentanaTope:
    """Ventana deslizante en memoria: como máximo `tope` reservas por `ventana` segundos (por instancia)."""

    def __init__(self, tope: int, ventana: float = VENTANA_TOPE_S, reloj: Callable[[], float] = time.monotonic) -> None:
        self.tope, self.ventana, self.reloj = tope, ventana, reloj
        self._marcas: deque[float] = deque()
        self._cerrojo = threading.Lock()

    def reservar(self) -> bool:
        with self._cerrojo:
            ahora = self.reloj()
            while self._marcas and ahora - self._marcas[0] >= self.ventana:
                self._marcas.popleft()
            if len(self._marcas) >= self.tope:
                return False
            self._marcas.append(ahora)
            return True


class NotificadorSmtp(Notificador):
    """`smtplib` con TLS obligatorio: 465 con `SMTP_SSL` o 587 con `starttls()`, siempre con certificado verificado."""

    MODOS_POR_PUERTO: dict[int, str] = {465: "ssl", 587: "starttls"}
    TIMEOUT_S = TIMEOUT_SMTP_S

    def __init__(self, config: ConfigSmtp, *, contexto_ssl: ssl.SSLContext | None = None,
                 timeout: float | None = None, ventana: VentanaTope | None = None) -> None:
        self.config = config
        self._contexto_ssl = contexto_ssl
        self.timeout = self.TIMEOUT_S if timeout is None else timeout
        self.ventana = ventana or VentanaTope(config.tope_hora)

    def _contexto(self) -> ssl.SSLContext:
        return self._contexto_ssl or ssl.create_default_context()

    def _mensaje(self, correo: CorreoLoteNotificacion) -> EmailMessage:
        m = EmailMessage()
        m["Subject"], m["From"], m["To"] = correo.asunto, self.config.remitente, correo.destinatario.email.strip()
        m.set_content(correo.cuerpo_texto)
        if correo.cuerpo_html:
            m.add_alternative(correo.cuerpo_html, subtype="html")
        return m

    def _enviar(self, correo: CorreoLoteNotificacion) -> None:
        """Bloqueante: se ejecuta en un hilo. Cualquier fallo de TLS sube como error de configuración."""
        cfg, contexto = self.config, self._contexto()
        modo = self.MODOS_POR_PUERTO.get(cfg.puerto)
        mensaje = self._mensaje(correo)
        if modo == "ssl":
            with smtplib.SMTP_SSL(cfg.host, cfg.puerto, timeout=self.timeout, context=contexto) as s:
                s.login(cfg.usuario, cfg.contrasena)
                s.send_message(mensaje)
            return
        with smtplib.SMTP(cfg.host, cfg.puerto, timeout=self.timeout) as s:
            s.ehlo()
            if not s.has_extn("starttls"):
                raise ErrorConfiguracionSmtp("sin_starttls")
            s.starttls(context=contexto)
            s.ehlo()
            s.login(cfg.usuario, cfg.contrasena)
            s.send_message(mensaje)

    def _resultado(self, correo: CorreoLoteNotificacion, estado, detalle: str | None = None) -> ResultadoDespacho:
        return ResultadoDespacho(despacho_id=str(uuid4()), lote_id=correo.lote_id,
                                 destinatario_email=correo.destinatario.email if correo.destinatario else "",
                                 estado=estado, error_detalle=detalle)

    async def enviar_correo(self, correo: CorreoLoteNotificacion) -> ResultadoDespacho:
        if not correo.destinatario or not correo.destinatario.email.strip():
            return self._resultado(correo, EstadoEnvio.DESCARTADO_SIN_DESTINATARIO,
                                   "El correo no posee dirección de destinatario válida")
        if self.config.puerto not in self.MODOS_POR_PUERTO:
            return self._resultado(correo, EstadoEnvio.FALLIDO, "error_de_configuracion:puerto_sin_tls")
        if not self.ventana.reservar():
            return self._resultado(correo, EstadoSmtp.TOPE, "tope de correos por hora")  # type: ignore[arg-type]
        try:
            await asyncio.to_thread(self._enviar, correo)
        except (ErrorConfiguracionSmtp, ssl.SSLError, ssl.CertificateError) as exc:
            return self._resultado(correo, EstadoEnvio.FALLIDO, f"error_de_configuracion:{type(exc).__name__}")
        except Exception as exc:  # noqa: BLE001 - solo el tipo: el mensaje puede traer direcciones o texto del servidor
            return self._resultado(correo, EstadoEnvio.FALLIDO, type(exc).__name__)
        return self._resultado(correo, EstadoEnvio.ENVIADO)


def _validar_config(valor: str | None) -> "dict | str":
    """El diccionario validado, o un código corto del defecto (nunca el contenido)."""
    if not valor or not valor.strip():
        return "ausente"
    try:
        datos = json.loads(valor)
    except ValueError:
        return "no_es_json"
    if not isinstance(datos, dict):
        return "no_es_objeto"
    for campo in CAMPOS_SMTP:
        if campo not in datos:
            return f"falta_{campo}"
        if campo != "puerto" and not (isinstance(datos[campo], str) and datos[campo].strip()):
            return f"campo_invalido_{campo}"
    if isinstance(datos["puerto"], bool) or datos["puerto"] not in NotificadorSmtp.MODOS_POR_PUERTO:
        return "puerto_sin_tls"
    if "@" not in datos["remitente"]:
        return "campo_invalido_remitente"
    tope = datos.get("tope_hora", TOPE_HORA_POR_DEFECTO)
    if isinstance(tope, bool) or not isinstance(tope, int) or tope < 1:
        return "campo_invalido_tope_hora"
    return datos


def leer_config_smtp(valor: str | None) -> ConfigSmtp | None:
    """Interpreta `NOTIF_SMTP_CONFIG`; None si falta, no es JSON o le falta algo. Nunca registra el valor."""
    resultado = _validar_config(valor)
    if isinstance(resultado, dict):
        return ConfigSmtp(**{k: resultado[k] for k in (*CAMPOS_SMTP, "tope_hora") if k in resultado})
    if resultado != "ausente":
        logger.warning("NOTIF_SMTP_CONFIG no es válida (%s); sigue el notificador no configurado", resultado)
    return None


_SMTP_EN_USO: dict[str, "NotificadorSmtp | None"] = {}


def notificador_smtp_desde_entorno() -> NotificadorSmtp | None:
    """El notificador de `NOTIF_SMTP_CONFIG`, o None. Una instancia por valor: su tope por hora es de la instancia."""
    valor = os.environ.get("NOTIF_SMTP_CONFIG")
    if valor not in _SMTP_EN_USO:
        config = leer_config_smtp(valor)
        _SMTP_EN_USO.clear()
        _SMTP_EN_USO[valor] = NotificadorSmtp(config) if config else None
    return _SMTP_EN_USO[valor]
# === fin NOTIF-03 ===
