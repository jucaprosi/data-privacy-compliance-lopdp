"""Flujo de alta de responsables de área (sala ADPA: Organización). PRD §5.3.1.

Regla base: *el coordinador solicita, el implementador ejecuta.* Ningún rol completa el flujo solo ni
puede saltarse pasos, y cada transición queda registrada en `audit_events`.

Estados: `pendiente` → `aprobada` | `rechazada` | `cancelada`; `aprobada` → `ejecutada`. Aprobar y
ejecutar son pasos separados, para permitir aprobación diferida o por lotes.

Tres capas: el trigger `trg_arr_transiciones` de la base (migración 20261018_responsable_requests)
impone las transiciones válidas y que cada paso deje a su actor; este motor aplica las reglas de
negocio; el router traduce los errores a HTTP.

Cada transición es un UPDATE condicionado por el estado de origen (`WHERE estado = ...`): dos
aprobaciones simultáneas no se pisan, la segunda no encuentra la fila y recibe 409. Las sentencias son
estáticas, con valores enlazados.

Ejecutar es atómico: el área (si hay que crearla), la asignación del rol, el cambio de estado y los
eventos de auditoría van en la misma transacción de la sesión; si algo falla, no queda nada.
"""
from __future__ import annotations

from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from app_core.audit import registrar_evento
from app_core.errors import DPO_INDEPENDENCE_VIOLATED
from features.organizacion.domain.models import AreaCreate, RbacError, RoleGrant
from features.organizacion.domain.roles import Role
from features.organizacion.services.areas_engine import create_area
from features.organizacion.services.contexto_tenant import fijar_tenant
from features.organizacion.services.regla_tamano_engine import verificar_excepcion_coordinador_responsable
from features.organizacion.services.roles_engine import grant_role

# Cada transición es una sentencia estática (sin SQL interpolado): UPDATE condicionado por el estado de
# origen, con los valores enlazados.
SQL_CANCELAR = text(
    "UPDATE area_responsable_requests SET estado = 'cancelada', decided_by = :u, decided_at = now(), "
    "updated_at = now() WHERE id = :id AND tenant_id = :t AND estado = :desde RETURNING *"
)
SQL_APROBAR = text(
    "UPDATE area_responsable_requests SET estado = 'aprobada', decided_by = :u, decided_at = now(), "
    "decision_notes = :n, updated_at = now() WHERE id = :id AND tenant_id = :t AND estado = :desde RETURNING *"
)
SQL_RECHAZAR = text(
    "UPDATE area_responsable_requests SET estado = 'rechazada', decided_by = :u, decided_at = now(), "
    "decision_notes = :n, updated_at = now() WHERE id = :id AND tenant_id = :t AND estado = :desde RETURNING *"
)
SQL_EJECUTAR = text(
    "UPDATE area_responsable_requests SET estado = 'ejecutada', executed_by = :u, executed_at = now(), "
    "assignment_id = :a, area_id = COALESCE(area_id, :area), updated_at = now() "
    "WHERE id = :id AND tenant_id = :t AND estado = :desde RETURNING *"
)

ENTIDAD = "area_responsable_request"
MARCA_TRANSICION = "RESPONSABLE_REQUEST_TRANSITION"
ESTADOS = ("pendiente", "aprobada", "rechazada", "cancelada", "ejecutada")


class ResponsableRequestCreate(BaseModel):
    """Solicitud de alta de un responsable de área. El área existe (`area_id`) o se crea al ejecutar."""

    target_user_id: str = Field(min_length=1)
    area_id: Optional[str] = None
    area_nombre: Optional[str] = Field(default=None, min_length=1, max_length=255)
    motivo: Optional[str] = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def un_area_o_un_nombre(self) -> "ResponsableRequestCreate":
        if bool(self.area_id) == bool(self.area_nombre):
            raise ValueError("Indique el área existente (area_id) o el nombre de una nueva (area_nombre), no ambos ni ninguno")
        return self


class ResponsableRequestDecision(BaseModel):
    notas: Optional[str] = Field(default=None, max_length=1000)


class ResponsableRequestPatch(BaseModel):
    """PATCH sobre una solicitud: el único cambio posible es cancelarla."""

    estado: Literal["cancelada"]


def _conflicto_de_transicion(exc: IntegrityError) -> Optional[RbacError]:
    mensaje = str(getattr(exc, "orig", exc))
    if MARCA_TRANSICION in mensaje:
        detalle = mensaje.split(MARCA_TRANSICION + ":", 1)[1].strip().splitlines()[0]
        return RbacError(409, detalle)
    return None


async def _fila(session: AsyncSession, tenant_id: str, request_id: str) -> Optional[dict]:
    row = (await session.execute(
        text("SELECT * FROM area_responsable_requests WHERE id = :id AND tenant_id = :t"),
        {"id": request_id, "t": tenant_id},
    )).mappings().first()
    return dict(row) if row else None


async def _existente_o_404(session: AsyncSession, tenant_id: str, request_id: str) -> dict:
    fila = await _fila(session, tenant_id, request_id)
    if fila is None:
        raise RbacError(404, "Solicitud no encontrada")
    return fila


