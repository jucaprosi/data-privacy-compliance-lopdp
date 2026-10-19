# ¤rbac-tenant
# ¤dpo-independencia
# ¤arbitro
"""Pruebas del flujo de alta de responsables de área (RM-10, PRD §5.3.1).

El encargado solicita, el implementador aprueba o rechaza y ejecuta.
Aislamiento:
- Cada prueba contra BD corre en una transacción que SIEMPRE se revierte (rollback).
- La migración 20261018_responsable_requests se instala dentro de la transacción usando
  SQL_ASCENDENTE si la tabla no existe en la BD de pruebas.
- RLS se valida con el rol lopdp_app y SET LOCAL ROLE.
"""
from __future__ import annotations

import importlib.util
import uuid
from pathlib import Path
from typing import Optional

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from app_core.db.session import get_session
from features.organizacion import organizacion_service as svc
from features.organizacion.organizacion_service import RbacError, Role
from main import app

pytestmark = pytest.mark.asyncio

MIGRACION_RM10 = (
    Path(__file__).resolve().parent.parent
    / "alembic"
    / "versions"
    / "20261018_responsable_requests.py"
)


def _sentencias_migracion_rm10() -> tuple[list[str], list[str]]:
    spec = importlib.util.spec_from_file_location("mig_rm10", MIGRACION_RM10)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return list(mod.SQL_ASCENDENTE), list(mod.SQL_DESCENDENTE)


@pytest_asyncio.fixture
async def conn(db_engine):
    """Conexión transaccional que SIEMPRE se revierte al finalizar cada prueba."""
    async with db_engine.connect() as c:
        tx = await c.begin()
        try:
            yield c
        finally:
            await tx.rollback()


@pytest_asyncio.fixture
async def session(conn):
    return AsyncSession(bind=conn, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def tabla_rm10(conn):
    """Asegura que la tabla y triggers de RM-10 estén disponibles en la transacción de prueba."""
    asc, _ = _sentencias_migracion_rm10()
    # Si la tabla ya existe, no la volvemos a crear
    existe = (
        await conn.execute(
            text(
                "SELECT 1 FROM information_schema.tables WHERE table_name = 'area_responsable_requests'"
            )
        )
    ).first()
    if not existe:
        for sentencia in asc:
            await conn.execute(text(sentencia))
    yield


async def _as_app_role(session: AsyncSession, tenant_id: Optional[str] = None):
    exists = (
        await session.execute(
            text("SELECT 1 FROM pg_roles WHERE rolname = 'lopdp_app'")
        )
    ).first()
    if not exists:
        pytest.skip("Rol lopdp_app no existe en la base de datos")
    await session.execute(text("SET LOCAL ROLE lopdp_app"))
    if tenant_id:
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :t, true)"),
            {"t": tenant_id},
        )


async def _crear_tenant(conn, tamano: Optional[str] = "mediana") -> str:
    tid = f"rm10-t-{uuid.uuid4().hex[:10]}"
    await conn.execute(
        text(
            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
            "VALUES (:i, :n, :r, :ruc, :tam)"
        ),
        {
            "i": tid,
            "n": tid,
            "r": tid,
            "ruc": f"RUC{uuid.uuid4().hex[:12]}",
            "tam": tamano,
        },
    )
    return tid


async def _crear_usuario(conn) -> str:
    uid = f"rm10-u-{uuid.uuid4().hex[:10]}"
    await conn.execute(
        text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, :n)"),
        {"i": uid, "e": f"{uid}@test.local", "n": uid},
    )
    return uid


async def _crear_area(conn, tenant_id: str, nombre: str = "Seguridad") -> str:
    aid = f"rm10-a-{uuid.uuid4().hex[:10]}"
    await conn.execute(
        text(
            "INSERT INTO areas (id, tenant_id, nombre, codigo) VALUES (:i, :t, :n, :c)"
        ),
        {"i": aid, "t": tenant_id, "n": nombre, "c": f"COD-{aid[:6]}"},
    )
    return aid


async def _asignar_rol(
    conn, user_id: str, tenant_id: str, role: str, area_id: Optional[str] = None
) -> str:
    rid = f"rm10-r-{uuid.uuid4().hex[:10]}"
    await conn.execute(
        text(
            "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role, area_id) "
            "VALUES (:i, :u, :t, :r, :a)"
        ),
        {"i": rid, "u": user_id, "t": tenant_id, "r": role, "a": area_id},
    )
    return rid


