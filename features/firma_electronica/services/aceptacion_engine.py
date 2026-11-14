# ¤firma-electronica
"""Motor de aceptación simple con acuse (FIRMA-02).

Reglas de negocio:
- R1: Token aleatorio de 32 bytes; se guarda su sha256; un solo uso; caduca en dias_vigencia días.
- R2: acuse = sha256(documento_sha256 ‖ persona_id ‖ aceptado_en.isoformat() ‖ str(ip));
       se registra en evidencias_service con tipo acuse y visibilidad organizacion (EVI-02).
- R3: verificar ⟺ sha256(archivo) ∈ {documentos aprobados} ∪ {acuses} del tenant.
- R4: la ruta pública no expone otras aceptaciones ni el contenido del documento.

Cruza a otras salas únicamente por su compuerta (_service.py).
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import fijar_contexto_rls
from app_core.errors import ErrorNegocio
from features.firma_electronica.domain.aceptacion import (
    Aceptacion,
    DocumentoParaAceptacion,
    EnlaceGenerado,
    InfoPublicaAceptacion,
    ACEPTACION_CADUCADA,
    ACEPTACION_NO_ENCONTRADA,
    DOCUMENTO_NO_APROBADO,
    PERSONA_NO_ENCONTRADA,
)


# --------------------------------------------------------------------------- #
# Helpers internos                                                              #
# --------------------------------------------------------------------------- #

def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _generar_token() -> tuple[str, str]:
    """Devuelve (token_raw_hex, token_hash_hex). El hash va a la BD; el raw al cliente."""
    raw = secrets.token_bytes(32)
    return raw.hex(), _sha256_hex(raw)



async def _fila_a_aceptacion(fila) -> Aceptacion:
    return Aceptacion(
        id=fila.id,
        tenant_id=fila.tenant_id,
        documento_id=fila.documento_id,
        documento_sha256=fila.documento_sha256,
        persona_id=fila.persona_id,
        token_hash=fila.token_hash,
        caduca_en=fila.caduca_en,
        nombre=fila.nombre,
        email=fila.email,
        creado_por=fila.creado_por,
        creado_en=fila.creado_en,
        aceptado_en=fila.aceptado_en,
        ip=str(fila.ip) if fila.ip else None,
        acuse_sha256=fila.acuse_sha256,
    )


# --------------------------------------------------------------------------- #
# API pública del engine                                                        #
# --------------------------------------------------------------------------- #

async def crear_enlaces(
    db: AsyncSession,
    tenant_id: str,
    user_id: str,
    documento_id: str,
    persona_ids: list[str],
    dias_vigencia: int,
    base_url: str = "",
    *,
    obtener_doc=None,
    obtener_persona=None,
) -> list[EnlaceGenerado]:
    """Crea un enlace de aceptación por persona y devuelve los tokens raw para las URLs.

    obtener_doc: callable(db, tenant_id, documento_id) → DocumentoParaAceptacion (Biblioteca, BIB-107).
    obtener_persona: callable(db, tenant_id, persona_id) → PersonaParaAceptacion | None (inventario, ORG-17).
    Ambos los provee la compuerta firma_electronica_service desde los pasillos.
    """
    if obtener_doc is None or obtener_persona is None:
        raise NotImplementedError("Faltan los lectores de documento (BIB-107) y de persona (ORG-17).")
    doc = await obtener_doc(db, tenant_id, documento_id)
    if doc.estado != "aprobado":
        raise ErrorNegocio(DOCUMENTO_NO_APROBADO)

    ahora = datetime.now(timezone.utc)
    caduca_en = ahora + timedelta(days=dias_vigencia)
    resultado: list[EnlaceGenerado] = []

    for pid in persona_ids:
        persona = await obtener_persona(db, tenant_id, pid)
        if persona is None:
            raise ErrorNegocio(PERSONA_NO_ENCONTRADA)
        nombre, email = persona.nombre, persona.email
        token_raw, token_hash = _generar_token()
        await db.execute(
            text(
                "INSERT INTO aceptaciones "
                "(tenant_id, documento_id, documento_sha256, persona_id, token_hash, "
                " caduca_en, nombre, email, creado_por) "
                "VALUES (CAST(:tid AS uuid), CAST(:did AS uuid), :dsha, CAST(:pid AS uuid), "
                "        :thash, :cad, :nom, :mail, CAST(:uid AS uuid))"
            ),
            {
                "tid": tenant_id,
                "did": documento_id,
                "dsha": doc.sha256,
                "pid": pid,
                "thash": token_hash,
                "cad": caduca_en,
                "nom": nombre,
                "mail": email,
                "uid": user_id,
            },
        )
        url = f"{base_url}/aceptar/{token_raw}"
        resultado.append(EnlaceGenerado(persona_id=pid, url=url))

    await db.commit()
    return resultado


async def listar_aceptaciones(
    db: AsyncSession, tenant_id: str, documento_id: Optional[str] = None
) -> list[dict]:
    """Lista aceptaciones del tenant (con RLS) sin exponer el token."""
    q = (
        "SELECT id, tenant_id, documento_id, documento_sha256, persona_id, "
        "       caduca_en, aceptado_en, nombre, email, ip, acuse_sha256, creado_en "
        "FROM aceptaciones"
    )
    params: dict = {}
    if documento_id:
        q += " WHERE documento_id = CAST(:did AS uuid)"
        params["did"] = documento_id
    q += " ORDER BY creado_en DESC"
    filas = (await db.execute(text(q), params)).fetchall()
    return [
        {
            "id": str(f.id),
            "documento_id": str(f.documento_id),
            "documento_sha256": f.documento_sha256,
            "persona_id": str(f.persona_id),
            "nombre": f.nombre,
            "email": f.email,
            "caduca_en": f.caduca_en.isoformat(),
            "aceptado_en": f.aceptado_en.isoformat() if f.aceptado_en else None,
            "ip": str(f.ip) if f.ip else None,
            "acuse_sha256": f.acuse_sha256,
            "creado_en": f.creado_en.isoformat(),
        }
        for f in filas
    ]


async def obtener_info_publica(
    db: AsyncSession, token_raw: str, *, obtener_doc=None
) -> InfoPublicaAceptacion:
    """Devuelve datos públicos del enlace sin exponer otras aceptaciones del tenant (R4).

    Usa la función SECURITY DEFINER para operar sin contexto de tenant.
    """
    token_hash = _sha256_hex(bytes.fromhex(token_raw))
    fila = (
        await db.execute(
            text("SELECT * FROM obtener_aceptacion_por_token(:h)"),
            {"h": token_hash},
        )
    ).fetchone()
    if fila is None:
        raise ErrorNegocio(ACEPTACION_NO_ENCONTRADA)

    ahora = datetime.now(timezone.utc)
    if fila.aceptado_en is not None or fila.caduca_en <= ahora:
        raise ErrorNegocio(ACEPTACION_CADUCADA)

    # Nombre de la organización (tenant).
    org_fila = (
        await db.execute(
            text("SELECT nombre_comercial FROM tenants WHERE id = :t"),
            {"t": str(fila.tenant_id)},
        )
    ).fetchone()
    organizacion = org_fila.nombre_comercial if org_fila else str(fila.tenant_id)

    # Nombre del documento: solo el nombre, nunca el contenido (R4). Si el lector falla, no se rompe la página.
    nombre_documento = str(fila.documento_id)
    if obtener_doc is not None:
        await fijar_contexto_rls(db, str(fila.tenant_id), str(fila.creado_por))
        try:
            nombre_documento = (await obtener_doc(db, str(fila.tenant_id), str(fila.documento_id))).nombre
        except ErrorNegocio:
            pass

    return InfoPublicaAceptacion(
        nombre_documento=nombre_documento,
        organizacion=organizacion,
        sha256=fila.documento_sha256,
    )


async def registrar_aceptacion(
    db: AsyncSession, token_raw: str, ip: Optional[str], *, custodiar=None
) -> str:
    """Procesa la aceptación del enlace y devuelve el acuse_sha256.

    Registra aceptado_en, ip y acuse_sha256 en la fila, y crea una evidencia tipo acuse (EVI-02).
    La IP se registra deliberadamente; comentarla provoca que test_aceptacion_registra_acuse falle
    (prueba de mutación documentada en el commit).
    """
    token_hash = _sha256_hex(bytes.fromhex(token_raw))
    fila = (
        await db.execute(
            text("SELECT * FROM obtener_aceptacion_por_token(:h)"),
            {"h": token_hash},
        )
    ).fetchone()
    if fila is None:
        raise ErrorNegocio(ACEPTACION_NO_ENCONTRADA)

    ahora = datetime.now(timezone.utc)
    if fila.aceptado_en is not None or fila.caduca_en <= ahora:
        raise ErrorNegocio(ACEPTACION_CADUCADA)

    # R2: acuse = sha256(documento_sha256 ‖ persona_id ‖ aceptado_en.isoformat() ‖ str(ip))
    aceptado_en = ahora
    ip_str = ip or ""
    acuse_data = (
        fila.documento_sha256
        + str(fila.persona_id)
        + aceptado_en.isoformat()
        + ip_str  # MUTACIÓN: comentar esta línea hace fallar test_aceptacion_registra_acuse
    ).encode("utf-8")
    acuse_sha256 = _sha256_hex(acuse_data)

    # La ruta pública llega sin organización: se fija la de la fila para que RLS deje actualizarla.
    # El UPDATE solo vale si el enlace sigue sin usar: dos aceptaciones simultáneas no pasan las dos.
    await fijar_contexto_rls(db, str(fila.tenant_id), str(fila.creado_por))
    actualizada = await db.execute(
        text(
            "UPDATE aceptaciones SET aceptado_en = :ack, ip = CAST(:ip AS inet), acuse_sha256 = :acu "
            "WHERE token_hash = :h AND aceptado_en IS NULL"
        ),
        {"ack": aceptado_en, "ip": ip_str or None, "acu": acuse_sha256, "h": token_hash},
    )
    if actualizada.rowcount != 1:
        raise ErrorNegocio(ACEPTACION_CADUCADA)

    # R2: el acuse se custodia como evidencia en la misma transacción. Si la custodia falla no queda
    # aceptación sin acuse: la excepción sube y no se confirma nada.
    if custodiar is not None:
        await custodiar(
            db,
            tenant_id=str(fila.tenant_id),
            user_id=str(fila.creado_por),
            aceptacion_id=str(fila.id),
            acuse_sha256=acuse_sha256,
            documento_sha256=fila.documento_sha256,
            persona_id=str(fila.persona_id),
            nombre=fila.nombre,
            email=fila.email,
            aceptado_en=aceptado_en,
            ip=ip_str,
        )

    await db.commit()
    return acuse_sha256


async def verificar_hash(
    db: AsyncSession, tenant_id: str, contenido: bytes, *, es_aprobado=None
) -> tuple[bool, Optional[str]]:
    """R3: comprueba si sha256(contenido) coincide con un documento aprobado o un acuse del tenant."""
    digest = _sha256_hex(contenido)

    # Busca en aceptaciones (acuse_sha256 y documento_sha256) y, por `es_aprobado`, en los documentos aprobados.
    fila = (
        await db.execute(
            text(
                "SELECT "
                "  EXISTS(SELECT 1 FROM aceptaciones "
                "         WHERE tenant_id = CAST(:t AS uuid) AND documento_sha256 = :d) AS es_doc,"
                "  EXISTS(SELECT 1 FROM aceptaciones "
                "         WHERE tenant_id = CAST(:t AS uuid) AND acuse_sha256 = :d) AS es_acuse"
            ),
            {"t": tenant_id, "d": digest},
        )
    ).fetchone()

    if fila and fila.es_doc:
        return True, "documento"
    if es_aprobado is not None and await es_aprobado(db, tenant_id, digest):
        return True, "documento"
    if fila and fila.es_acuse:
        return True, "acuse"
    return False, None