def _no_esta_en(fila: dict, esperado: str) -> RbacError:
    return RbacError(409, f"La solicitud está {fila['estado']}; solo se puede hacer desde el estado {esperado}")


async def _transicionar(
    session: AsyncSession, tenant_id: str, request_id: str, desde: str, sentencia: TextClause, parametros: dict
) -> Optional[dict]:
    """Ejecuta la transición. Devuelve la fila, o None si la solicitud ya no estaba en `desde`."""
    try:
        row = (await session.execute(
            sentencia, {"id": request_id, "t": tenant_id, "desde": desde, **parametros}
        )).mappings().first()
    except IntegrityError as exc:
        traducido = _conflicto_de_transicion(exc)
        if traducido is not None:
            raise traducido from exc
        raise
    return dict(row) if row else None


async def _validar_destino(
    session: AsyncSession, tenant_id: str, fila: dict, actor_id: str, area_id: Optional[str]
) -> None:
    """Reglas del usuario destino (PRD §5.3.1). Se aplican al aprobar y de nuevo al ejecutar."""
    destino = fila["target_user_id"]
    if destino == actor_id:
        raise RbacError(409, "No puede asignarse a sí mismo como responsable de área")

    activos = (await session.execute(
        text(
            "SELECT role, area_id FROM user_tenant_roles WHERE user_id = :u AND tenant_id = :t "
            "AND (valid_to IS NULL OR valid_to > now())"
        ),
        {"u": destino, "t": tenant_id},
    )).mappings().all()
    roles = {r["role"] for r in activos}

    if Role.dpo.value in roles:
        raise ErrorNegocio(
            DPO_INDEPENDENCE_VIOLATED,
            "El DPO no puede ser responsable de área: debe conservar su independencia (INV_LOPDP_DPO_INDEPENDENCE)",
        )
    if area_id and any(r["role"] == Role.responsable_area.value and r["area_id"] == area_id for r in activos):
        raise RbacError(409, "El usuario ya es responsable de esa área")
    # Coordinador: solo en organizaciones micro o pequeña; sin tamaño configurado se rechaza (falla cerrado).
    await verificar_excepcion_coordinador_responsable(session, tenant_id, destino, Role.responsable_area.value)


async def create_responsable_request(
    session: AsyncSession, tenant_id: str, requested_by: str, payload: ResponsableRequestCreate
) -> dict:
    await fijar_tenant(session, tenant_id, requested_by)
    destino = (await session.execute(
        text("SELECT id FROM users WHERE id = :id AND deleted_at IS NULL"), {"id": payload.target_user_id}
    )).first()
    if destino is None:
        raise RbacError(404, "Usuario destino no encontrado")
    if payload.area_id:
        area = (await session.execute(
            text("SELECT id FROM areas WHERE id = :id AND tenant_id = :t AND deleted_at IS NULL"),
            {"id": payload.area_id, "t": tenant_id},
        )).first()
        if area is None:
            raise RbacError(404, "Área no encontrada en el tenant")

    request_id = str(uuid4())
    try:
        row = (await session.execute(
            text(
                "INSERT INTO area_responsable_requests "
                "(id, tenant_id, target_user_id, area_id, area_nombre, motivo, requested_by) "
                "VALUES (:id, :t, :u, :a, :n, :m, :rb) RETURNING *"
            ),
            {
                "id": request_id, "t": tenant_id, "u": payload.target_user_id, "a": payload.area_id,
                "n": payload.area_nombre, "m": payload.motivo, "rb": requested_by,
            },
        )).mappings().first()
    except IntegrityError as exc:
        if "uq_arr_abierta_por_usuario_area" in str(getattr(exc, "orig", exc)):
            raise RbacError(409, "Ya hay una solicitud abierta para ese usuario y esa área") from exc
        raise
    await registrar_evento(
        session, tenant_id, ENTIDAD, request_id, "responsable_request_created", requested_by,
        {"target_user_id": payload.target_user_id, "area_id": payload.area_id, "area_nombre": payload.area_nombre},
    )
    return dict(row)


async def list_responsable_requests(session: AsyncSession, tenant_id: str, estado: Optional[str] = None) -> list[dict]:
    await fijar_tenant(session, tenant_id)
    if estado is not None and estado not in ESTADOS:
        raise RbacError(422, f"Estado inválido '{estado}'. Opciones: {', '.join(ESTADOS)}")
    if estado is None:
        consulta = text("SELECT * FROM area_responsable_requests WHERE tenant_id = :t ORDER BY created_at DESC")
        parametros = {"t": tenant_id}
    else:
        consulta = text(
            "SELECT * FROM area_responsable_requests WHERE tenant_id = :t AND estado = :e ORDER BY created_at DESC"
        )
        parametros = {"t": tenant_id, "e": estado}
    return [dict(r) for r in (await session.execute(consulta, parametros)).mappings().all()]


async def get_responsable_request(session: AsyncSession, tenant_id: str, request_id: str) -> dict:
    await fijar_tenant(session, tenant_id)
    return await _existente_o_404(session, tenant_id, request_id)