# ============================================================================
# 1. FLUJO COMPLETO Y AUDITORÍA
# ============================================================================


async def test_flujo_completo_crear_aprobar_ejecutar(conn, session):
    tid = await _crear_tenant(conn, "mediana")
    encargado = await _crear_usuario(conn)
    implementador = await _crear_usuario(conn)
    destino = await _crear_usuario(conn)
    area = await _crear_area(conn, tid, "Tecnologia")

    # 1. Crear solicitud
    solicitud = await svc.create_responsable_request(
        session,
        tid,
        encargado,
        svc.ResponsableRequestCreate(target_user_id=destino, area_id=area, motivo="Asignacion inicial"),
    )
    req_id = solicitud["id"]
    assert solicitud["estado"] == "pendiente"
    assert solicitud["requested_by"] == encargado
    assert solicitud["target_user_id"] == destino
    assert solicitud["area_id"] == area

    # 2. Aprobar solicitud
    aprobada = await svc.approve_responsable_request(
        session,
        tid,
        implementador,
        req_id,
        svc.ResponsableRequestDecision(notas="Aprobado por implementador"),
    )
    assert aprobada["estado"] == "aprobada"
    assert aprobada["decided_by"] == implementador
    assert aprobada["decision_notes"] == "Aprobado por implementador"

    # 3. Ejecutar solicitud
    ejecutada = await svc.execute_responsable_request(session, tid, implementador, req_id)
    assert ejecutada["estado"] == "ejecutada"
    assert ejecutada["executed_by"] == implementador
    assert ejecutada["assignment_id"] is not None

    # Verificar que el rol quedó asignado con request_id enlazado
    rol_db = (
        await conn.execute(
            text(
                "SELECT role, area_id, request_id FROM user_tenant_roles WHERE id = :id"
            ),
            {"id": ejecutada["assignment_id"]},
        )
    ).mappings().first()
    assert rol_db["role"] == "responsable_area"
    assert rol_db["area_id"] == area
    assert rol_db["request_id"] == req_id

    # 4. Verificar auditoría de los 3 pasos
    eventos = (
        await conn.execute(
            text(
                "SELECT action, user_id FROM audit_events WHERE entity_id = :id ORDER BY timestamp ASC"
            ),
            {"id": req_id},
        )
    ).mappings().all()
    acciones = [e["action"] for e in eventos]
    assert acciones == [
        "responsable_request_created",
        "responsable_request_approved",
        "responsable_request_executed",
    ]


# ============================================================================
# 2. TRANSICIONES INVÁLIDAS Y SALTOS DE PASO
# ============================================================================


async def test_ejecutar_sin_aprobar_falla_409(conn, session):
    tid = await _crear_tenant(conn, "mediana")
    encargado = await _crear_usuario(conn)
    implementador = await _crear_usuario(conn)
    destino = await _crear_usuario(conn)
    area = await _crear_area(conn, tid)

    sol = await svc.create_responsable_request(
        session,
        tid,
        encargado,
        svc.ResponsableRequestCreate(target_user_id=destino, area_id=area),
    )
    with pytest.raises(RbacError) as exc:
        await svc.execute_responsable_request(session, tid, implementador, sol["id"])
    assert exc.value.code == 409


async def test_aprobar_dos_veces_falla_409(conn, session):
    tid = await _crear_tenant(conn, "mediana")
    encargado = await _crear_usuario(conn)
    implementador = await _crear_usuario(conn)
    destino = await _crear_usuario(conn)
    area = await _crear_area(conn, tid)

    sol = await svc.create_responsable_request(
        session,
        tid,
        encargado,
        svc.ResponsableRequestCreate(target_user_id=destino, area_id=area),
    )
    await svc.approve_responsable_request(
        session, tid, implementador, sol["id"], svc.ResponsableRequestDecision()
    )
    with pytest.raises(RbacError) as exc:
        await svc.approve_responsable_request(
            session, tid, implementador, sol["id"], svc.ResponsableRequestDecision()
        )
    assert exc.value.code == 409


