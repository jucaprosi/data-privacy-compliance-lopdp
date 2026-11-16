# ¤¤backend-developer
# ¤api-integraciones ¤seguridad ¤seguridad-tenant
"""Autenticación y ciclo de vida de claves de integración (API-02).

Invariante: INV_API_INTEGRATION_SCOPED_KEYS_VERSIONED.
- La clave en claro solo se entrega en crear y rotar.
- En la base se guarda únicamente hash_sha256.
- Aislamiento estricto por tenant_id y alcances (rat:lectura, tareas:lectura, evidencias:lectura).
- Registro de cada uso en audit_events.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.integraciones.techos import verificar_techo_claves

ALCANCES_VALIDOS = {"rat:lectura", "tareas:lectura", "evidencias:lectura"}


def generar_credenciales_clave() -> tuple[str, str, str]:
    """Genera (clave_en_claro, prefijo, hash_sha256). Clave con prefijo evk_."""
    aleatorio = secrets.token_urlsafe(32)
    clave_en_claro = f"evk_{aleatorio}"
    prefijo = f"{clave_en_claro[:12]}..."
    hash_sha256 = hashlib.sha256(clave_en_claro.encode("utf-8")).hexdigest()
    return clave_en_claro, prefijo, hash_sha256


async def autenticar_clave(
    session: AsyncSession,
    cabecera_auth: str | None,
    alcance_requerido: str | None = None,
) -> dict[str, Any]:
    """Valida la cabecera 'Authorization: Bearer evk_…' y comprueba el alcance."""
    if not cabecera_auth or not cabecera_auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cabecera Authorization ausente o formato inválido (se espera Bearer evk_...)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = cabecera_auth.removeprefix("Bearer ").strip()
    if not token.startswith("evk_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no es una clave de integración válida",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    stmt = text(
        """
        SELECT id, tenant_id, nombre, prefijo, alcances, creada_en, rotada_en, revocada_en
        FROM claves_integracion
        WHERE hash_sha256 = :token_hash
        """
    )
    res = await session.execute(stmt, {"token_hash": token_hash})
    row = res.mappings().first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clave de integración inválida",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if row["revocada_en"] is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clave de integración revocada",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if row["rotada_en"] is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clave de integración rotada",
            headers={"WWW-Authenticate": "Bearer"},
        )

    alcances = set(row["alcances"] or [])
    if alcance_requerido and alcance_requerido not in alcances:
        await registrar_evento(
            session=session,
            tenant_id=row["tenant_id"],
            entidad="clave_integracion",
            entidad_id=str(row["id"]),
            accion="alcance_denegado",
            usuario_id=f"key:{row['id']}",
            datos={"alcance_solicitado": alcance_requerido, "alcances": sorted(alcances)},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Alcance insuficiente para la operación: requiere '{alcance_requerido}'",
        )

    await registrar_evento(
        session=session,
        tenant_id=row["tenant_id"],
        entidad="clave_integracion",
        entidad_id=str(row["id"]),
        accion="uso_clave_integracion",
        usuario_id=f"key:{row['id']}",
        datos={"alcance": alcance_requerido},
    )

    return {
        "id": str(row["id"]),
        "tenant_id": row["tenant_id"],
        "nombre": row["nombre"],
        "prefijo": row["prefijo"],
        "alcances": list(alcances),
    }


async def crear_clave(
    session: AsyncSession,
    tenant_id: str,
    nombre: str,
    alcances: list[str],
    usuario_id: str,
) -> tuple[dict[str, Any], str]:
    """Crea una nueva clave de integración para el tenant si no supera el techo del paquete."""
    await verificar_techo_claves(session, tenant_id)

    clave_en_claro, prefijo, hash_sha256 = generar_credenciales_clave()
    alcances_filtrados = [a for a in alcances if a in ALCANCES_VALIDOS] or list(ALCANCES_VALIDOS)

    stmt = text(
        """
        INSERT INTO claves_integracion (tenant_id, nombre, prefijo, hash_sha256, alcances)
        VALUES (:tenant_id, :nombre, :prefijo, :hash_sha256, :alcances)
        RETURNING id, tenant_id, nombre, prefijo, alcances, creada_en, rotada_en, revocada_en
        """
    )
    res = await session.execute(
        stmt,
        {
            "tenant_id": tenant_id,
            "nombre": nombre.strip(),
            "prefijo": prefijo,
            "hash_sha256": hash_sha256,
            "alcances": alcances_filtrados,
        },
    )
    row = res.mappings().one()

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entidad="clave_integracion",
        entidad_id=str(row["id"]),
        accion="crear",
        usuario_id=usuario_id,
        datos={"nombre": nombre, "prefijo": prefijo, "alcances": alcances_filtrados},
    )

    clave_dict = {
        "id": str(row["id"]),
        "nombre": row["nombre"],
        "prefijo": row["prefijo"],
        "alcances": row["alcances"],
        "creada_en": row["creada_en"].isoformat() if row["creada_en"] else None,
        "rotada_en": row["rotada_en"].isoformat() if row["rotada_en"] else None,
        "revocada_en": row["revocada_en"].isoformat() if row["revocada_en"] else None,
    }
    return clave_dict, clave_en_claro


async def listar_claves(session: AsyncSession, tenant_id: str) -> list[dict[str, Any]]:
    """Lista las claves de integración del tenant. Nunca incluye hash ni clave en claro."""
    stmt = text(
        """
        SELECT id, nombre, prefijo, alcances, creada_en, rotada_en, revocada_en
        FROM claves_integracion
        WHERE tenant_id = :tenant_id
        ORDER BY creada_en DESC
        """
    )
    res = await session.execute(stmt, {"tenant_id": tenant_id})
    filas = res.mappings().all()

    return [
        {
            "id": str(r["id"]),
            "nombre": r["nombre"],
            "prefijo": r["prefijo"],
            "alcances": r["alcances"] or [],
            "creada_en": r["creada_en"].isoformat() if r["creada_en"] else None,
            "rotada_en": r["rotada_en"].isoformat() if r["rotada_en"] else None,
            "revocada_en": r["revocada_en"].isoformat() if r["revocada_en"] else None,
        }
        for r in filas
    ]


async def rotar_clave(
    session: AsyncSession,
    tenant_id: str,
    clave_id: str,
    usuario_id: str,
) -> tuple[dict[str, Any], str]:
    """Invalida la clave previa marcando rotada_en y genera una nueva clave en claro."""
    stmt_antigua = text(
        """
        SELECT id, nombre, alcances, rotada_en, revocada_en
        FROM claves_integracion
        WHERE id = :id AND tenant_id = :tenant_id
        """
    )
    res_antigua = await session.execute(stmt_antigua, {"id": clave_id, "tenant_id": tenant_id})
    antigua = res_antigua.mappings().first()

    if not antigua:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clave de integración no encontrada")

    if antigua["revocada_en"] is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede rotar una clave ya revocada")

    if antigua["rotada_en"] is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La clave ya ha sido rotada previamente")

    # Marcar antigua como rotada
    await session.execute(
        text("UPDATE claves_integracion SET rotada_en = NOW() WHERE id = :id"),
        {"id": clave_id},
    )

    # Crear nueva clave con el mismo nombre y alcances
    clave_en_claro, prefijo, hash_sha256 = generar_credenciales_clave()
    stmt_nueva = text(
        """
        INSERT INTO claves_integracion (tenant_id, nombre, prefijo, hash_sha256, alcances)
        VALUES (:tenant_id, :nombre, :prefijo, :hash_sha256, :alcances)
        RETURNING id, tenant_id, nombre, prefijo, alcances, creada_en, rotada_en, revocada_en
        """
    )
    res_nueva = await session.execute(
        stmt_nueva,
        {
            "tenant_id": tenant_id,
            "nombre": antigua["nombre"],
            "prefijo": prefijo,
            "hash_sha256": hash_sha256,
            "alcances": antigua["alcances"],
        },
    )
    row = res_nueva.mappings().one()

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entidad="clave_integracion",
        entidad_id=str(row["id"]),
        accion="rotar",
        usuario_id=usuario_id,
        datos={"clave_anterior_id": clave_id, "nueva_clave_id": str(row["id"])},
    )

    nueva_dict = {
        "id": str(row["id"]),
        "nombre": row["nombre"],
        "prefijo": row["prefijo"],
        "alcances": row["alcances"],
        "creada_en": row["creada_en"].isoformat() if row["creada_en"] else None,
        "rotada_en": row["rotada_en"].isoformat() if row["rotada_en"] else None,
        "revocada_en": row["revocada_en"].isoformat() if row["revocada_en"] else None,
    }
    return nueva_dict, clave_en_claro


async def revocar_clave(
    session: AsyncSession,
    tenant_id: str,
    clave_id: str,
    usuario_id: str,
) -> dict[str, Any]:
    """Revoca una clave de integración marcando revocada_en."""
    stmt_check = text(
        """
        SELECT id, nombre, rotada_en, revocada_en
        FROM claves_integracion
        WHERE id = :id AND tenant_id = :tenant_id
        """
    )
    res = await session.execute(stmt_check, {"id": clave_id, "tenant_id": tenant_id})
    row = res.mappings().first()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clave de integración no encontrada")

    if row["revocada_en"] is not None:
        return {
            "id": str(row["id"]),
            "nombre": row["nombre"],
            "revocada_en": row["revocada_en"].isoformat(),
        }

    stmt_update = text(
        """
        UPDATE claves_integracion
        SET revocada_en = NOW()
        WHERE id = :id AND tenant_id = :tenant_id
        RETURNING id, nombre, prefijo, alcances, creada_en, rotada_en, revocada_en
        """
    )
    res_up = await session.execute(stmt_update, {"id": clave_id, "tenant_id": tenant_id})
    revocada = res_up.mappings().one()

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entidad="clave_integracion",
        entidad_id=str(revocada["id"]),
        accion="revocar",
        usuario_id=usuario_id,
    )

    return {
        "id": str(revocada["id"]),
        "nombre": revocada["nombre"],
        "prefijo": revocada["prefijo"],
        "alcances": revocada["alcances"] or [],
        "creada_en": revocada["creada_en"].isoformat() if revocada["creada_en"] else None,
        "rotada_en": revocada["rotada_en"].isoformat() if revocada["rotada_en"] else None,
        "revocada_en": revocada["revocada_en"].isoformat() if revocada["revocada_en"] else None,
    }
