# ¤¤developer-architect ¤derechos ¤seguridad ¤adpa
"""Motor del portal público de solicitudes de titulares por organización (DER-02).

Contrato: governance/especificaciones/DER-02.md
- R1 Mínimo: derecho, nombre, correo y descripción; sin adjuntos.
- R2 Seguimiento: devuelve estado, recibida_en, respondida_en; nunca respuesta ni datos privados.
- R3 No enumeración: 404 idéntico para slug inexistente, inactivo o código ajeno.
- R4 Tasa: 5 solicitudes por IP y hora.
"""
from __future__ import annotations

import hashlib
import os
import re
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import ErrorNegocio
from features.derechos_arco.domain.plazos import TIPOS_ACTIVOS, TipoSolicitud

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_DESCRIPCION = 4000
MAX_NOMBRE = 200
TASA_LIMITE_IP_HORA = 5
VENTANA_HORA_SEGUNDOS = 3600

# Almacén de tasa por IP en memoria para entornos locales / pruebas
_REGISTRO_IPS_MEMORIA: Dict[str, List[float]] = {}


def _reloj_actual() -> float:
    return time.time()


def limpiar_registro_ips() -> None:
    """Utilidad para pruebas: resetea el limitador de tasa."""
    _REGISTRO_IPS_MEMORIA.clear()


def verificar_tasa_ip(ip: str, reloj: Callable[[], float] = _reloj_actual) -> None:
    """Comprueba si la IP superó el límite de 5 solicitudes por hora (R4)."""
    ahora = reloj()
    limite_tiempo = ahora - VENTANA_HORA_SEGUNDOS
    peticiones = [t for t in _REGISTRO_IPS_MEMORIA.get(ip, []) if t > limite_tiempo]
    if len(peticiones) >= TASA_LIMITE_IP_HORA:
        raise ErrorNegocio("PORTAL_LIMITE")


def registrar_peticion_ip(ip: str, reloj: Callable[[], float] = _reloj_actual) -> None:
    """Registra una solicitud exitosa para el contador de la IP."""
    ahora = reloj()
    limite_tiempo = ahora - VENTANA_HORA_SEGUNDOS
    peticiones = [t for t in _REGISTRO_IPS_MEMORIA.get(ip, []) if t > limite_tiempo]
    peticiones.append(ahora)
    _REGISTRO_IPS_MEMORIA[ip] = peticiones


async def obtener_portal_publico(session: AsyncSession, slug: str) -> dict:
    """Devuelve la información pública del portal por slug (R3: 404 uniforme)."""
    slug_limpio = (slug or "").strip().lower()
    res = await session.execute(
        text("SELECT tenant_id, nombre_comercial, activo, texto_bienvenida FROM resolver_portal_por_slug(:s)"),
        {"s": slug_limpio},
    )
    fila = res.mappings().first()
    if not fila or not fila["activo"]:
        raise HTTPException(status_code=404, detail="No encontrado")

    return {
        "organizacion": fila["nombre_comercial"] or "Organización",
        "derechos": [t.value for t in TIPOS_ACTIVOS],
        "texto": fila["texto_bienvenida"] or "",
    }


async def crear_solicitud_desde_portal(
    session: AsyncSession,
    slug: str,
    ip: str,
    derecho: str,
    nombre: str,
    email: str,
    descripcion: str,
) -> dict:
    """Crea una solicitud pública desde el portal externo respetando límites y RLS."""
    # 1. Límite de tasa por IP (R4)
    verificar_tasa_ip(ip)

    # 2. Validaciones de entrada
    nombre_limpio = (nombre or "").strip()
    if not nombre_limpio or len(nombre_limpio) > MAX_NOMBRE:
        raise HTTPException(status_code=422, detail="Nombre inválido o demasiado largo")

    email_limpio = (email or "").strip().lower()
    if not email_limpio or not EMAIL_REGEX.match(email_limpio):
        raise HTTPException(status_code=422, detail="Email con formato inválido")

    desc_limpia = (descripcion or "").strip()
    if len(desc_limpia) > MAX_DESCRIPCION:
        raise HTTPException(status_code=422, detail="Descripción excede los 4.000 caracteres")

    tipo_str = (derecho or "").strip().upper()
    try:
        tipo = TipoSolicitud(tipo_str)
        if tipo not in TIPOS_ACTIVOS:
            raise ValueError()
    except Exception:
        raise HTTPException(status_code=422, detail="Derecho fuera del catálogo activo")

    # 3. Resolver slug y tenant
    slug_limpio = (slug or "").strip().lower()
    res = await session.execute(
        text("SELECT tenant_id, activo FROM resolver_portal_por_slug(:s)"),
        {"s": slug_limpio},
    )
    fila = res.mappings().first()
    if not fila or not fila["activo"]:
        raise HTTPException(status_code=404, detail="No encontrado")

    tenant_id = fila["tenant_id"]

    # 4. Generar código seguro de seguimiento y su hash SHA-256
    codigo_aleatorio = secrets.token_hex(16)
    codigo_seguimiento = f"sol_{codigo_aleatorio}"
    codigo_hash = hashlib.sha256(codigo_seguimiento.encode("utf-8")).hexdigest()

    # 5. Insertar mediante función SECURITY DEFINER sin abrir RLS
    await session.execute(
        text(
            "SELECT crear_solicitud_portal(:t, :tipo, :nombre, :email, :desc, :hash)"
        ),
        {
            "t": tenant_id,
            "tipo": tipo.value,
            "nombre": nombre_limpio,
            "email": email_limpio,
            "desc": desc_limpia,
            "hash": codigo_hash,
        },
    )

    # 6. Anotar uso para la IP
    registrar_peticion_ip(ip)

    return {"codigo": codigo_seguimiento}