async def test_aprobar_tras_rechazar_falla_409(conn, session):
    tid = await _crear_tenant(conn, "mediana")
    encargado = await _crear_usuario(conn)
    implementador = await _crear_usuario(conn)
    destino = await _crear_usuario(conn)
    area = await _crear_area(conn, tid)

    sol = await svc.create_responsable_request(
        session,
        tid,
        encargado,
        svc.ResponsableRequestCreate(target_user_id=destino, area_id=area),
    )
    await svc.reject_responsable_request(
        session, tid, implementador, sol["id"], svc.ResponsableRequestDecision()
    )
    with pytest.raises(RbacError) as exc:
        await svc.approve_responsable_request(
            session, tid, implementador, sol["id"], svc.ResponsableRequestDecision()
        )
    assert exc.value.code == 409


async def test_aprobar_tras_cancelar_falla_409(conn, session):
    tid = await _crear_tenant(conn, "mediana")
    encargado = await _crear_usuario(conn)
    implementador = await _crear_usuario(conn)
    destino = await _crear_usuario(conn)
    area = await _crear_area(conn, tid)

    sol = await svc.create_responsable_request(
        session,
        tid,
        encargado,
        svc.ResponsableRequestCreate(target_user_id=destino, area_id=area),
    )
    await svc.cancel_responsable_request(session, tid, encargado, sol["id"])
    with pytest.raises(RbacError) as exc:
        await svc.approve_responsable_request(
            session, tid, implementador, sol["id"], svc.ResponsableRequestDecision()
        )
    assert exc.value.code == 409


# ============================================================================
# 3. REGLAS DE CANCELACIÓN
# ============================================================================


async def test_cancelar_solo_quien_solicito(conn, session):
    tid = await _crear_tenant(conn, "mediana")
    encargado1 = await _crear_usuario(conn)
    encargado2 = await _crear_usuario(conn)
    destino = await _crear_usuario(conn)
    area = await _crear_area(conn, tid)

    sol = await svc.create_responsable_request(
        session,
        tid,
        encargado1,
        svc.ResponsableRequestCreate(target_user_id=destino, area_id=area),
    )
    with pytest.raises(RbacError) as exc:
        await svc.cancel_responsable_request(session, tid, encargado2, sol["id"])
    assert exc.value.code == 403


async def test_cancelar_solo_si_pendiente(conn, session):
    tid = await _crear_tenant(conn, "mediana")
    encargado = await _crear_usuario(conn)
    implementador = await _crear_usuario(conn)
    destino = await _crear_usuario(conn)
    area = await _crear_area(conn, tid)

    sol = await svc.create_responsable_request(
        session,
        tid,
        encargado,
        svc.ResponsableRequestCreate(target_user_id=destino, area_id=area),
    )
    await svc.approve_responsable_request(
        session, tid, implementador, sol["id"], svc.ResponsableRequestDecision()
    )
    with pytest.raises(RbacError) as exc:
        await svc.cancel_responsable_request(session, tid, encargado, sol["id"])
    assert exc.value.code == 409


# ============================================================================
# 4. TABLA DE VALIDACIÓN DEL USUARIO DESTINO (PRD §5.3.1 y RM-16)
# ============================================================================


async def test_destino_sin_roles_o_admin_o_implementador_es_permitido(conn, session):
    tid = await _crear_tenant(conn, "mediana")
    encargado = await _crear_usuario(conn)
    implementador = await _crear_usuario(conn)
    destino = await _crear_usuario(conn)
    area = await _crear_area(conn, tid)
    await _asignar_rol(conn, destino, tid, "admin_organizacion")

    sol = await svc.create_responsable_request(
        session,
        tid,
        encargado,
        svc.ResponsableRequestCreate(target_user_id=destino, area_id=area),
    )
    aprobada = await svc.approve_responsable_request(
        session, tid, implementador, sol["id"], svc.ResponsableRequestDecision()
    )
    assert aprobada["estado"] == "aprobada"