async def cancel_responsable_request(session: AsyncSession, tenant_id: str, user_id: str, request_id: str) -> dict:
    """Cancela el coordinador que la solicitó, y solo mientras está pendiente."""
    await fijar_tenant(session, tenant_id, user_id)
    fila = await _existente_o_404(session, tenant_id, request_id)
    if fila["requested_by"] != user_id:
        raise RbacError(403, "Solo quien solicitó el alta puede cancelarla")
    nueva = await _transicionar(session, tenant_id, request_id, "pendiente", SQL_CANCELAR, {"u": user_id})
    if nueva is None:
        raise _no_esta_en(await _existente_o_404(session, tenant_id, request_id), "pendiente")
    await registrar_evento(session, tenant_id, ENTIDAD, request_id, "responsable_request_cancelled", user_id, {})
    return nueva


async def approve_responsable_request(
    session: AsyncSession, tenant_id: str, user_id: str, request_id: str, decision: ResponsableRequestDecision
) -> dict:
    await fijar_tenant(session, tenant_id, user_id)
    fila = await _existente_o_404(session, tenant_id, request_id)
    if fila["estado"] != "pendiente":
        raise _no_esta_en(fila, "pendiente")
    await _validar_destino(session, tenant_id, fila, user_id, fila["area_id"])
    nueva = await _transicionar(
        session, tenant_id, request_id, "pendiente", SQL_APROBAR, {"u": user_id, "n": decision.notas}
    )
    if nueva is None:
        raise _no_esta_en(await _existente_o_404(session, tenant_id, request_id), "pendiente")
    await registrar_evento(session, tenant_id, ENTIDAD, request_id, "responsable_request_approved", user_id,
                           {"notas": decision.notas})
    return nueva


async def reject_responsable_request(
    session: AsyncSession, tenant_id: str, user_id: str, request_id: str, decision: ResponsableRequestDecision
) -> dict:
    await fijar_tenant(session, tenant_id, user_id)
    fila = await _existente_o_404(session, tenant_id, request_id)
    if fila["estado"] != "pendiente":
        raise _no_esta_en(fila, "pendiente")
    nueva = await _transicionar(
        session, tenant_id, request_id, "pendiente", SQL_RECHAZAR, {"u": user_id, "n": decision.notas}
    )
    if nueva is None:
        raise _no_esta_en(await _existente_o_404(session, tenant_id, request_id), "pendiente")
    await registrar_evento(session, tenant_id, ENTIDAD, request_id, "responsable_request_rejected", user_id,
                           {"notas": decision.notas})
    return nueva


async def _area_para_ejecutar(session: AsyncSession, tenant_id: str, fila: dict) -> str:
    """Área de la solicitud; si se pidió una nueva por nombre, se reutiliza la que ya exista o se crea."""
    if fila["area_id"]:
        return fila["area_id"]
    existente = (await session.execute(
        text("SELECT id FROM areas WHERE tenant_id = :t AND deleted_at IS NULL AND lower(nombre) = lower(:n)"),
        {"t": tenant_id, "n": fila["area_nombre"]},
    )).first()
    if existente is not None:
        return existente[0]
    return (await create_area(session, tenant_id, AreaCreate(nombre=fila["area_nombre"])))["id"]


async def execute_responsable_request(session: AsyncSession, tenant_id: str, user_id: str, request_id: str) -> dict:
    """Asigna el rol `responsable_area`. Atómico: todo o nada, en la transacción de la sesión."""
    await fijar_tenant(session, tenant_id, user_id)
    fila = await _existente_o_404(session, tenant_id, request_id)
    if fila["estado"] != "aprobada":
        raise _no_esta_en(fila, "aprobada")
    # El destino pudo cambiar desde la aprobación (p. ej. pasó a ser DPO): se valida otra vez, antes de
    # crear nada.
    await _validar_destino(session, tenant_id, fila, user_id, fila["area_id"])

    area_id = await _area_para_ejecutar(session, tenant_id, fila)
    if fila["area_id"] is None:
        # Una vez resuelta el área, se vuelve a comprobar que no sea ya responsable de ella.
        await _validar_destino(session, tenant_id, fila, user_id, area_id)

    asignacion = await grant_role(
        session, tenant_id, user_id,
        RoleGrant(user_id=fila["target_user_id"], role=Role.responsable_area, area_id=area_id),
    )
    await session.execute(
        text("UPDATE user_tenant_roles SET request_id = :r WHERE id = :id AND tenant_id = :t"),
        {"r": request_id, "id": asignacion["id"], "t": tenant_id},
    )
    nueva = await _transicionar(
        session, tenant_id, request_id, "aprobada", SQL_EJECUTAR,
        {"u": user_id, "a": asignacion["id"], "area": area_id},
    )
    if nueva is None:
        raise _no_esta_en(await _existente_o_404(session, tenant_id, request_id), "aprobada")
    await registrar_evento(
        session, tenant_id, ENTIDAD, request_id, "responsable_request_executed", user_id,
        {"assignment_id": asignacion["id"], "area_id": area_id, "target_user_id": fila["target_user_id"]},
    )
    return nueva
