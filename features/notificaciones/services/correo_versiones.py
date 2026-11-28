# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤notificaciones ¤adpa
"""NOTIF-03: correo de las versiones por revisar y de sus recordatorios (R2, R3, R4).

Los textos salen de NOTIF-02 (`domain/avisos.py`) por las mismas funciones que la bandeja: aquí solo se añaden el
asunto y el saludo. El registro lleva el id del aviso y el tipo de error, nunca destinatario, asunto ni cuerpo.
"""
from __future__ import annotations

import logging
import re
from html import escape
from typing import Sequence

from features.notificaciones.domain import avisos as av
from features.notificaciones.domain.models import (
    CanalNotificacion,
    CorreoLoteNotificacion,
    Destinatario,
    EstadoEnvio,
)
from features.notificaciones.domain.puertos import Notificador
from features.notificaciones.services.adaptadores import (
    EstadoSmtp,
    NotificadorNoConfigurado,
    notificador_smtp_desde_entorno,
)
from features.notificaciones.services.destinatarios_entorno import EstadoEntorno, NotificadorEntornoPermitido

logger = logging.getLogger(__name__)

MOTIVO_DEL_CORREO = "Recibes este correo porque tienes el permiso de revisión técnica de la Biblioteca."


def notificador_de_correo() -> Notificador:
    """El SMTP de `NOTIF_SMTP_CONFIG` si es válido; si no, el no configurado. Siempre tras la guardia del entorno (R5)."""
    smtp = notificador_smtp_desde_entorno()
    return NotificadorEntornoPermitido(smtp if smtp is not None else NotificadorNoConfigurado())


def _linea(texto: str | None) -> str:
    """Una sola línea sin saltos ni espacios dobles: nada de lo que viene de una persona rompe la cabecera."""
    return re.sub(r"\s+", " ", texto or "").strip()


def asunto(plantilla: str, recordatorio: bool = False) -> str:
    if recordatorio:
        return f"Recordatorio: {_linea(plantilla)} sigue por revisar"
    return av.titulo(_linea(plantilla))


def cuerpo(*, nombre: str, plantilla: str, motivo: str, enlace: str, recordatorio: str | None = None) -> str:
    """R3: el mismo cuerpo para el aviso y el recordatorio; el recordatorio añade su texto tras la línea de motivo."""
    saludo = f"Hola, {_linea(nombre)}:" if _linea(nombre) else "Hola:"
    lineas = [saludo, f"Hay una versión nueva de la plantilla «{_linea(plantilla)}» pendiente de revisión técnica.",
              _linea(motivo)]
    if recordatorio:
        lineas.append(_linea(recordatorio))
    lineas += [f"Revísala en la plataforma: {_linea(enlace)}.", MOTIVO_DEL_CORREO]
    return " ".join(lineas)


def _html(texto: str, enlace: str) -> str:
    seguro, url = escape(texto), escape(_linea(enlace))
    vinculo = '<a href="' + url + '">' + url + "</a>"
    return "<html><body><p>" + seguro.replace(url, vinculo) + "</p></body></html>"


def construir_correo(*, aviso_id: str, destinatario: Destinatario, plantilla: str, motivo: str, enlace: str,
                     recordatorio: str | None = None) -> CorreoLoteNotificacion:
    """El correo de un aviso nuevo (sin `recordatorio`) o de un recordatorio. `lote_id` es el id del aviso."""
    texto = cuerpo(nombre=destinatario.nombre, plantilla=plantilla, motivo=motivo, enlace=enlace,
                   recordatorio=recordatorio)
    return CorreoLoteNotificacion(
        lote_id=aviso_id, destinatario=destinatario, canal=CanalNotificacion.CORREO,
        asunto=asunto(plantilla, recordatorio is not None), cuerpo_texto=texto, cuerpo_html=_html(texto, enlace),
        tareas=())


async def enviar_correos(notificador: Notificador, correos: Sequence[CorreoLoteNotificacion]) -> dict[str, int]:
    """Un intento por correo, sin reintentos (R1e, R4). Nunca lanza: el aviso de la campana ya está confirmado."""
    cuenta = {"enviados": 0, "tope": 0, "retenidos": 0, "sin_proveedor": 0, "fallidos": 0}
    for correo in correos:
        try:
            r = await notificador.enviar_correo(correo)
        except Exception as exc:  # noqa: BLE001 - solo el tipo del error: su mensaje puede traer datos personales
            logger.warning("Correo del aviso %s sin enviar: %s", correo.lote_id, type(exc).__name__)
            cuenta["fallidos"] += 1
            continue
        if r.estado == EstadoEnvio.ENVIADO:
            cuenta["enviados"] += 1
        elif r.estado == EstadoSmtp.TOPE:
            logger.warning("Correo del aviso %s sin enviar: TOPE", correo.lote_id)
            cuenta["tope"] += 1
        elif r.estado == EstadoEntorno.RETENIDO_POR_ENTORNO:
            cuenta["retenidos"] += 1
        elif r.estado == EstadoEnvio.PENDIENTE:
            cuenta["sin_proveedor"] += 1
        else:
            logger.warning("Correo del aviso %s sin enviar: %s", correo.lote_id, r.error_detalle or r.estado)
            cuenta["fallidos"] += 1
    logger.info("NOTIF-03: correos de avisos %s", cuenta)
    return cuenta
