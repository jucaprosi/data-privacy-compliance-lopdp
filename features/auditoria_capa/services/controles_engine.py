# ¤controles-periodicos ¤auditoria-capa ¤hallazgos ¤rbac-tenant
"""Motor de controles periódicos (CAPA-02).

Reglas (governance/especificaciones/CAPA-02.md §3):
- R1 verificar mueve la próxima fecha y cierra el hallazgo del vencimiento por la compuerta de `roadmap`.
- R2 el responsable tiene rol vigente en la organización y no es el `dpo`.
- R3/R4 vencer produce un hallazgo por vencimiento; esta sala nunca crea tareas.
- R5 `evidencia_sha256` es una referencia: no se lee ni guarda vigencia de evidencias.
- R6 cada cambio deja evento en `audit_events`.
Cada operación fija el contexto RLS y además filtra por `tenant_id`.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from app_core.audit import registrar_evento
from app_core.db.session import fijar_contexto_rls
from app_core.errors import CodigoErrorNegocio
from features.auditoria_capa.domain.control_periodico import (
    ControlPeriodico,
    CrearControlEntrada,
    EstadoControl,
    ResultadoVencimiento,
    RetirarControlEntrada,
    VerificacionControl,
    VerificarControlEntrada,
    ahora_guayaquil,
    clave_vencimiento,
    hoy_guayaquil,
    siguiente_verificacion,
)
from features.evidencias import evidencias_service
from features.organizacion import organizacion_service
from features.roadmap import roadmap_service

CONTROL_NO_ENCONTRADO = CodigoErrorNegocio(
    codigo="CONTROL_NO_ENCONTRADO",
    status_code=404,
    mensaje_defecto="El control no existe en la organización.",
)
CONTROL_RETIRADO = CodigoErrorNegocio(
    codigo="CONTROL_RETIRADO",
    status_code=409,
    mensaje_defecto="El control está retirado.",
)
CONTROL_AJENO = CodigoErrorNegocio(
    codigo="CONTROL_AJENO",
    status_code=403,
    mensaje_defecto="Solo el responsable del control o el implementador pueden verificarlo.",
)
RESPONSABLE_SIN_ROL = CodigoErrorNegocio(
    codigo="RESPONSABLE_SIN_ROL",
    status_code=422,
    mensaje_defecto="El responsable no tiene un rol vigente en la organización.",
)
EVIDENCIA_NO_ENCONTRADA = CodigoErrorNegocio(
    codigo="EVIDENCIA_NO_ENCONTRADA",
    status_code=422,
    mensaje_defecto="La evidencia indicada no existe en la organización.",
)

ROL_DPO = "dpo"
ROL_IMPLEMENTADOR = "implementador"
ROL_RESPONSABLE_AREA = "responsable_area"

_CONTROL = (
    "SELECT c.id, c.nombre, c.control_ref, c.frecuencia, c.responsable_user_id, c.proxima_verificacion, "
    "c.estado, c.hallazgo_vigente_id, "
    "(SELECT max(v.verificado_en) FROM verificaciones_control v "
    " WHERE v.tenant_id = c.tenant_id AND v.control_id = c.id) AS ultima_verificacion_en "
    "FROM controles_periodicos c WHERE c.tenant_id = :t"
)

_LISTADO = _CONTROL + (
    " AND (CAST(:estado AS TEXT) IS NULL OR c.estado = :estado)"
    " AND (CAST(:u AS TEXT) IS NULL OR c.responsable_user_id = :u)"
    " ORDER BY c.proxima_verificacion, c.id"
)
_POR_ID = _CONTROL + " AND c.id = :id"


def _fila_a_control(fila) -> ControlPeriodico:
    return ControlPeriodico(**dict(fila))


async def _obtener(session: AsyncSession, tenant_id: str, control_id: str) -> ControlPeriodico:
    fila = (
        await session.execute(text(_POR_ID), {"t": tenant_id, "id": control_id})
    ).mappings().first()
    if fila is None:
        raise ErrorNegocio(CONTROL_NO_ENCONTRADO)
    return _fila_a_control(fila)


async def _bloquear(session: AsyncSession, tenant_id: str, control_id: str) -> ControlPeriodico:
    """Serializa las escrituras sobre un control: verificar y vencer a la vez no se pisan."""
    await session.execute(
        text("SELECT 1 FROM controles_periodicos WHERE tenant_id = :t AND id = :id FOR UPDATE"),
        {"t": tenant_id, "id": control_id},
    )
    return await _obtener(session, tenant_id, control_id)


async def _exigir_responsable(session: AsyncSession, tenant_id: str, user_id: str, responsable_id: str) -> None:
    roles = await organizacion_service.list_my_roles(session, tenant_id, responsable_id)
    await fijar_contexto_rls(session, tenant_id, user_id)  # list_my_roles fijó al responsable como usuario
    if not roles:
        raise ErrorNegocio(RESPONSABLE_SIN_ROL)
    if any(r["role"] == ROL_DPO for r in roles):
        raise ErrorNegocio(RESPONSABLE_SIN_ROL, detail="El DPO no puede ser responsable de un control (D-2).")


def _exigir_evidencia(tenant_id: str, evidencia_sha256: Optional[str]) -> Optional[str]:
    if evidencia_sha256 is None:
        return None
    try:
        huella = evidencias_service.normalizar_sha256(evidencia_sha256)
    except evidencias_service.HashInvalido:
        raise ErrorNegocio(EVIDENCIA_NO_ENCONTRADA) from None
    if evidencias_service.verificar_hash(tenant_id, huella) is None:
        raise ErrorNegocio(EVIDENCIA_NO_ENCONTRADA)
    return huella


async def listar_controles(
    session: AsyncSession, tenant_id: str, user_id: str, rol: str, estado: Optional[str] = None
) -> list[ControlPeriodico]:
    await fijar_contexto_rls(session, tenant_id, user_id)
    params = {"t": tenant_id, "estado": estado, "u": user_id if rol == ROL_RESPONSABLE_AREA else None}
    filas = (await session.execute(text(_LISTADO), params)).mappings().all()
    return [_fila_a_control(f) for f in filas]


async def crear_control(
    session: AsyncSession, tenant_id: str, user_id: str, entrada: CrearControlEntrada
) -> ControlPeriodico:
    await fijar_contexto_rls(session, tenant_id, user_id)
    await _exigir_responsable(session, tenant_id, user_id, entrada.responsable_user_id)
    control_id = str(uuid.uuid4())
    await session.execute(
        text(
            "INSERT INTO controles_periodicos (id, tenant_id, nombre, control_ref, frecuencia, "
            "responsable_user_id, proxima_verificacion, creado_por) "
            "VALUES (:id, :t, :nombre, :control, :frecuencia, :responsable, :proxima, :u)"
        ),
        {
            "id": control_id,
            "t": tenant_id,
            "nombre": entrada.nombre,
            "control": entrada.control_ref,
            "frecuencia": entrada.frecuencia,
            "responsable": entrada.responsable_user_id,
            "proxima": entrada.proxima_verificacion,
            "u": user_id,
        },
    )
    await registrar_evento(
        session, tenant_id, "control_periodico", control_id, "creado", user_id,
        {"frecuencia": entrada.frecuencia, "responsable_user_id": entrada.responsable_user_id},
    )
    return await _obtener(session, tenant_id, control_id)


async def registrar_verificacion(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    rol: str,
    control_id: str,
    entrada: VerificarControlEntrada,
) -> tuple[ControlPeriodico, VerificacionControl]:
    await fijar_contexto_rls(session, tenant_id, user_id)
    control = await _bloquear(session, tenant_id, control_id)
    if rol != ROL_IMPLEMENTADOR and user_id != control.responsable_user_id:
        raise ErrorNegocio(CONTROL_AJENO)
    if control.estado == EstadoControl.retirado.value:
        raise ErrorNegocio(CONTROL_RETIRADO)
    huella = _exigir_evidencia(tenant_id, entrada.evidencia_sha256)

    verificado_en = ahora_guayaquil()
    verificacion = VerificacionControl(
        id=str(uuid.uuid4()),
        control_id=control_id,
        verificado_por=user_id,
        verificado_en=verificado_en,
        evidencia_sha256=huella,
        nota=entrada.nota,
    )
    await session.execute(
        text(
            "INSERT INTO verificaciones_control (id, tenant_id, control_id, verificado_por, verificado_en, "
            "evidencia_sha256, nota) VALUES (:id, :t, :control, :u, :en, :huella, :nota)"
        ),
        {
            "id": verificacion.id,
            "t": tenant_id,
            "control": control_id,
            "u": user_id,
            "en": verificado_en,
            "huella": huella,
            "nota": entrada.nota,
        },
    )
    await session.execute(
        text(
            "UPDATE controles_periodicos SET proxima_verificacion = :proxima, estado = 'vigente', "
            "hallazgo_vigente_id = NULL, actualizado_en = now() WHERE tenant_id = :t AND id = :id"
        ),
        {"proxima": siguiente_verificacion(verificado_en.date(), control.frecuencia), "t": tenant_id, "id": control_id},
    )
    if control.hallazgo_vigente_id:
        await roadmap_service.cerrar_hallazgo(session, tenant_id, user_id, control.hallazgo_vigente_id)
    await registrar_evento(
        session, tenant_id, "control_periodico", control_id, "verificado", user_id,
        {"verificacion_id": verificacion.id, "evidencia_sha256": huella},
    )
    return await _obtener(session, tenant_id, control_id), verificacion


async def retirar_control(
    session: AsyncSession, tenant_id: str, user_id: str, control_id: str, entrada: RetirarControlEntrada
) -> ControlPeriodico:
    await fijar_contexto_rls(session, tenant_id, user_id)
    control = await _bloquear(session, tenant_id, control_id)
    if control.estado == EstadoControl.retirado.value:
        raise ErrorNegocio(CONTROL_RETIRADO)
    await session.execute(
        text(
            "UPDATE controles_periodicos SET estado = 'retirado', actualizado_en = now() "
            "WHERE tenant_id = :t AND id = :id"
        ),
        {"t": tenant_id, "id": control_id},
    )
    await registrar_evento(
        session, tenant_id, "control_periodico", control_id, "retirado", user_id, {"motivo": entrada.motivo}
    )
    return await _obtener(session, tenant_id, control_id)


async def vencer_controles(session: AsyncSession, tenant_id: str, user_id: str) -> ResultadoVencimiento:
    """Marca los controles vencidos (R3) y registra un hallazgo por vencimiento (R4)."""
    await fijar_contexto_rls(session, tenant_id, user_id)
    filas = (
        await session.execute(
            text(
                "SELECT id, nombre, control_ref, proxima_verificacion FROM controles_periodicos "
                "WHERE tenant_id = :t AND estado = 'vigente' AND proxima_verificacion < :hoy "
                "ORDER BY proxima_verificacion, id FOR UPDATE"
            ),
            {"t": tenant_id, "hoy": hoy_guayaquil()},
        )
    ).mappings().all()
    creados = 0
    for fila in filas:
        hallazgo_id, creado = await roadmap_service.registrar_hallazgo(
            session,
            tenant_id,
            user_id,
            origen=roadmap_service.OrigenHallazgo.control_periodico.value,
            origen_ref=clave_vencimiento(fila["id"], fila["proxima_verificacion"]),
            severidad=roadmap_service.SeveridadHallazgo.alta.value,
            titulo=f"Control vencido: {fila['nombre']}"[:roadmap_service.TITULO_MAX],
            control_ref=fila["control_ref"],
        )
        creados += int(creado)
        await session.execute(
            text(
                "UPDATE controles_periodicos SET estado = 'vencido', hallazgo_vigente_id = :h, "
                "actualizado_en = now() WHERE tenant_id = :t AND id = :id"
            ),
            {"h": hallazgo_id, "t": tenant_id, "id": fila["id"]},
        )
        await registrar_evento(
            session, tenant_id, "control_periodico", fila["id"], "vencido", user_id, {"hallazgo_id": hallazgo_id}
        )
    return ResultadoVencimiento(vencidos=len(filas), hallazgos_creados=creados)
