# ¤evidencias ¤evidencias-vigencia
"""Vigencia y visibilidad de los documentos de evidencia, en la base (EVI-02)."""
from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.errors import ErrorNegocio
from features.evidencias.domain import errores as _e
from features.evidencias.domain.vigencia import (
    mensaje_documentos_vencidos,
    ROL_DPO,
    ROLES_VISIBILIDAD_POSIBLES,
    AtributosDocumento,
    normalizar_visibilidad,
    puede_ver,
)


async def _fijar_rls(session: AsyncSession, tenant_id: str, user_id: Optional[str] = None) -> None:
    from app_core.db.session import fijar_contexto_rls

    await fijar_contexto_rls(session, tenant_id, user_id)


def exigir_puede_definir_atributos(rol: str) -> None:
    if rol != ROL_DPO:
        raise ErrorNegocio(_e.SIN_PERMISO_PARA_ATRIBUTOS)


async def fijar_atributos(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    rol: str,
    documento_id: str,
    vence_en: Optional[date],
    visible_para: Optional[list[str]] = None,
) -> None:
    """Define la fecha de vencimiento y los roles que ven el documento. Solo el DPO; deja un evento de auditoría."""
    exigir_puede_definir_atributos(rol)
    try:
        roles = normalizar_visibilidad(list(visible_para) if visible_para is not None else list(ROLES_VISIBILIDAD_POSIBLES))
    except ValueError as exc:
        raise ErrorNegocio(_e.VISIBILIDAD_INVALIDA) from exc
    await _fijar_rls(session, tenant_id, user_id)
    existe = await session.execute(
        text("SELECT 1 FROM evidencias_documentos WHERE id = :d AND tenant_id = :t"),
        {"d": documento_id, "t": tenant_id},
    )
    if existe.first() is None:
        raise ErrorNegocio(_e.DOCUMENTO_NO_ENCONTRADO)
    await session.execute(
        text(
            "INSERT INTO evidencias_atributos (documento_id, tenant_id, vence_en, visible_para, actualizado_por) "
            "VALUES (:d, :t, :v, :roles, :u) "
            "ON CONFLICT (documento_id) DO UPDATE SET vence_en = EXCLUDED.vence_en, "
            "visible_para = EXCLUDED.visible_para, actualizado_por = EXCLUDED.actualizado_por, actualizado_en = now()"
        ),
        {"d": documento_id, "t": tenant_id, "v": vence_en, "roles": roles, "u": user_id},
    )
    await registrar_evento(
        session, tenant_id, "evidencia_atributos", documento_id, "definir", user_id,
        {"vence_en": vence_en.isoformat() if vence_en else None, "visible_para": roles},
    )


async def listar_atributos(
    session: AsyncSession, tenant_id: str, user_id: str, rol: str
) -> list[AtributosDocumento]:
    """Documentos de la organización con su vigencia y visibilidad, solo los que el rol puede ver."""
    await _fijar_rls(session, tenant_id, user_id)
    filas = (
        await session.execute(
            text(
                "SELECT d.id, d.codigo, d.nombre_archivo, d.tipo_mime, d.tamano_bytes, d.sha256, d.subido_en, "
                "d.clave_almacen, a.vence_en, a.visible_para FROM evidencias_documentos d "
                "LEFT JOIN evidencias_atributos a ON a.documento_id = d.id AND a.tenant_id = d.tenant_id "
                "WHERE d.tenant_id = :t ORDER BY d.subido_en, d.codigo"
            ),
            {"t": tenant_id},
        )
    ).mappings().all()
    vinculos = await session.execute(
        text("SELECT documento_id, control_id FROM evidencias_vinculos WHERE tenant_id = :t ORDER BY control_id"),
        {"t": tenant_id},
    )
    controles: dict[str, list[int]] = {}
    for documento_id, control_id in vinculos.all():
        controles.setdefault(documento_id, []).append(int(control_id))
    resultado = []
    for f in filas:
        visibles = list(f["visible_para"]) if f["visible_para"] is not None else list(ROLES_VISIBILIDAD_POSIBLES)
        if not puede_ver(rol, visibles):
            continue
        resultado.append(
            AtributosDocumento(
                documento_id=f["id"], codigo=f["codigo"], nombre_archivo=f["nombre_archivo"],
                tipo_mime=f["tipo_mime"], tamano_bytes=f["tamano_bytes"], sha256=f["sha256"],
                subido_en=f["subido_en"], vence_en=f["vence_en"], visible_para=visibles,
                controles=controles.get(f["id"], []), clave_almacen=f["clave_almacen"],
            )
        )
    return resultado