async def test_destino_responsable_en_otra_area_es_permitido(conn, session):
    tid = await _crear_tenant(conn, "mediana")
    encargado = await _crear_usuario(conn)
    implementador = await _crear_usuario(conn)
    destino = await _crear_usuario(conn)
    area1 = await _crear_area(conn, tid, "Area 1")
    area2 = await _crear_area(conn, tid, "Area 2")
    await _asignar_rol(conn, destino, tid, "responsable_area", area_id=area1)

    sol = await svc.create_responsable_request(
        session,
        tid,
        encargado,
        svc.ResponsableRequestCreate(target_user_id=destino, area_id=area2),
    )
    aprobada = await svc.approve_responsable_request(
        session, tid, implementador, sol["id"], svc.ResponsableRequestDecision()
    )
    assert aprobada["estado"] == "aprobada"


@pytest.mark.parametrize("tamano", ["micro", "pequena"])
async def test_destino_encargado_permitido_en_micro_y_pequena(conn, session, tamano):
    tid = await _crear_tenant(conn, tamano)
    encargado = await _crear_usuario(conn)
    implementador = await _crear_usuario(conn)
    destino = await _crear_usuario(conn)
    area = await _crear_area(conn, tid)
    await _asignar_rol(conn, destino, tid, "coordinador")

    sol = await svc.create_responsable_request(
        session,
        tid,
        encargado,
        svc.ResponsableRequestCreate(target_user_id=destino, area_id=area),
    )
    aprobada = await svc.approve_responsable_request(
        session, tid, implementador, sol["id"], svc.ResponsableRequestDecision()
    )
    assert aprobada["estado"] == "aprobada"


@pytest.mark.parametrize("tamano", ["mediana", "corporativo"])
async def test_destino_encargado_rechazado_en_mediana_y_corporativo(conn, session, tamano):
    tid = await _crear_tenant(conn, tamano)
    encargado = await _crear_usuario(conn)
    implementador = await _crear_usuario(conn)
    destino = await _crear_usuario(conn)
    area = await _crear_area(conn, tid)
    await _asignar_rol(conn, destino, tid, "coordinador")

    sol = await svc.create_responsable_request(
        session,
        tid,
        encargado,
        svc.ResponsableRequestCreate(target_user_id=destino, area_id=area),
    )
    with pytest.raises(ErrorNegocio) as exc:
        await svc.approve_responsable_request(
            session, tid, implementador, sol["id"], svc.ResponsableRequestDecision()
        )
    assert exc.value.status_code == 409
    assert exc.value.code == "SOD_VIOLATION"


async def test_destino_sin_tamano_rechazado_falla_cerrado(conn, session):
    tid = await _crear_tenant(conn, tamano=None)
    encargado = await _crear_usuario(conn)
    implementador = await _crear_usuario(conn)
    destino = await _crear_usuario(conn)
    area = await _crear_area(conn, tid)
    await _asignar_rol(conn, destino, tid, "coordinador")

    sol = await svc.create_responsable_request(
        session,
        tid,
        encargado,
        svc.ResponsableRequestCreate(target_user_id=destino, area_id=area),
    )
    with pytest.raises(ErrorNegocio) as exc:
        await svc.approve_responsable_request(
            session, tid, implementador, sol["id"], svc.ResponsableRequestDecision()
        )
    assert exc.value.status_code == 409
    assert exc.value.code == "TENANT_SIZE_NOT_CONFIGURED"


async def test_destino_dpo_rechazado_dpo_independence(conn, session):
    tid = await _crear_tenant(conn, "mediana")
    encargado = await _crear_usuario(conn)
    implementador = await _crear_usuario(conn)
    destino = await _crear_usuario(conn)
    area = await _crear_area(conn, tid)
    await _asignar_rol(conn, destino, tid, "dpo")

    sol = await svc.create_responsable_request(
        session,
        tid,
        encargado,
        svc.ResponsableRequestCreate(target_user_id=destino, area_id=area),
    )
    with pytest.raises(ErrorNegocio) as exc:
        await svc.approve_responsable_request(
            session, tid, implementador, sol["id"], svc.ResponsableRequestDecision()
        )
    assert exc.value.status_code == 409
    assert exc.value.code == "DPO_INDEPENDENCE_VIOLATED"


