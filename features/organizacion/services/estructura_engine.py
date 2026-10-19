# ¤rbac-tenant
"""Motor de estructura orgánica (sala ADPA: Organización).

Gestiona unidades (niveles jerárquicos), cargos orgánicos, titulares,
validación de ciclos, reporte jerárquico, reglas de incompatibilidad del
delegado de protección de datos (Art. 18 Reglamento del Delegado) y
el informe de cobertura de responsables por designar.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from features.organizacion.domain.models import RbacError
from features.organizacion.domain.roles import Role
from features.organizacion.services.contexto_tenant import fijar_tenant


# ==============================================================================
# Catálogos Cerrados y Modelos Pydantic
# ==============================================================================

class NivelArea(str, Enum):
    alta_direccion = "alta_direccion"
    direccion = "direccion"
    jefatura = "jefatura"
    unidad = "unidad"


class TipoCargo(str, Enum):
    oficial_cumplimiento = "oficial_cumplimiento"
    oficial_seguridad_informacion = "oficial_seguridad_informacion"
    apoderado_especial_extranjero = "apoderado_especial_extranjero"
    miembro_administracion_o_control = "miembro_administracion_o_control"
    implementador_proteccion_datos = "implementador_proteccion_datos"
    nivel_superior_sector_publico = "nivel_superior_sector_publico"
    delegado_proteccion_datos = "delegado_proteccion_datos"
    otro = "otro"


# Los seis primeros tipos impiden ser delegado (Arts. 16.1-16.3, Art. 56.1, Art. 15.1/15.5)
TIPOS_INCOMPATIBLES_CON_DPD: frozenset[TipoCargo] = frozenset({
    TipoCargo.oficial_cumplimiento,
    TipoCargo.oficial_seguridad_informacion,
    TipoCargo.apoderado_especial_extranjero,
    TipoCargo.miembro_administracion_o_control,
    TipoCargo.implementador_proteccion_datos,
    TipoCargo.nivel_superior_sector_publico,
})


class AreaEstructuraCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    codigo: Optional[str] = Field(default=None, max_length=50)
    nivel: NivelArea = Field(default=NivelArea.unidad)
    parent_area_id: Optional[str] = None


class AreaEstructuraUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=255)
    codigo: Optional[str] = Field(default=None, max_length=50)
    nivel: Optional[NivelArea] = None
    parent_area_id: Optional[str] = None
    responsable_user_id: Optional[str] = None


class CargoCreate(BaseModel):
    area_id: str = Field(min_length=1)
    nombre: str = Field(min_length=1, max_length=255)
    tipo_cargo: TipoCargo = Field(default=TipoCargo.otro)
    es_jefatura: bool = False
    reporta_a_cargo_id: Optional[str] = None
    titular_user_id: Optional[str] = None
    valid_to: Optional[datetime] = None


class CargoUpdate(BaseModel):
    area_id: Optional[str] = None
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=255)
    tipo_cargo: Optional[TipoCargo] = None
    es_jefatura: Optional[bool] = None
    reporta_a_cargo_id: Optional[str] = None
    titular_user_id: Optional[str] = None
    valid_to: Optional[datetime] = None


class CargoTitularSet(BaseModel):
    titular_user_id: Optional[str] = None


# ==============================================================================
# Verificaciones y Auxiliares de Grafo / Jerarquía
# ==============================================================================

async def _obtener_area(session: AsyncSession, tenant_id: str, area_id: str) -> Optional[dict[str, Any]]:
    row = (await session.execute(
        text("SELECT * FROM areas WHERE id=:id AND tenant_id=:t AND deleted_at IS NULL"),
        {"id": area_id, "t": tenant_id},
    )).mappings().first()
    return dict(row) if row else None


async def _obtener_cargo(session: AsyncSession, tenant_id: str, cargo_id: str) -> Optional[dict[str, Any]]:
    row = (await session.execute(
        text("SELECT * FROM cargos_organicos WHERE id=:id AND tenant_id=:t"),
        {"id": cargo_id, "t": tenant_id},
    )).mappings().first()
    return dict(row) if row else None


async def _verificar_ciclo_areas(session: AsyncSession, tenant_id: str, area_id: str, nuevo_padre_id: str) -> None:
    if area_id == nuevo_padre_id:
        raise RbacError(400, "Un área no puede ser padre de sí misma (ciclo detectado).")
    
    actual = nuevo_padre_id
    visitados = {area_id}
    while actual:
        if actual in visitados:
            raise RbacError(400, "La jerarquía de áreas contiene un ciclo.")
        visitados.add(actual)
        padre_row = (await session.execute(
            text("SELECT parent_area_id FROM areas WHERE id=:id AND tenant_id=:t AND deleted_at IS NULL"),
            {"id": actual, "t": tenant_id},
        )).first()
        actual = padre_row[0] if padre_row else None


async def _verificar_ciclo_cargos(session: AsyncSession, tenant_id: str, cargo_id: str, nuevo_reporta_id: str) -> None:
    if cargo_id == nuevo_reporta_id:
        raise RbacError(400, "Un cargo no puede reportar a sí mismo (ciclo detectado).")

    actual = nuevo_reporta_id
    visitados = {cargo_id}
    while actual:
        if actual in visitados:
            raise RbacError(400, "La línea de reporte de cargos contiene un ciclo.")
        visitados.add(actual)
        reporta_row = (await session.execute(
            text("SELECT reporta_a_cargo_id FROM cargos_organicos WHERE id=:id AND tenant_id=:t"),
            {"id": actual, "t": tenant_id},
        )).first()
        actual = reporta_row[0] if reporta_row else None


# ==============================================================================
# Operaciones de Unidades (Áreas) con Nivel
# ==============================================================================

async def crear_area_estructura(
    session: AsyncSession,
    tenant_id: str,
    payload: AreaEstructuraCreate,
    user_id: Optional[str] = None,
) -> dict[str, Any]:
    await fijar_tenant(session, tenant_id)

    # Validar alta_direccion única
    if payload.nivel == NivelArea.alta_direccion:
        if payload.parent_area_id is not None:
            raise RbacError(400, "La unidad 'alta_direccion' es la raíz del árbol y no debe tener área padre.")
        existente = (await session.execute(
            text("SELECT id FROM areas WHERE tenant_id=:t AND nivel='alta_direccion' AND deleted_at IS NULL"),
            {"t": tenant_id},
        )).first()
        if existente:
            raise RbacError(409, "Ya existe una unidad de nivel 'alta_direccion' en la organización.")
    elif payload.parent_area_id:
        padre = await _obtener_area(session, tenant_id, payload.parent_area_id)
        if not padre:
            raise RbacError(404, "Área padre no encontrada en la organización.")

    area_id = str(uuid4())
    row = (await session.execute(
        text(
            "INSERT INTO areas (id, tenant_id, nombre, codigo, nivel, parent_area_id) "
            "VALUES (:id, :t, :n, :c, :lvl, :p) RETURNING *"
        ),
        {
            "id": area_id,
            "t": tenant_id,
            "n": payload.nombre,
            "c": payload.codigo,
            "lvl": payload.nivel.value,
            "p": payload.parent_area_id,
        },
    )).mappings().first()

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="area",
        entity_id=area_id,
        action="area_created",
        user_id=user_id,
        payload={"nombre": payload.nombre, "nivel": payload.nivel.value, "parent_area_id": payload.parent_area_id},
    )

    return dict(row)


async def editar_area_estructura(
    session: AsyncSession,
    tenant_id: str,
    area_id: str,
    payload: AreaEstructuraUpdate,
    user_id: Optional[str] = None,
) -> dict[str, Any]:
    await fijar_tenant(session, tenant_id)
    actual = await _obtener_area(session, tenant_id, area_id)
    if not actual:
        raise RbacError(404, "Área no encontrada.")

    changes = payload.model_dump(exclude_unset=True)
    if "parent_area_id" in changes and changes["parent_area_id"]:
        padre = await _obtener_area(session, tenant_id, changes["parent_area_id"])
        if not padre:
            raise RbacError(404, "Área padre no encontrada.")
        await _verificar_ciclo_areas(session, tenant_id, area_id, changes["parent_area_id"])

    if changes.get("nivel") == NivelArea.alta_direccion.value:
        existente = (await session.execute(
            text("SELECT id FROM areas WHERE tenant_id=:t AND nivel='alta_direccion' AND id<>:id AND deleted_at IS NULL"),
            {"t": tenant_id, "id": area_id},
        )).first()
        if existente:
            raise RbacError(409, "Ya existe otra unidad de nivel 'alta_direccion' en la organización.")

    if not changes:
        return actual

    row = (await session.execute(
        text(
            "UPDATE areas SET "
            "nombre = CASE WHEN :set_nombre THEN :nombre ELSE nombre END, "
            "codigo = CASE WHEN :set_codigo THEN :codigo ELSE codigo END, "
            "nivel = CASE WHEN :set_nivel THEN :nivel ELSE nivel END, "
            "parent_area_id = CASE WHEN :set_parent THEN :parent ELSE parent_area_id END, "
            "responsable_user_id = CASE WHEN :set_resp THEN :resp ELSE responsable_user_id END, "
            "updated_at = now() "
            "WHERE id=:id AND tenant_id=:t RETURNING *"
        ),
        {
            "set_nombre": "nombre" in changes, "nombre": changes.get("nombre"),
            "set_codigo": "codigo" in changes, "codigo": changes.get("codigo"),
            "set_nivel": "nivel" in changes, "nivel": changes.get("nivel"),
            "set_parent": "parent_area_id" in changes, "parent": changes.get("parent_area_id"),
            "set_resp": "responsable_user_id" in changes, "resp": changes.get("responsable_user_id"),
            "id": area_id, "t": tenant_id,
        },
    )).mappings().first()

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="area",
        entity_id=area_id,
        action="area_updated",
        user_id=user_id,
        payload=changes,
    )

    return dict(row)


# ==============================================================================
# Operaciones de Cargos Orgánicos
# ==============================================================================

async def _validar_titular_cargo(
    session: AsyncSession,
    tenant_id: str,
    cargo_id: Optional[str],
    tipo_cargo: TipoCargo,
    titular_user_id: Optional[str],
) -> None:
    """Aplica la regla de que quien es titular del cargo de delegado no puede serlo de ningún otro."""
    if not titular_user_id:
        return

    # Verificar existencia del usuario
    user = (await session.execute(
        text("SELECT id FROM users WHERE id=:u"),
        {"u": titular_user_id},
    )).first()
    if not user:
        raise RbacError(404, "El usuario titular no existe.")

    # 1. Si el cargo actual es delegado_proteccion_datos: no puede tener ningún otro cargo activo
    if tipo_cargo == TipoCargo.delegado_proteccion_datos:
        query_sql = (
            "SELECT id, nombre, tipo_cargo FROM cargos_organicos "
            "WHERE titular_user_id = :u AND tenant_id = :t "
            "AND (valid_to IS NULL OR valid_to > now())"
        )
        params: dict[str, Any] = {"u": titular_user_id, "t": tenant_id}
        if cargo_id:
            query_sql += " AND id <> :cid"
            params["cid"] = cargo_id

        otro_cargo = (await session.execute(text(query_sql), params)).mappings().first()
        if otro_cargo:
            raise RbacError(
                409,
                f"El titular del cargo de Delegado no puede ocupar ningún otro cargo en la organización (Art. 18.1/18.2). Ya ocupa: {otro_cargo['nombre']}",
            )

    # 2. Si el cargo actual NO es delegado, verificar si el usuario ya es titular del cargo de delegado
    else:
        query_sql = (
            "SELECT id, nombre FROM cargos_organicos "
            "WHERE titular_user_id = :u AND tenant_id = :t "
            "AND tipo_cargo = 'delegado_proteccion_datos' "
            "AND (valid_to IS NULL OR valid_to > now())"
        )
        params = {"u": titular_user_id, "t": tenant_id}
        if cargo_id:
            query_sql += " AND id <> :cid"
            params["cid"] = cargo_id

        cargo_dpd = (await session.execute(text(query_sql), params)).mappings().first()
        if cargo_dpd:
            raise RbacError(
                409,
                "El usuario ya es titular del cargo de Delegado de Protección de Datos y no puede ocupar otros cargos (Art. 18.1/18.2).",
            )


async def crear_cargo(
    session: AsyncSession,
    tenant_id: str,
    payload: CargoCreate,
    user_id: Optional[str] = None,
) -> dict[str, Any]:
    await fijar_tenant(session, tenant_id)

    area = await _obtener_area(session, tenant_id, payload.area_id)
    if not area:
        raise RbacError(404, "Área especificada no encontrada.")

    # El cargo de delegado es de asesoría: reporta a la alta dirección (Art. 50 de la ley) y no puede ser jefatura operativa
    if payload.tipo_cargo == TipoCargo.delegado_proteccion_datos:
        if payload.es_jefatura:
            raise RbacError(400, "El cargo de Delegado de Protección de Datos es de asesoría y no puede ser jefatura de una unidad operativa.")
        if area.get("nivel") != NivelArea.alta_direccion.value:
            # Puede depender/adscribirse a alta dirección
            pass

    if payload.reporta_a_cargo_id:
        cargo_padre = await _obtener_cargo(session, tenant_id, payload.reporta_a_cargo_id)
        if not cargo_padre:
            raise RbacError(404, "El cargo al que reporta no existe.")

    # Validar jefatura única activa
    if payload.es_jefatura:
        jefatura_existente = (await session.execute(
            text(
                "SELECT id FROM cargos_organicos "
                "WHERE area_id=:a AND tenant_id=:t AND es_jefatura=TRUE "
                "AND (valid_to IS NULL OR valid_to > now())"
            ),
            {"a": payload.area_id, "t": tenant_id},
        )).first()
        if jefatura_existente:
            raise RbacError(409, "El área ya posee una jefatura activa designada.")

    # Validar titular
    await _validar_titular_cargo(session, tenant_id, None, payload.tipo_cargo, payload.titular_user_id)

    cargo_id = str(uuid4())
    row = (await session.execute(
        text(
            "INSERT INTO cargos_organicos ("
            "id, tenant_id, area_id, nombre, tipo_cargo, es_jefatura, "
            "reporta_a_cargo_id, titular_user_id, valid_to"
            ") VALUES (:id, :t, :a, :n, :tc, :j, :r, :tit, :vt) RETURNING *"
        ),
        {
            "id": cargo_id,
            "t": tenant_id,
            "a": payload.area_id,
            "n": payload.nombre,
            "tc": payload.tipo_cargo.value,
            "j": payload.es_jefatura,
            "r": payload.reporta_a_cargo_id,
            "tit": payload.titular_user_id,
            "vt": payload.valid_to,
        },
    )).mappings().first()

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="cargo_organico",
        entity_id=cargo_id,
        action="cargo_created",
        user_id=user_id,
        payload=payload.model_dump(mode="json"),
    )

    return dict(row)


async def editar_cargo(
    session: AsyncSession,
    tenant_id: str,
    cargo_id: str,
    payload: CargoUpdate,
    user_id: Optional[str] = None,
) -> dict[str, Any]:
    await fijar_tenant(session, tenant_id)
    actual = await _obtener_cargo(session, tenant_id, cargo_id)
    if not actual:
        raise RbacError(404, "Cargo no encontrado.")

    changes = payload.model_dump(exclude_unset=True)
    target_area_id = changes.get("area_id", actual["area_id"])
    target_tipo = TipoCargo(changes.get("tipo_cargo", actual["tipo_cargo"]))
    target_es_jefatura = changes.get("es_jefatura", actual["es_jefatura"])
    target_titular = changes.get("titular_user_id", actual["titular_user_id"])
    target_reporta = changes.get("reporta_a_cargo_id", actual["reporta_a_cargo_id"])

    if target_reporta:
        cargo_padre = await _obtener_cargo(session, tenant_id, target_reporta)
        if not cargo_padre:
            raise RbacError(404, "El cargo al que reporta no existe.")
        await _verificar_ciclo_cargos(session, tenant_id, cargo_id, target_reporta)

    if target_tipo == TipoCargo.delegado_proteccion_datos and target_es_jefatura:
        raise RbacError(400, "El cargo de Delegado no puede ser jefatura operativa.")

    if target_es_jefatura:
        jefatura_existente = (await session.execute(
            text(
                "SELECT id FROM cargos_organicos "
                "WHERE area_id=:a AND tenant_id=:t AND id<>:id AND es_jefatura=TRUE "
                "AND (valid_to IS NULL OR valid_to > now())"
            ),
            {"a": target_area_id, "t": tenant_id, "id": cargo_id},
        )).first()
        if jefatura_existente:
            raise RbacError(409, "El área ya posee otra jefatura activa designada.")

    await _validar_titular_cargo(session, tenant_id, cargo_id, target_tipo, target_titular)

    if not changes:
        return actual

    row = (await session.execute(
        text(
            "UPDATE cargos_organicos SET "
            "area_id = CASE WHEN :set_area THEN :area ELSE area_id END, "
            "nombre = CASE WHEN :set_nombre THEN :nombre ELSE nombre END, "
            "tipo_cargo = CASE WHEN :set_tipo THEN :tipo ELSE tipo_cargo END, "
            "es_jefatura = CASE WHEN :set_jefe THEN :jefe ELSE es_jefatura END, "
            "reporta_a_cargo_id = CASE WHEN :set_rep THEN :rep ELSE reporta_a_cargo_id END, "
            "titular_user_id = CASE WHEN :set_tit THEN :tit ELSE titular_user_id END, "
            "valid_to = CASE WHEN :set_vt THEN :vt ELSE valid_to END, "
            "updated_at = now() "
            "WHERE id=:id AND tenant_id=:t RETURNING *"
        ),
        {
            "set_area": "area_id" in changes, "area": changes.get("area_id"),
            "set_nombre": "nombre" in changes, "nombre": changes.get("nombre"),
            "set_tipo": "tipo_cargo" in changes, "tipo": changes.get("tipo_cargo"),
            "set_jefe": "es_jefatura" in changes, "jefe": changes.get("es_jefatura"),
            "set_rep": "reporta_a_cargo_id" in changes, "rep": changes.get("reporta_a_cargo_id"),
            "set_tit": "titular_user_id" in changes, "tit": changes.get("titular_user_id"),
            "set_vt": "valid_to" in changes, "vt": changes.get("valid_to"),
            "id": cargo_id, "t": tenant_id,
        },
    )).mappings().first()

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="cargo_organico",
        entity_id=cargo_id,
        action="cargo_updated",
        user_id=user_id,
        payload=payload.model_dump(mode="json", exclude_unset=True),
    )

    return dict(row)


async def asignar_titular_cargo(
    session: AsyncSession,
    tenant_id: str,
    cargo_id: str,
    titular_user_id: Optional[str],
    user_id: Optional[str] = None,
) -> dict[str, Any]:
    """Asigna o quita (vacante) el titular de un cargo orgánico."""
    return await editar_cargo(
        session=session,
        tenant_id=tenant_id,
        cargo_id=cargo_id,
        payload=CargoUpdate(titular_user_id=titular_user_id),
        user_id=user_id,
    )


# ==============================================================================
# Árbol Completo e Informe de Cobertura
# ==============================================================================

async def obtener_arbol_estructura(session: AsyncSession, tenant_id: str) -> dict[str, Any]:
    """Devuelve el árbol completo de la organización: unidades, cargos, titulares y vacantes."""
    await fijar_tenant(session, tenant_id)

    # 1. Unidades
    areas_rows = (await session.execute(
        text("SELECT * FROM areas WHERE tenant_id=:t AND deleted_at IS NULL ORDER BY nombre"),
        {"t": tenant_id},
    )).mappings().all()

    # 2. Cargos
    cargos_rows = (await session.execute(
        text(
            "SELECT c.*, u.nombre AS titular_nombre, u.email AS titular_email "
            "FROM cargos_organicos c "
            "LEFT JOIN users u ON c.titular_user_id = u.id "
            "WHERE c.tenant_id=:t "
            "ORDER BY c.nombre"
        ),
        {"t": tenant_id},
    )).mappings().all()

    cargos_por_area: dict[str, list[dict[str, Any]]] = {}
    for c in cargos_rows:
        item = dict(c)
        aid = item["area_id"]
        cargos_por_area.setdefault(aid, []).append(item)

    areas_dict: dict[str, dict[str, Any]] = {}
    for a in areas_rows:
        d = dict(a)
        d["cargos"] = cargos_por_area.get(d["id"], [])
        d["subareas"] = []
        areas_dict[d["id"]] = d

    raices: list[dict[str, Any]] = []
    for d in areas_dict.values():
        pid = d.get("parent_area_id")
        if pid and pid in areas_dict:
            areas_dict[pid]["subareas"].append(d)
        else:
            raices.append(d)

    return {
        "tenant_id": tenant_id,
        "arbol": raices,
        "total_areas": len(areas_rows),
        "total_cargos": len(cargos_rows),
    }


async def obtener_informe_cobertura(session: AsyncSession, tenant_id: str) -> dict[str, Any]:
    """Genera informe de cobertura de estructura orgánica y lista de responsables por designar.

    Detecta:
    1. Unidades sin jefatura definida.
    2. Jefaturas vacantes (sin titular).
    3. Unidades con jefatura y titular, pero sin rol 'responsable_area' asignado en user_tenant_roles.
    """
    await fijar_tenant(session, tenant_id)

    # Unidades
    areas = (await session.execute(
        text("SELECT id, nombre, codigo, nivel, parent_area_id, responsable_user_id FROM areas WHERE tenant_id=:t AND deleted_at IS NULL"),
        {"t": tenant_id},
    )).mappings().all()

    # Jefaturas vigentes
    jefaturas = (await session.execute(
        text(
            "SELECT c.*, u.nombre AS titular_nombre, u.email AS titular_email "
            "FROM cargos_organicos c "
            "LEFT JOIN users u ON c.titular_user_id = u.id "
            "WHERE c.tenant_id=:t AND c.es_jefatura=TRUE "
            "AND (c.valid_to IS NULL OR c.valid_to > now())"
        ),
        {"t": tenant_id},
    )).mappings().all()
    jefatura_por_area = {j["area_id"]: dict(j) for j in jefaturas}

    # Responsables de área vigentes
    roles_resp = (await session.execute(
        text(
            "SELECT area_id, user_id FROM user_tenant_roles "
            "WHERE tenant_id=:t AND role='responsable_area' "
            "AND (valid_to IS NULL OR valid_to > now())"
        ),
        {"t": tenant_id},
    )).all()
    responsables_por_area: dict[str, set[str]] = {}
    for aid, uid in roles_resp:
        if aid:
            responsables_por_area.setdefault(aid, set()).add(uid)

    unidades_sin_jefatura = []
    jefaturas_vacantes = []
    responsables_por_designar = []

    for a in areas:
        aid = a["id"]
        jefe = jefatura_por_area.get(aid)
        if not jefe:
            unidades_sin_jefatura.append({
                "area_id": aid,
                "nombre_area": a["nombre"],
                "nivel": a["nivel"],
            })
        else:
            titular_id = jefe.get("titular_user_id")
            if not titular_id:
                jefaturas_vacantes.append({
                    "area_id": aid,
                    "nombre_area": a["nombre"],
                    "cargo_id": jefe["id"],
                    "nombre_cargo": jefe["nombre"],
                })
            else:
                # Comprobar si ya tiene rol responsable_area para esa área
                resps = responsables_por_area.get(aid, set())
                if titular_id not in resps:
                    responsables_por_designar.append({
                        "area_id": aid,
                        "nombre_area": a["nombre"],
                        "cargo_id": jefe["id"],
                        "nombre_cargo": jefe["nombre"],
                        "candidato_user_id": titular_id,
                        "candidato_nombre": jefe.get("titular_nombre"),
                        "candidato_email": jefe.get("titular_email"),
                        "motivo": "Titular de la jefatura de unidad sin nombramiento formal de responsable_area",
                    })

    return {
        "tenant_id": tenant_id,
        "total_unidades": len(areas),
        "unidades_sin_jefatura": unidades_sin_jefatura,
        "jefaturas_vacantes": jefaturas_vacantes,
        "responsables_por_designar": responsables_por_designar,
    }


# ==============================================================================
# Incompatibilidades con Delegado (Compuerta para ORG-06)
# ==============================================================================

async def cargos_incompatibles_con_dpd(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
) -> list[dict[str, Any]]:
    """Retorna la lista de cargos activos del usuario que son incompatibles con ser Delegado.

    Base legal: Art. 16.1 a 16.3 Reglamento del Delegado y Art. 56.1 Reglamento General.
    """
    await fijar_tenant(session, tenant_id)
    rows = (await session.execute(
        text(
            "SELECT c.id, c.nombre, c.tipo_cargo, c.area_id, a.nombre AS area_nombre "
            "FROM cargos_organicos c "
            "JOIN areas a ON c.area_id = a.id "
            "WHERE c.tenant_id=:t AND c.titular_user_id=:u "
            "AND (c.valid_to IS NULL OR c.valid_to > now()) "
            "AND c.tipo_cargo IN :tipos"
        ),
        {
            "t": tenant_id,
            "u": user_id,
            "tipos": tuple(t.value for t in TIPOS_INCOMPATIBLES_CON_DPD),
        },
    )).mappings().all()

    return [dict(r) for r in rows]