async def atributos_de(
    session: AsyncSession, tenant_id: str, user_id: str, documento_id: str
) -> AtributosDocumento:
    """El documento con sus atributos, sin filtrar por rol (quien llama decide); 404 si no es de la organización."""
    await _fijar_rls(session, tenant_id, user_id)
    fila = (
        await session.execute(
            text(
                "SELECT d.id, d.codigo, d.nombre_archivo, d.tipo_mime, d.tamano_bytes, d.sha256, d.subido_en, "
                "d.clave_almacen, a.vence_en, a.visible_para FROM evidencias_documentos d "
                "LEFT JOIN evidencias_atributos a ON a.documento_id = d.id AND a.tenant_id = d.tenant_id "
                "WHERE d.tenant_id = :t AND d.id = :d"
            ),
            {"t": tenant_id, "d": documento_id},
        )
    ).mappings().first()
    if fila is None:
        raise ErrorNegocio(_e.DOCUMENTO_NO_ENCONTRADO)
    return AtributosDocumento(
        documento_id=fila["id"], codigo=fila["codigo"], nombre_archivo=fila["nombre_archivo"],
        tipo_mime=fila["tipo_mime"], tamano_bytes=fila["tamano_bytes"], sha256=fila["sha256"],
        subido_en=fila["subido_en"], vence_en=fila["vence_en"],
        visible_para=list(fila["visible_para"]) if fila["visible_para"] is not None else list(ROLES_VISIBILIDAD_POSIBLES),
        clave_almacen=fila["clave_almacen"],
    )


async def controles_con_documento_vigente(session: AsyncSession, tenant_id: str, hoy: date) -> set[int]:
    """Controles con al menos un documento vinculado que sigue vigente: un vencido no respalda ningún requisito."""
    await _fijar_rls(session, tenant_id)
    filas = await session.execute(
        text(
            "SELECT DISTINCT v.control_id FROM evidencias_vinculos v "
            "JOIN evidencias_documentos d ON d.id = v.documento_id AND d.tenant_id = v.tenant_id "
            "LEFT JOIN evidencias_atributos a ON a.documento_id = d.id AND a.tenant_id = d.tenant_id "
            "WHERE v.tenant_id = :t AND (a.vence_en IS NULL OR a.vence_en >= :hoy)"
        ),
        {"t": tenant_id, "hoy": hoy},
    )
    return {int(c) for (c,) in filas.all()}


async def documentos_vencidos_de_controles(
    session: AsyncSession, tenant_id: str, hoy: date, controles: list[int]
) -> list[dict]:
    """Documentos vencidos vinculados a esos controles, con los controles que respaldaban."""
    await _fijar_rls(session, tenant_id)
    filas = (
        await session.execute(
            text(
                "SELECT d.id, d.codigo, d.nombre_archivo, a.vence_en, v.control_id FROM evidencias_vinculos v "
                "JOIN evidencias_documentos d ON d.id = v.documento_id AND d.tenant_id = v.tenant_id "
                "JOIN evidencias_atributos a ON a.documento_id = d.id AND a.tenant_id = d.tenant_id "
                "WHERE v.tenant_id = :t AND a.vence_en < :hoy AND v.control_id = ANY(:controles) "
                "ORDER BY d.codigo, v.control_id"
            ),
            {"t": tenant_id, "hoy": hoy, "controles": controles},
        )
    ).mappings().all()
    por_documento: dict[str, dict] = {}
    for f in filas:
        d = por_documento.setdefault(
            f["id"],
            {"codigo": f["codigo"], "nombre_archivo": f["nombre_archivo"], "vence_en": f["vence_en"], "controles": []},
        )
        d["controles"].append(int(f["control_id"]))
    return list(por_documento.values())


async def controles_para_sellar(session: AsyncSession, tenant_id: str, hoy: date) -> set[int]:
    """Controles que un sello futuro cuenta como respaldados: los que tienen un documento vigente.

    Si un control tiene documentos vinculados pero todos vencidos, su respaldo se perdió y el sello se rechaza
    nombrando los documentos vencidos (la evidencia que pierde vigencia reabre su control). Los sellos ya emitidos
    no cambian: sus huellas son inmutables.
    """
    registrados = await _controles_con_documento_registrado(session, tenant_id)
    vigentes = await controles_con_documento_vigente(session, tenant_id, hoy)
    sin_respaldo = sorted(registrados - vigentes)
    if sin_respaldo:
        vencidos = await documentos_vencidos_de_controles(session, tenant_id, hoy, sin_respaldo)
        raise ErrorNegocio(_e.SELLO_CON_DOCUMENTOS_VENCIDOS, detail=mensaje_documentos_vencidos(vencidos))
    return vigentes


async def _controles_con_documento_registrado(session: AsyncSession, tenant_id: str) -> set[int]:
    await _fijar_rls(session, tenant_id)
    filas = await session.execute(
        text("SELECT DISTINCT control_id FROM evidencias_vinculos WHERE tenant_id = :t"), {"t": tenant_id}
    )
    return {int(c) for (c,) in filas.all()}