async def test_destino_ya_es_responsable_de_esa_misma_area(conn, session):
    tid = await _crear_tenant(conn, "mediana")
    encargado = await _crear_usuario(conn)
    implementador = await _crear_usuario(conn)
    destino = await _crear_usuario(conn)
    area = await _crear_area(conn, tid)
    await _asignar_rol(conn, destino, tid, "responsable_area", area_id=area)

    sol = await svc.create_responsable_request(
        session,
        tid,
        encargado,
        svc.ResponsableRequestCreate(target_user_id=destino, area_id=area),
    )
    with pytest.raises(RbacError) as exc:
        await svc.approve_responsable_request(
            session, tid, implementador, sol["id"], svc.ResponsableRequestDecision()
        )
    assert exc.value.code == 409
    assert "ya es responsable" in exc.value.detail


async def test_asignarse_a_si_mismo_falla_409(conn, session):
    tid = await _crear_tenant(conn, "mediana")
    actor = await _crear_usuario(conn)
    area = await _crear_area(conn, tid)

    sol = await svc.create_responsable_request(
        session,
        tid,
        actor,
        svc.ResponsableRequestCreate(target_user_id=actor, area_id=area),
    )
    with pytest.raises(RbacError) as exc:
        await svc.approve_responsable_request(
            session, tid, actor, sol["id"], svc.ResponsableRequestDecision()
        )
    assert exc.value.code == 409
    assert "a sí mismo" in exc.value.detail


# ============================================================================
# 5. REVALIDACIÓN AL EJECUTAR (DESTINO CAMBIÓ TRAS APROBAR)
# ============================================================================


async def test_revalidacion_al_ejecutar_si_destino_pasa_a_dpo(conn, session):
    tid = await _crear_tenant(conn, "mediana")
    encargado = await _crear_usuario(conn)
    implementador = await _crear_usuario(conn)
    destino = await _crear_usuario(conn)
    area = await _crear_area(conn, tid)

    sol = await svc.create_responsable_request(
        session,
        tid,
        encargado,
        svc.ResponsableRequestCreate(target_user_id=destino, area_id=area),
    )
    await svc.approve_responsable_request(
        session, tid, implementador, sol["id"], svc.ResponsableRequestDecision()
    )

    # El destino adquiere el rol DPO antes de la ejecución
    await _asignar_rol(conn, destino, tid, "dpo")

    with pytest.raises(ErrorNegocio) as exc:
        await svc.execute_responsable_request(session, tid, implementador, sol["id"])
    assert exc.value.status_code == 409
    assert exc.value.code == "DPO_INDEPENDENCE_VIOLATED"


# ============================================================================
# 6. ÁREA NUEVA POR NOMBRE: REUTILIZAR SI EXISTE, NO DUPLICAR
# ============================================================================


async def test_area_nueva_por_nombre_se_reutiliza_si_ya_existe(conn, session):
    tid = await _crear_tenant(conn, "mediana")
    encargado = await _crear_usuario(conn)
    implementador = await _crear_usuario(conn)
    destino = await _crear_usuario(conn)
    area_existente = await _crear_area(conn, tid, "Contabilidad")

    sol = await svc.create_responsable_request(
        session,
        tid,
        encargado,
        svc.ResponsableRequestCreate(target_user_id=destino, area_nombre="contabilidad"),
    )
    await svc.approve_responsable_request(
        session, tid, implementador, sol["id"], svc.ResponsableRequestDecision()
    )
    ejecutada = await svc.execute_responsable_request(session, tid, implementador, sol["id"])

    assert ejecutada["area_id"] == area_existente
    # Comprobar que no se creó un área duplicada
    total_areas = (
        await conn.execute(
            text("SELECT count(*) FROM areas WHERE tenant_id = :t AND lower(nombre) = 'contabilidad'"),
            {"t": tid},
        )
    ).scalar()
    assert total_areas == 1


async def test_area_nueva_por_nombre_se_crea_si_no_existe(conn, session):
    tid = await _crear_tenant(conn, "mediana")
    encargado = await _crear_usuario(conn)
    implementador = await _crear_usuario(conn)
    destino = await _crear_usuario(conn)

    sol = await svc.create_responsable_request(
        session,
        tid,
        encargado,
        svc.ResponsableRequestCreate(target_user_id=destino, area_nombre="Auditoría Interna"),
    )
    await svc.approve_responsable_request(
        session, tid, implementador, sol["id"], svc.ResponsableRequestDecision()
    )
    ejecutada = await svc.execute_responsable_request(session, tid, implementador, sol["id"])
    assert ejecutada["area_id"] is not None

    creada = (
        await conn.execute(
            text("SELECT nombre FROM areas WHERE id = :id"), {"id": ejecutada["area_id"]}
        )
    ).mappings().first()
    assert creada["nombre"] == "Auditoría Interna"


