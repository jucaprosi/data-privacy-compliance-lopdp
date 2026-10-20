# ¤rbac-tenant
# ¤seguridad
# ¤arbitro
"""ORG-02: INV_LOPDP_COORDINADOR_RESPONSABLE_EXCEPCION (coordinador + responsable_area con excepción activa).

Sustituye tests/test_encargado_responsable_tamano.py (RM-16).
Valida:
1. Sin excepción SoD activa: rechaza acumular coordinador y responsable_area (SOD_VIOLATION, 409).
2. Con excepción activa y vigente: permite acumular ambos roles.
3. Con excepción vencida o revocada: rechaza (SOD_VIOLATION, 409).
4. Sin tamaño configurado en el tenant: no aprueba ni permite (TENANT_SIZE_NOT_CONFIGURED, 409).
5. Quien se beneficia de la excepción NO puede aprobarla (salvo con resolución de RL si es único admin).
6. El DPO NUNCA puede aprobar excepciones SoD (Art. 18.3 Reglamento del Delegado).
7. Aislamiento multi-tenant y RLS con rol de aplicación `lopdp_app`.
8. Registro inmutable en `audit_events`.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from features.organizacion import organizacion_service as svc

pytestmark = pytest.mark.asyncio

PASADO = datetime(2020, 1, 1, tzinfo=timezone.utc)
FUTURO = datetime.now(timezone.utc) + timedelta(days=365)


@pytest_asyncio.fixture
async def conn(db_engine):
    async with db_engine.connect() as c:
        tx = await c.begin()
        try:
            yield c
        finally:
            await tx.rollback()


@pytest_asyncio.fixture
async def session(conn):
    return AsyncSession(bind=conn, expire_on_commit=False)


async def _tenant(conn, tamano: str | None = "mediana") -> str:
    tid = f"org02-t-{uuid.uuid4().hex[:10]}"
    await conn.execute(
        text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
             "VALUES (:i, :n, :r, :ruc, :tam)"),
        {"i": tid, "n": tid, "r": tid, "ruc": f"RUC{uuid.uuid4().hex[:12]}", "tam": tamano},
    )
    return tid


async def _usuario(conn) -> str:
    uid = f"org02-u-{uuid.uuid4().hex[:10]}"
    await conn.execute(
        text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, :n)"),
        {"i": uid, "e": f"{uid}@test.local", "n": uid},
    )
    return uid


async def _rol(conn, uid: str, tid: str, role: str, valid_to: datetime | None = None) -> None:
    await conn.execute(
        text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role, valid_to) "
             "VALUES (:i, :u, :t, :r, :v)"),
        {"i": f"org02-r-{uuid.uuid4().hex[:10]}", "u": uid, "t": tid, "r": role, "v": valid_to},
    )


async def _crear_excepcion_activa(
    conn,
    tid: str,
    uid: str,
    admin_id: str,
    valid_from: datetime | None = None,
    valid_to: datetime | None = None,
    estado: str = "activa",
) -> str:
    eid = f"org02-e-{uuid.uuid4().hex[:10]}"
    vf = valid_from or (datetime.now(timezone.utc) - timedelta(minutes=5))
    vt = valid_to or (datetime.now(timezone.utc) + timedelta(days=180))
    await conn.execute(
        text("""
            INSERT INTO sod_exceptions (
                id, tenant_id, user_id, rol_existente, rol_solicitado,
                motivo, control_compensatorio_tipo, control_compensatorio_detalle,
                origen, estado, requested_by, approved_by, approved_at,
                valid_from, valid_to
            ) VALUES (
                :id, :t, :u, 'coordinador', 'responsable_area',
                'Motivo prueba', 'aprobacion_decisiones_alta_direccion', 'Detalle prueba',
                'solicitud', :estado, :adm, :adm, now(),
                :vf, :vt
            )
        """),
        {
            "id": eid,
            "t": tid,
            "u": uid,
            "estado": estado,
            "adm": admin_id,
            "vf": vf,
            "vt": vt,
        },
    )
    return eid


# ============================================================================
# 1. EVALUAR TAMAÑO Y FALLO CERRADO
# ============================================================================

@pytest.mark.parametrize("tamano", ["micro", "pequena", "mediana", "corporativo"])
async def test_tamano_valido_pasa_evaluacion(tamano):
    svc.evaluar_tamano(tamano)


@pytest.mark.parametrize("tamano", [None, "", "gigante", "MICRO"])
async def test_tamano_nulo_o_invalido_falla_cerrado(tamano):
    with pytest.raises(ErrorNegocio) as e:
        svc.evaluar_tamano(tamano)
    assert e.value.code == "TENANT_SIZE_NOT_CONFIGURED"
    assert e.value.action_required == "configure_tenant_size"


# ============================================================================
# 2. VALIDACIÓN DEL SERVICIO (REGLA SoD COORDINADOR + RESPONSABLE_AREA)
# ============================================================================

@pytest.mark.parametrize("par", [("coordinador", "responsable_area"), ("responsable_area", "coordinador")])
async def test_sin_excepcion_rechaza_acumulacion_en_cualquier_tamano(conn, session, par):
    for tamano in ["micro", "pequena", "mediana", "corporativo"]:
        tid = await _tenant(conn, tamano)
        uid = await _usuario(conn)
        await _rol(conn, uid, tid, par[0])

        with pytest.raises(ErrorNegocio) as e:
            await svc.verificar_excepcion_coordinador_responsable(session, tid, uid, par[1])
        assert e.value.code == "SOD_VIOLATION"


@pytest.mark.parametrize("par", [("coordinador", "responsable_area"), ("responsable_area", "coordinador")])
async def test_con_excepcion_activa_y_vigente_permite_acumulacion(conn, session, par):
    for tamano in ["micro", "pequena", "mediana", "corporativo"]:
        tid = await _tenant(conn, tamano)
        uid, admin = await _usuario(conn), await _usuario(conn)
        await _rol(conn, uid, tid, par[0])
        await _crear_excepcion_activa(conn, tid, uid, admin)

        # Debe permitir sin lanzar excepción
        await svc.verificar_excepcion_coordinador_responsable(session, tid, uid, par[1])


async def test_sin_tamano_configurado_falla_cerrado_aun_con_excepcion(conn, session):
    tid = await _tenant(conn, None)
    uid, admin = await _usuario(conn), await _usuario(conn)
    await _rol(conn, uid, tid, "coordinador")
    await _crear_excepcion_activa(conn, tid, uid, admin)

    with pytest.raises(ErrorNegocio) as e:
        await svc.verificar_excepcion_coordinador_responsable(session, tid, uid, "responsable_area")
    assert e.value.code == "TENANT_SIZE_NOT_CONFIGURED"


async def test_con_excepcion_vencida_rechaza_acumulacion(conn, session):
    tid = await _tenant(conn, "mediana")
    uid, admin = await _usuario(conn), await _usuario(conn)
    await _rol(conn, uid, tid, "coordinador")
    await _crear_excepcion_activa(conn, tid, uid, admin, valid_to=PASADO)

    with pytest.raises(ErrorNegocio) as e:
        await svc.verificar_excepcion_coordinador_responsable(session, tid, uid, "responsable_area")
    assert e.value.code == "SOD_VIOLATION"


async def test_con_excepcion_revocada_rechaza_acumulacion(conn, session):
    tid = await _tenant(conn, "mediana")
    uid, admin = await _usuario(conn), await _usuario(conn)
    await _rol(conn, uid, tid, "coordinador")
    await _crear_excepcion_activa(conn, tid, uid, admin, estado="revocada")

    with pytest.raises(ErrorNegocio) as e:
        await svc.verificar_excepcion_coordinador_responsable(session, tid, uid, "responsable_area")
    assert e.value.code == "SOD_VIOLATION"


async def test_grant_role_aplica_regla_de_excepcion(conn, session):
    tid = await _tenant(conn, "mediana")
    uid, admin = await _usuario(conn), await _usuario(conn)
    await _rol(conn, uid, tid, "coordinador")

    # Sin excepción falla
    with pytest.raises(ErrorNegocio) as e:
        await svc.grant_role(session, tid, admin, svc.RoleGrant(user_id=uid, role="responsable_area"))
    assert e.value.code == "SOD_VIOLATION"

    # Con excepción activa pasa
    await _crear_excepcion_activa(conn, tid, uid, admin)
    fila = await svc.grant_role(session, tid, admin, svc.RoleGrant(user_id=uid, role="responsable_area"))
    assert fila["role"] == "responsable_area"


# ============================================================================
# 3. TRIGGER DE LA BASE DE DATOS (RESPALDO EXÓGENO)
# ============================================================================

async def test_trigger_bd_bloquea_sin_excepcion(conn):
    tid = await _tenant(conn, "mediana")
    uid = await _usuario(conn)
    await _rol(conn, uid, tid, "coordinador")

    with pytest.raises(IntegrityError) as exc:
        await _rol(conn, uid, tid, "responsable_area")
    assert "SOD_VIOLATION" in str(exc.value.orig)


async def test_trigger_bd_permite_con_excepcion_activa(conn):
    tid = await _tenant(conn, "mediana")
    uid, admin = await _usuario(conn), await _usuario(conn)
    await _rol(conn, uid, tid, "coordinador")
    await _crear_excepcion_activa(conn, tid, uid, admin)

    # Debe insertar sin error de integridad
    await _rol(conn, uid, tid, "responsable_area")


async def test_trigger_bd_falla_cerrado_sin_tamano(conn):
    tid = await _tenant(conn, None)
    uid = await _usuario(conn)
    await _rol(conn, uid, tid, "coordinador")

    with pytest.raises(IntegrityError) as exc:
        await _rol(conn, uid, tid, "responsable_area")
    assert "TENANT_SIZE_NOT_CONFIGURED" in str(exc.value.orig)


async def test_servicio_traduce_error_del_trigger(conn, session, monkeypatch):
    async def _bypassed(*a, **k):
        return None

    monkeypatch.setitem(svc.grant_role.__globals__, "verificar_excepcion_coordinador_responsable", _bypassed)
    tid = await _tenant(conn, "mediana")
    uid, admin = await _usuario(conn), await _usuario(conn)
    await _rol(conn, uid, tid, "coordinador")

    with pytest.raises(ErrorNegocio) as e:
        await svc.grant_role(session, tid, admin, svc.RoleGrant(user_id=uid, role="responsable_area"))
    assert e.value.code == "SOD_VIOLATION" and e.value.status_code == 409


# ============================================================================
# 4. FLUJO DE GESTIÓN DE EXCEPCIONES SoD (SOLICITAR, APROBAR, REVOCAR)
# ============================================================================

async def test_flujo_solicitud_aprobacion_y_revocacion(conn, session):
    tid = await _tenant(conn, "mediana")
    beneficiario = await _usuario(conn)
    solicitante = await _usuario(conn)
    admin = await _usuario(conn)

    # 1. Solicitar excepción
    payload_crear = svc.ExcepcionSoDCreate(
        user_id=beneficiario,
        rol_existente="coordinador",
        rol_solicitado="responsable_area",
        motivo="Transición organizacional temporal",
        control_compensatorio_tipo=svc.ControlCompensatorioTipo.aprobacion_decisiones_alta_direccion,
        control_compensatorio_detalle="Supervisión semanal por gerencia general",
        valid_to=datetime.now(timezone.utc) + timedelta(days=90),
    )
    sol = await svc.solicitar_excepcion_sod(session, tid, solicitante, payload_crear)
    assert sol["estado"] == "pendiente"
    assert sol["user_id"] == beneficiario

    # 2. Listar
    lista = await svc.listar_excepciones_sod(session, tid)
    assert len(lista) >= 1
    assert any(x["id"] == sol["id"] for x in lista)

    # 3. Ver por id
    detalle = await svc.obtener_excepcion_sod(session, tid, sol["id"])
    assert detalle["id"] == sol["id"]

    # 4. Aprobar por admin_organizacion
    aprobada = await svc.aprobar_excepcion_sod(
        session, tid, admin, "admin_organizacion", sol["id"], svc.ExcepcionSoDAprobar()
    )
    assert aprobada["estado"] == "activa"
    assert aprobada["approved_by"] == admin

    # 5. Revocar
    revocada = await svc.revocar_excepcion_sod(
        session, tid, admin, sol["id"], svc.ExcepcionSoDRevocar(motivo="Fin del periodo de transición")
    )
    assert revocada["estado"] == "revocada"
    assert revocada["motivo_revocacion"] == "Fin del periodo de transición"


async def test_beneficiario_no_puede_aprobar_su_propia_excepcion(conn, session):
    tid = await _tenant(conn, "mediana")
    beneficiario = await _usuario(conn)
    admin_otro = await _usuario(conn)
    await _rol(conn, beneficiario, tid, "admin_organizacion")
    await _rol(conn, admin_otro, tid, "admin_organizacion")

    payload_crear = svc.ExcepcionSoDCreate(
        user_id=beneficiario,
        rol_existente="coordinador",
        rol_solicitado="responsable_area",
        motivo="Auto-solicitud",
        control_compensatorio_tipo=svc.ControlCompensatorioTipo.verificacion_tercero_externo,
        control_compensatorio_detalle="Auditor externo semestral",
        valid_to=datetime.now(timezone.utc) + timedelta(days=60),
    )
    sol = await svc.solicitar_excepcion_sod(session, tid, beneficiario, payload_crear)

    with pytest.raises(svc.RbacError) as exc:
        await svc.aprobar_excepcion_sod(
            session, tid, beneficiario, "admin_organizacion", sol["id"], svc.ExcepcionSoDAprobar()
        )
    assert exc.value.code == 403


async def test_beneficiario_unico_admin_exige_resolucion_representante_legal(conn, session):
    tid = await _tenant(conn, "mediana")
    beneficiario = await _usuario(conn)
    await _rol(conn, beneficiario, tid, "admin_organizacion")

    payload_crear = svc.ExcepcionSoDCreate(
        user_id=beneficiario,
        rol_existente="coordinador",
        rol_solicitado="responsable_area",
        motivo="Único admin en la empresa",
        control_compensatorio_tipo=svc.ControlCompensatorioTipo.observaciones_periodicas_delegado,
        control_compensatorio_detalle="Informe mensual del DPO",
        valid_to=datetime.now(timezone.utc) + timedelta(days=60),
    )
    sol = await svc.solicitar_excepcion_sod(session, tid, beneficiario, payload_crear)

    # Sin resolución -> 400
    with pytest.raises(svc.RbacError) as exc:
        await svc.aprobar_excepcion_sod(
            session, tid, beneficiario, "admin_organizacion", sol["id"], svc.ExcepcionSoDAprobar(resolucion_referencia=None)
        )
    assert exc.value.code == 400

    # Con resolución del representante legal -> 200
    aprobada = await svc.aprobar_excepcion_sod(
        session,
        tid,
        beneficiario,
        "admin_organizacion",
        sol["id"],
        svc.ExcepcionSoDAprobar(resolucion_referencia="ACTA-DIRECTORIO-2026-001"),
    )
    assert aprobada["estado"] == "activa"
    assert aprobada["resolucion_referencia"] == "ACTA-DIRECTORIO-2026-001"


async def test_dpo_nunca_puede_aprobar_excepciones_sod(conn, session):
    tid = await _tenant(conn, "mediana")
    uid = await _usuario(conn)
    dpo = await _usuario(conn)
    await _rol(conn, dpo, tid, "dpo")

    payload_crear = svc.ExcepcionSoDCreate(
        user_id=uid,
        rol_existente="coordinador",
        rol_solicitado="responsable_area",
        motivo="Solicitud ordinaria",
        control_compensatorio_tipo=svc.ControlCompensatorioTipo.aprobacion_decisiones_alta_direccion,
        control_compensatorio_detalle="Supervisión",
        valid_to=datetime.now(timezone.utc) + timedelta(days=30),
    )
    sol = await svc.solicitar_excepcion_sod(session, tid, uid, payload_crear)

    # Intento de aprobación por DPO -> 403 (Art. 18.3 Reglamento)
    with pytest.raises(svc.RbacError) as exc:
        await svc.aprobar_excepcion_sod(
            session, tid, dpo, "dpo", sol["id"], svc.ExcepcionSoDAprobar()
        )
    assert exc.value.code == 403
    assert "DPO no puede aprobar" in exc.value.detail


async def test_dpo_puede_registrar_observaciones_no_vinculantes(conn, session):
    tid = await _tenant(conn, "mediana")
    uid = await _usuario(conn)
    dpo = await _usuario(conn)
    await _rol(conn, dpo, tid, "dpo")

    payload_crear = svc.ExcepcionSoDCreate(
        user_id=uid,
        rol_existente="coordinador",
        rol_solicitado="responsable_area",
        motivo="Solicitud ordinaria",
        control_compensatorio_tipo=svc.ControlCompensatorioTipo.observaciones_periodicas_delegado,
        control_compensatorio_detalle="Revisión DPO",
        valid_to=datetime.now(timezone.utc) + timedelta(days=30),
    )
    sol = await svc.solicitar_excepcion_sod(session, tid, uid, payload_crear)

    obs = await svc.agregar_observacion_dpo(
        session, tid, dpo, sol["id"], svc.ExcepcionSoDObservacionDpo(observaciones="El DPO advierte monitorear el RAT")
    )
    assert obs["observaciones_dpo"] == "El DPO advierte monitorear el RAT"
    assert obs["observaciones_dpo_by"] == dpo


# ============================================================================
# 5. AISLAMIENTO MULTI-TENANT Y RLS (lopdp_app)
# ============================================================================

async def test_aislamiento_multi_tenant_y_rls(conn, session):
    t1 = await _tenant(conn, "mediana")
    t2 = await _tenant(conn, "mediana")
    u1, adm1 = await _usuario(conn), await _usuario(conn)
    adm2 = await _usuario(conn)

    # Crear excepción en T1
    e1 = await _crear_excepcion_activa(conn, t1, u1, adm1)

    # T2 intenta ver la excepción de T1 -> 404
    with pytest.raises(svc.RbacError) as exc:
        await svc.obtener_excepcion_sod(session, t2, e1)
    assert exc.value.code == 404

    # T2 intenta aprobarla -> 404
    with pytest.raises(svc.RbacError) as exc:
        await svc.aprobar_excepcion_sod(
            session, t2, adm2, "admin_organizacion", e1, svc.ExcepcionSoDAprobar()
        )
    assert exc.value.code == 404

    # Verificar RLS directa como rol lopdp_app
    await conn.execute(text("SET LOCAL ROLE lopdp_app"))
    await conn.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, true)"),
        {"tid": str(t2)},
    )
    res = await conn.execute(text("SELECT count(*) FROM sod_exceptions WHERE id = :id"), {"id": e1})
    assert res.scalar() == 0, "RLS debió ocultar la fila ante lopdp_app de otro tenant"


# ============================================================================
# 6. REGISTRO EN AUDIT_EVENTS
# ============================================================================

async def test_audit_events_registra_solicitud_y_aprobacion(conn, session):
    tid = await _tenant(conn, "mediana")
    uid, admin = await _usuario(conn), await _usuario(conn)

    payload_crear = svc.ExcepcionSoDCreate(
        user_id=uid,
        rol_existente="coordinador",
        rol_solicitado="responsable_area",
        motivo="Prueba de auditoria",
        control_compensatorio_tipo=svc.ControlCompensatorioTipo.aprobacion_decisiones_alta_direccion,
        control_compensatorio_detalle="Supervision",
        valid_to=datetime.now(timezone.utc) + timedelta(days=45),
    )
    sol = await svc.solicitar_excepcion_sod(session, tid, admin, payload_crear)
    await svc.aprobar_excepcion_sod(session, tid, admin, "admin_organizacion", sol["id"], svc.ExcepcionSoDAprobar())

    eventos = (await conn.execute(
        text("SELECT action FROM audit_events WHERE entity_id = :id ORDER BY timestamp"),
        {"id": sol["id"]},
    )).scalars().all()

    assert "sod_exception_requested" in eventos
    assert "sod_exception_approved" in eventos
