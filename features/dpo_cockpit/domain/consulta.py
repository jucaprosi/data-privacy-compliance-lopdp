# ¤dpo-cockpit ¤evidencias
"""Dominio de las consultas de la organización al DPO (DPO-03): entidades, estados y huella del hilo.

Puro: sin base de datos. La huella canónica del hilo es determinista (mensajes por secuencia,
JSON con claves ordenadas, UTF-8) para que cualquiera pueda recomputarla y verificarla.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

ESTADO_ABIERTA = "abierta"
ESTADO_RESPONDIDA = "respondida"
ESTADO_CERRADA = "cerrada"
ESTADOS = (ESTADO_ABIERTA, ESTADO_RESPONDIDA, ESTADO_CERRADA)
ASUNTO_MAX = 120
ROL_DPO = "dpo"
ROLES_QUE_VEN_TODAS = ("dpo", "admin_organizacion", "coordinador")


def nuevo_id() -> str:
    return str(uuid.uuid4())


def ahora() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class MensajeConsulta:
    consulta_id: str
    autor_id: str
    autor_rol: str
    texto: str
    secuencia: int = 0
    id: str = field(default_factory=nuevo_id)
    creado_en: datetime = field(default_factory=ahora)
    autor_nombre: Optional[str] = None  # se resuelve al leer; nunca se guarda (dato personal)


@dataclass
class Consulta:
    tenant_id: str
    asunto: str
    creado_por: str
    id: str = field(default_factory=nuevo_id)
    estado: str = ESTADO_ABIERTA
    creado_en: datetime = field(default_factory=ahora)
    cerrada_en: Optional[datetime] = None
    dictamen_id: Optional[str] = None
    evidencia_sha256: Optional[str] = None
    mensajes: list[MensajeConsulta] = field(default_factory=list)


def normalizar_texto(valor: Optional[str]) -> str:
    return (valor or "").strip()


def hilo_canonico(consulta_id: str, asunto: str, mensajes: list[MensajeConsulta]) -> bytes:
    """Bytes canónicos del hilo: mensajes por secuencia, claves ordenadas, UTF-8 sin escapes."""
    ordenados = sorted(mensajes, key=lambda m: m.secuencia)
    cuerpo = {
        "consulta_id": consulta_id,
        "asunto": asunto,
        "mensajes": [
            {
                "secuencia": m.secuencia,
                "autor_id": m.autor_id,
                "autor_rol": m.autor_rol,
                "texto": m.texto,
                "creado_en": m.creado_en.astimezone(timezone.utc).isoformat(),
            }
            for m in ordenados
        ],
    }
    return json.dumps(cuerpo, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def huella_hilo(consulta_id: str, asunto: str, mensajes: list[MensajeConsulta]) -> str:
    return hashlib.sha256(hilo_canonico(consulta_id, asunto, mensajes)).hexdigest()


def hilo_es_integro(consulta: Consulta) -> bool:
    """True si la huella guardada al cerrar coincide con la del hilo actual."""
    if not consulta.evidencia_sha256:
        return False
    return huella_hilo(consulta.id, consulta.asunto, consulta.mensajes) == consulta.evidencia_sha256