# ============================================================================
# 7. TRIGGER DE BD CON UPDATES DIRECTOS
# ============================================================================


async def test_trigger_directo_bloquea_transiciones_invalidas(conn):
    tid = await _crear_tenant(conn, "mediana")
    u1, u2 = await _crear_usuario(conn), await _crear_usuario(conn)
    area = await _crear_area(conn, tid)
    rid = str(uuid.uuid4())

    await conn.execute(
        text(
            "INSERT INTO area_responsable_requests (id, tenant_id, target_user_id, area_id, requested_by) "
            "VALUES (:i, :t, :u, :a, :rb)"
        ),
        {"i": rid, "t": tid, "u": u2, "a": area, "rb": u1},
    )

    # De pendiente a ejecutada directamente debe fallar en el trigger
    with pytest.raises(IntegrityError) as exc:
        await conn.execute(
            text("UPDATE area_responsable_requests SET estado = 'ejecutada' WHERE id = :id"),
            {"id": rid},
        )
    assert "RESPONSABLE_REQUEST_TRANSITION" in str(exc.value.orig)


async def test_trigger_directo_bloquea_cambios_en_estados_terminales(conn):
    tid = await _crear_tenant(conn, "mediana")
    u1, u2 = await _crear_usuario(conn), await _crear_usuario(conn)
    area = await _crear_area(conn, tid)
    rid = str(uuid.uuid4())

    await conn.execute(
        text(
            "INSERT INTO area_responsable_requests (id, tenant_id, target_user_id, area_id, requested_by) "
            "VALUES (:i, :t, :u, :a, :rb)"
        ),
        {"i": rid, "t": tid, "u": u2, "a": area, "rb": u1},
    )
    # Pasar a rechazada
    await conn.execute(
        text("UPDATE area_responsable_requests SET estado = 'rechazada', decided_by = :u WHERE id = :id"),
        {"u": u1, "id": rid},
    )
    # Intentar modificarla una vez rechazada
    with pytest.raises(IntegrityError) as exc:
        await conn.execute(
            text("UPDATE area_responsable_requests SET decision_notes = 'otra cosa' WHERE id = :id"),
            {"id": rid},
        )
    assert "esta rechazada y no admite cambios" in str(exc.value.orig)


async def test_trigger_directo_bloquea_cambiar_destinatario_o_solicitante(conn):
    tid = await _crear_tenant(conn, "mediana")
    u1, u2, u3 = await _crear_usuario(conn), await _crear_usuario(conn), await _crear_usuario(conn)
    area = await _crear_area(conn, tid)
    rid = str(uuid.uuid4())

    await conn.execute(
        text(
            "INSERT INTO area_responsable_requests (id, tenant_id, target_user_id, area_id, requested_by) "
            "VALUES (:i, :t, :u, :a, :rb)"
        ),
        {"i": rid, "t": tid, "u": u2, "a": area, "rb": u1},
    )
    with pytest.raises(IntegrityError) as exc:
        await conn.execute(
            text("UPDATE area_responsable_requests SET target_user_id = :u3 WHERE id = :id"),
            {"u3": u3, "id": rid},
        )
    assert "no se puede cambiar el tenant, el destinatario ni quien solicita" in str(exc.value.orig)


# ============================================================================
# 8. ÍNDICE ÚNICO DE SOLICITUD ABIERTA
# ============================================================================


async def test_indice_unico_solicitud_abierta(conn, session):
    tid = await _crear_tenant(conn, "mediana")
    encargado = await _crear_usuario(conn)
    destino = await _crear_usuario(conn)
    area = await _crear_area(conn, tid)

    await svc.create_responsable_request(
        session,
        tid,
        encargado,
        svc.ResponsableRequestCreate(target_user_id=destino, area_id=area),
    )
    # Segunda solicitud idéntica mientras está pendiente debe dar 409
    with pytest.raises(RbacError) as exc:
        await svc.create_responsable_request(
            session,
            tid,
            encargado,
            svc.ResponsableRequestCreate(target_user_id=destino, area_id=area),
        )
    assert exc.value.code == 409
    assert "Ya hay una solicitud abierta" in exc.value.detail


