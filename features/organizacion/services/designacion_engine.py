# ¤rbac-tenant
"""Motor de designaciones formales (sala ADPA: Organización).

Gestiona las designaciones formales del Delegado de Protección de Datos (DPD)
y del Coordinador (mandato de la alta dirección), asegurando:
1. Validación contra la estructura orgánica (cargos incompatibles con DPD).
2. Registro de aceptación y declaración previa de conflictos (solo por la persona designada).
3. Registro de constancia de inscripción ante la Superintendencia (SPDP).
4. Revocación formal motivada.
5. Emisión de informe de estado de designaciones (de solo lectura).
6. Trazabilidad inmutable en audit_events.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from features.organizacion.domain.models import RbacError
from features.organizacion.services.contexto_tenant import fijar_tenant
from features.organizacion.services.estructura_engine import TIPOS_INCOMPATIBLES_CON_DPD


class TipoDesignacion(str, Enum):
    dpd = "dpd"
    coordinador = "coordinador"


class VinculoDesignacion(str, Enum):
    relacion_dependencia = "relacion_dependencia"
    prestacion_servicios = "prestacion_servicios"


class DesignacionCreate(BaseModel):
    tipo: TipoDesignacion
    user_id: str = Field(min_length=1)
    representante_nombre: str = Field(min_length=1, max_length=255)
    representante_identificacion: str = Field(min_length=1, max_length=50)
    representante_cargo: str = Field(min_length=1, max_length=255)
    fecha_designacion: date
    doc_referencia: str = Field(min_length=1, max_length=255)
    valid_to: Optional[datetime] = None
    vinculo: Optional[VinculoDesignacion] = None


class InscripcionSpdpCreate(BaseModel):
    inscripcion_spdp_fecha: date
    inscripcion_spdp_ref: str = Field(min_length=1, max_length=255)


class DeclaracionConflictosCreate(BaseModel):
    declaracion_texto: str = Field(min_length=1)
    declaracion_tiene_conflicto: bool = False
    declaracion_es_socio_accionista: bool = False
    declaracion_es_pariente_admin: bool = False


class RevocacionCreate(BaseModel):
    motivo: str = Field(min_length=1, max_length=255)


async def _cargos_incompatibles_usuario(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
) -> list[dict[str, Any]]:
    """Consulta directa y robusta de cargos incompatibles con DPD en la estructura orgánica."""
    await fijar_tenant(session, tenant_id)
    rows = (await session.execute(
        text(
            "SELECT c.id, c.nombre, c.tipo_cargo, c.area_id, a.nombre AS area_nombre "
            "FROM cargos_organicos c "
            "JOIN areas a ON c.area_id = a.id "
            "WHERE c.tenant_id = :t AND c.titular_user_id = :u "
            "AND (c.valid_to IS NULL OR c.valid_to > now()) "
            "AND c.tipo_cargo = ANY(:tipos)"
        ),
        {
            "t": tenant_id,
            "u": user_id,
            "tipos": [t.value for t in TIPOS_INCOMPATIBLES_CON_DPD],
        },
    )).mappings().all()
    return [dict(r) for r in rows]


async def _obtener_designacion_activa(
    session: AsyncSession,
    tenant_id: str,
    tipo: TipoDesignacion,
) -> Optional[dict[str, Any]]:
    row = (await session.execute(
        text(
            "SELECT * FROM designaciones_formales "
            "WHERE tenant_id=:t AND tipo=:tipo AND revocada_at IS NULL "
            "AND (valid_to IS NULL OR valid_to > now())"
        ),
        {"t": tenant_id, "tipo": tipo.value},
    )).mappings().first()
    return dict(row) if row else None


async def crear_designacion_formal(
    session: AsyncSession,
    tenant_id: str,
    admin_user_id: str,
    payload: DesignacionCreate,
) -> dict[str, Any]:
    """Crea una designación formal para DPD o Coordinador.

    Base legal:
    - Art. 3 del Reglamento del Delegado (designa el representante legal o apoderado).
    - Art. 49 del Reglamento General (vínculo laboral o de prestación de servicios).
    - Art. 15.5, 16 del Reglamento del Delegado y Art. 56 del Reglamento General (incompatibilidades con cargos).
    """
    await fijar_tenant(session, tenant_id)

    # Verificar que el usuario exista
    user = (await session.execute(
        text("SELECT id, nombre, email FROM users WHERE id=:u AND deleted_at IS NULL"),
        {"u": payload.user_id},
    )).mappings().first()
    if not user:
        raise RbacError(404, "El usuario a designar no existe.")

    # Si es DPD, validar vínculo obligatorio y cargos incompatibles
    if payload.tipo == TipoDesignacion.dpd:
        if not payload.vinculo:
            raise RbacError(400, "El vínculo (relacion_dependencia o prestacion_servicios) es obligatorio para el DPD.")

        # Consultar estructura orgánica
        cargos_incompatibles = await _cargos_incompatibles_usuario(session, tenant_id, payload.user_id)
        if cargos_incompatibles:
            nombres_cargos = ", ".join(f"'{c['nombre']}' ({c['tipo_cargo']})" for c in cargos_incompatibles)
            raise RbacError(
                409,
                f"La persona ocupa cargos incompatibles con las funciones del DPD: {nombres_cargos}. "
                "Base legal: Arts. 15.5 y 16 del Reglamento del Delegado y Art. 56 del Reglamento General.",
            )

    # Verificar si ya existe una designación activa para este tipo
    activa = await _obtener_designacion_activa(session, tenant_id, payload.tipo)
    if activa:
        raise RbacError(409, f"Ya existe una designación formal activa para el tipo '{payload.tipo.value}'.")

    designacion_id = str(uuid4())
    ahora = datetime.now(timezone.utc)

    row = (await session.execute(
        text(
            "INSERT INTO designaciones_formales ("
            "    id, tenant_id, tipo, user_id, representante_nombre, representante_identificacion, "
            "    representante_cargo, fecha_designacion, doc_referencia, valid_from, valid_to, "
            "    vinculo, created_at, updated_at"
            ") VALUES ("
            "    :id, :t, :tipo, :u, :rep_nom, :rep_id, :rep_car, :fec_des, :doc_ref, :vf, :vt, "
            "    :vinc, :ahora, :ahora"
            ") RETURNING *"
        ),
        {
            "id": designacion_id,
            "t": tenant_id,
            "tipo": payload.tipo.value,
            "u": payload.user_id,
            "rep_nom": payload.representante_nombre,
            "rep_id": payload.representante_identificacion,
            "rep_car": payload.representante_cargo,
            "fec_des": payload.fecha_designacion,
            "doc_ref": payload.doc_referencia,
            "vf": ahora,
            "vt": payload.valid_to,
            "vinc": payload.vinculo.value if payload.vinculo else None,
            "ahora": ahora,
        },
    )).mappings().first()

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="designacion_formal",
        entity_id=designacion_id,
        action="designacion_creada",
        user_id=admin_user_id,
        payload={
            "tipo": payload.tipo.value,
            "designado_user_id": payload.user_id,
            "representante_nombre": payload.representante_nombre,
            "doc_referencia": payload.doc_referencia,
        },
    )

    return dict(row)


async def listar_designaciones_formales(
    session: AsyncSession,
    tenant_id: str,
    tipo: Optional[TipoDesignacion] = None,
) -> list[dict[str, Any]]:
    """Lista las designaciones formales del tenant."""
    await fijar_tenant(session, tenant_id)

    query = (
        "SELECT d.*, u.nombre AS usuario_nombre, u.email AS usuario_email "
        "FROM designaciones_formales d "
        "JOIN users u ON d.user_id = u.id "
        "WHERE d.tenant_id = :t "
    )
    params: dict[str, Any] = {"t": tenant_id}

    if tipo:
        query += "AND d.tipo = :tipo "
        params["tipo"] = tipo.value

    query += "ORDER BY d.created_at DESC"

    rows = (await session.execute(text(query), params)).mappings().all()
    return [dict(r) for r in rows]


async def obtener_designacion_formal(
    session: AsyncSession,
    tenant_id: str,
    designacion_id: str,
) -> dict[str, Any]:
    """Obtiene el detalle de una designación formal."""
    await fijar_tenant(session, tenant_id)

    row = (await session.execute(
        text(
            "SELECT d.*, u.nombre AS usuario_nombre, u.email AS usuario_email "
            "FROM designaciones_formales d "
            "JOIN users u ON d.user_id = u.id "
            "WHERE d.id = :id AND d.tenant_id = :t"
        ),
        {"id": designacion_id, "t": tenant_id},
    )).mappings().first()

    if not row:
        raise RbacError(404, "Designación formal no encontrada.")
    return dict(row)


async def registrar_declaracion_conflictos(
    session: AsyncSession,
    tenant_id: str,
    designacion_id: str,
    user_id_declarador: str,
    payload: DeclaracionConflictosCreate,
) -> dict[str, Any]:
    """Registra la declaración de conflictos de intereses y aceptación del DPD.

    Base legal: Art. 17 del Reglamento del Delegado y Art. 4.7 y 56 del Reglamento General.
    Solo la propia persona designada puede emitir su declaración.
    Si se declara conflicto, parentesco o ser socio/accionista, se rechaza la aceptación con 409.
    """
    designacion = await obtener_designacion_formal(session, tenant_id, designacion_id)

    if designacion["tipo"] != TipoDesignacion.dpd.value:
        raise RbacError(400, "La declaración de conflictos solo aplica a designaciones de tipo 'dpd'.")

    if designacion["user_id"] != user_id_declarador:
        raise RbacError(403, "Solo la propia persona designada puede emitir la declaración de conflictos.")

    if designacion["revocada_at"] is not None:
        raise RbacError(409, "La designación formal ha sido revocada.")

    # Validar si declara conflicto sustancial
    if payload.declaracion_tiene_conflicto or payload.declaracion_es_socio_accionista or payload.declaracion_es_pariente_admin:
        motivos = []
        if payload.declaracion_tiene_conflicto:
            motivos.append("declara tener conflicto de intereses real, potencial o aparente")
        if payload.declaracion_es_socio_accionista:
            motivos.append("es socio o accionista de la entidad")
        if payload.declaracion_es_pariente_admin:
            motivos.append("es pariente de administradores o directores")
        raise RbacError(
            409,
            f"No puede asumir la función de DPD porque {', '.join(motivos)}. "
            "Base legal: Art. 17 Reglamento del Delegado y Art. 56 Reglamento General.",
        )

    ahora = datetime.now(timezone.utc)
    row = (await session.execute(
        text(
            "UPDATE designaciones_formales SET "
            "declaracion_at = :ahora, "
            "declaracion_texto = :texto, "
            "declaracion_tiene_conflicto = :conflicto, "
            "declaracion_es_socio_accionista = :socio, "
            "declaracion_es_pariente_admin = :pariente, "
            "aceptacion_at = COALESCE(aceptacion_at, :ahora), "
            "updated_at = :ahora "
            "WHERE id = :id AND tenant_id = :t RETURNING *"
        ),
        {
            "id": designacion_id,
            "t": tenant_id,
            "ahora": ahora,
            "texto": payload.declaracion_texto,
            "conflicto": payload.declaracion_tiene_conflicto,
            "socio": payload.declaracion_es_socio_accionista,
            "pariente": payload.declaracion_es_pariente_admin,
        },
    )).mappings().first()

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="designacion_formal",
        entity_id=designacion_id,
        action="declaracion_conflictos_registrada",
        user_id=user_id_declarador,
        payload={"declaracion_at": ahora.isoformat()},
    )

    return dict(row)


async def registrar_inscripcion_spdp(
    session: AsyncSession,
    tenant_id: str,
    designacion_id: str,
    admin_user_id: str,
    payload: InscripcionSpdpCreate,
) -> dict[str, Any]:
    """Registra la constancia de inscripción de la designación ante la Superintendencia (SPDP).

    Base legal: Art. 5 y 6 del Reglamento del Delegado de Protección de Datos.
    """
    designacion = await obtener_designacion_formal(session, tenant_id, designacion_id)

    if designacion["tipo"] != TipoDesignacion.dpd.value:
        raise RbacError(400, "La inscripción ante la SPDP solo aplica a designaciones de tipo 'dpd'.")

    if designacion["revocada_at"] is not None:
        raise RbacError(409, "La designación formal ha sido revocada.")

    ahora = datetime.now(timezone.utc)
    row = (await session.execute(
        text(
            "UPDATE designaciones_formales SET "
            "inscripcion_spdp_fecha = :fecha, "
            "inscripcion_spdp_ref = :ref, "
            "updated_at = :ahora "
            "WHERE id = :id AND tenant_id = :t RETURNING *"
        ),
        {
            "id": designacion_id,
            "t": tenant_id,
            "fecha": payload.inscripcion_spdp_fecha,
            "ref": payload.inscripcion_spdp_ref,
            "ahora": ahora,
        },
    )).mappings().first()

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="designacion_formal",
        entity_id=designacion_id,
        action="inscripcion_spdp_registrada",
        user_id=admin_user_id,
        payload={
            "inscripcion_spdp_fecha": payload.inscripcion_spdp_fecha.isoformat(),
            "inscripcion_spdp_ref": payload.inscripcion_spdp_ref,
        },
    )

    return dict(row)


async def revocar_designacion_formal(
    session: AsyncSession,
    tenant_id: str,
    designacion_id: str,
    admin_user_id: str,
    payload: RevocacionCreate,
) -> dict[str, Any]:
    """Revoca formalmente una designación activa."""
    designacion = await obtener_designacion_formal(session, tenant_id, designacion_id)

    if designacion["revocada_at"] is not None:
        raise RbacError(409, "La designación ya se encuentra revocada.")

    ahora = datetime.now(timezone.utc)
    row = (await session.execute(
        text(
            "UPDATE designaciones_formales SET "
            "revocada_at = :ahora, "
            "revocada_motivo = :motivo, "
            "revocada_por_user_id = :admin, "
            "updated_at = :ahora "
            "WHERE id = :id AND tenant_id = :t RETURNING *"
        ),
        {
            "id": designacion_id,
            "t": tenant_id,
            "ahora": ahora,
            "motivo": payload.motivo,
            "admin": admin_user_id,
        },
    )).mappings().first()

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="designacion_formal",
        entity_id=designacion_id,
        action="designacion_revocada",
        user_id=admin_user_id,
        payload={"motivo": payload.motivo},
    )

    return dict(row)


async def obtener_informe_estado_designaciones(
    session: AsyncSession,
    tenant_id: str,
) -> dict[str, Any]:
    """Emite un informe de solo lectura con el estado formal del DPD y del Coordinador.

    No bloquea nada: señala lo pendiente y los posibles conflictos sobrevenidos.
    """
    await fijar_tenant(session, tenant_id)

    # 1. Designación activa DPD
    dpd_activa = await _obtener_designacion_activa(session, tenant_id, TipoDesignacion.dpd)
    estado_dpd: dict[str, Any] = {
        "designado": False,
        "designacion": None,
        "declaracion_completada": False,
        "inscrito_spdp": False,
        "conflicto_sobrevenido": False,
        "cargos_incompatibles": [],
        "alertas": [],
    }

    if dpd_activa:
        estado_dpd["designado"] = True
        estado_dpd["designacion"] = dpd_activa
        estado_dpd["declaracion_completada"] = dpd_activa.get("declaracion_at") is not None
        estado_dpd["inscrito_spdp"] = dpd_activa.get("inscripcion_spdp_fecha") is not None

        # Verificar si sobrevino algún cargo incompatible en la estructura orgánica
        cargos_inc = await _cargos_incompatibles_usuario(session, tenant_id, dpd_activa["user_id"])
        if cargos_inc:
            estado_dpd["conflicto_sobrevenido"] = True
            estado_dpd["cargos_incompatibles"] = cargos_inc
            estado_dpd["alertas"].append(
                "Conflicto sobrevenido: la persona designada como DPD ocupa actualmente cargos incompatibles. "
                "La organización debe abstenerse, reestructurar funciones o revocar (Art. 17 Reglamento del Delegado)."
            )

        if not estado_dpd["declaracion_completada"]:
            estado_dpd["alertas"].append("Falta registrar la declaración formal de no tener conflicto de intereses.")
        if not estado_dpd["inscrito_spdp"]:
            estado_dpd["alertas"].append("Falta registrar la constancia de inscripción ante la SPDP.")
    else:
        estado_dpd["alertas"].append("No existe una designación formal activa para el Delegado de Protección de Datos.")

    # 2. Mandato activo Coordinador
    coord_activo = await _obtener_designacion_activa(session, tenant_id, TipoDesignacion.coordinador)
    estado_coord: dict[str, Any] = {
        "designado": False,
        "designacion": None,
        "tiene_mandato_escrito": False,
        "alertas": [],
    }

    if coord_activo:
        estado_coord["designado"] = True
        estado_coord["designacion"] = coord_activo
        estado_coord["tiene_mandato_escrito"] = True
    else:
        estado_coord["alertas"].append(
            "El Coordinador carece de mandato formal escrito de la alta dirección para supervisar las áreas."
        )

    return {
        "tenant_id": tenant_id,
        "dpd": estado_dpd,
        "coordinador": estado_coord,
    }