async def consultar_seguimiento_portal(session: AsyncSession, codigo: str) -> dict:
    """Consulta el estado público de una solicitud por su código de seguimiento (R2 y R3)."""
    cod_limpio = (codigo or "").strip()
    if not cod_limpio:
        raise HTTPException(status_code=404, detail="No encontrado")

    cod_hash = hashlib.sha256(cod_limpio.encode("utf-8")).hexdigest()
    res = await session.execute(
        text("SELECT estado, recibida_en, respondida_en FROM consultar_seguimiento_solicitud(:h)"),
        {"h": cod_hash},
    )
    fila = res.mappings().first()
    if not fila:
        raise HTTPException(status_code=404, detail="No encontrado")

    recibida_en = fila["recibida_en"]
    respondida_en = fila["respondida_en"]

    # Invariante: Solo estado y fechas; nunca texto de respuesta ni datos de otros titulares.
    return {
        "estado": fila["estado"],
        "recibida_en": recibida_en.isoformat() if isinstance(recibida_en, datetime) else str(recibida_en or ""),
        "respondida_en": respondida_en.isoformat() if isinstance(respondida_en, datetime) else (str(respondida_en) if respondida_en else None),
    }


async def configurar_portal(
    session: AsyncSession,
    tenant_id: str,
    activo: bool,
    slug: str,
    texto_bienvenida: Optional[str] = None,
) -> dict:
    """Configura el portal público para la organización actual (rol admin_organizacion)."""
    slug_limpio = (slug or "").strip().lower()
    if not slug_limpio or not re.match(r"^[a-z0-9][a-z0-9_-]{2,47}$", slug_limpio):
        raise HTTPException(status_code=422, detail="Slug inválido (3-48 caracteres alfanuméricos)")

    # Comprobar unicidad de slug entre otros tenants
    ver_slug = await session.execute(
        text("SELECT tenant_id FROM portal_config WHERE slug = :s AND tenant_id <> :t"),
        {"s": slug_limpio, "t": tenant_id},
    )
    if ver_slug.first():
        raise HTTPException(status_code=409, detail="Slug ya en uso por otra organización")

    await session.execute(
        text(
            """
            INSERT INTO portal_config (tenant_id, activo, slug, texto_bienvenida)
            VALUES (:t, :a, :s, :texto)
            ON CONFLICT (tenant_id) DO UPDATE
            SET activo = EXCLUDED.activo,
                slug = EXCLUDED.slug,
                texto_bienvenida = EXCLUDED.texto_bienvenida;
            """
        ),
        {
            "t": tenant_id,
            "a": activo,
            "s": slug_limpio,
            "texto": (texto_bienvenida or "").strip() or None,
        },
    )
    return {"ok": True, "slug": slug_limpio, "activo": activo}


async def obtener_configuracion_portal(session: AsyncSession, tenant_id: str) -> Optional[dict]:
    """Obtiene la configuración del portal para la organización del usuario."""
    res = await session.execute(
        text("SELECT tenant_id, activo, slug, texto_bienvenida FROM portal_config WHERE tenant_id = :t"),
        {"t": tenant_id},
    )
    fila = res.mappings().first()
    if not fila:
        return None
    return {
        "tenant_id": fila["tenant_id"],
        "activo": fila["activo"],
        "slug": fila["slug"],
        "texto_bienvenida": fila["texto_bienvenida"],
    }