# ============================================================================
# 9. AISLAMIENTO POR TENANT Y RLS (SET LOCAL ROLE lopdp_app)
# ============================================================================


async def test_aislamiento_rls_por_tenant(conn, session):
    t1 = await _crear_tenant(conn, "mediana")
    t2 = await _crear_tenant(conn, "mediana")
    u1, u2 = await _crear_usuario(conn), await _crear_usuario(conn)
    a1 = await _crear_area(conn, t1)
    a2 = await _crear_area(conn, t2)

    sol1 = await svc.create_responsable_request(
        session,
        t1,
        u1,
        svc.ResponsableRequestCreate(target_user_id=u1, area_id=a1),
    )
    sol2 = await svc.create_responsable_request(
        session,
        t2,
        u2,
        svc.ResponsableRequestCreate(target_user_id=u2, area_id=a2),
    )

    # Bajo el rol lopdp_app con tenant 1 fijado
    await _as_app_role(session, t1)
    filas_t1 = (
        await session.execute(text("SELECT id FROM area_responsable_requests"))
    ).scalars().all()
    assert sol1["id"] in filas_t1
    assert sol2["id"] not in filas_t1

    # Cambiar contexto a tenant 2
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": t2}
    )
    filas_t2 = (
        await session.execute(text("SELECT id FROM area_responsable_requests"))
    ).scalars().all()
    assert sol2["id"] in filas_t2
    assert sol1["id"] not in filas_t2


# ============================================================================
# 10. FLUJO HTTP COMPLETO CON CABECERAS
# ============================================================================


async def test_flujo_http_completo(conn, session):
    tid = await _crear_tenant(conn, "mediana")
    encargado = await _crear_usuario(conn)
    implementador = await _crear_usuario(conn)
    destino = await _crear_usuario(conn)
    area = await _crear_area(conn, tid, "Finanzas")

    # Asignar membresía activa para autenticación HTTP
    await _asignar_rol(conn, encargado, tid, "coordinador")
    await _asignar_rol(conn, implementador, tid, "implementador")

    headers_enc = {"X-Tenant-ID": tid, "X-User-ID": encargado, "X-Role": "coordinador"}
    headers_impl = {"X-Tenant-ID": tid, "X-User-ID": implementador, "X-Role": "implementador"}

    # Mockeamos get_session para reutilizar la conexión y transacción viva
    app.dependency_overrides[get_session] = lambda: session

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 1. Crear solicitud (POST)
            res = await ac.post(
                "/api/v1/areas/responsable-requests",
                json={"target_user_id": destino, "area_id": area, "motivo": "Flujo HTTP"},
                headers=headers_enc,
            )
            assert res.status_code == 201, res.text
            sol_id = res.json()["id"]

            # 2. Listar solicitudes (GET)
            res_list = await ac.get("/api/v1/areas/responsable-requests?estado=pendiente", headers=headers_enc)
            assert res_list.status_code == 200
            assert any(r["id"] == sol_id for r in res_list.json())

            # 3. Ver detalle (GET /{id})
            res_det = await ac.get(f"/api/v1/areas/responsable-requests/{sol_id}", headers=headers_impl)
            assert res_det.status_code == 200
            assert res_det.json()["id"] == sol_id

            # 4. Aprobar (POST /{id}/approve)
            res_app = await ac.post(
                f"/api/v1/areas/responsable-requests/{sol_id}/approve",
                json={"notas": "Aprobado HTTP"},
                headers=headers_impl,
            )
            assert res_app.status_code == 200
            assert res_app.json()["estado"] == "aprobada"

            # 5. Ejecutar (POST /{id}/execute)
            res_exe = await ac.post(
                f"/api/v1/areas/responsable-requests/{sol_id}/execute",
                headers=headers_impl,
            )
            assert res_exe.status_code == 200
            assert res_exe.json()["estado"] == "ejecutada"
            assert res_exe.json()["assignment_id"] is not None
    finally:
        app.dependency_overrides.pop(get_session, None)
