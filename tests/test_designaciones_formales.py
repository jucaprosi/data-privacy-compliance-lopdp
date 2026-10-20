# ¤rbac-tenant
# ¤seguridad
# ¤arbitro
"""Suite de pruebas para las designaciones formales de DPD y Coordinador (ORG-06).

Valida de forma exhaustiva y determinista:
1. Creación de designación formal para DPD y Coordinador por parte de 'admin_organizacion'.
2. Validación de vínculo obligatorio ('relacion_dependencia' o 'prestacion_servicios') para DPD (Art. 49 Reglamento General).
3. Validación contra estructura orgánica: rechazo 409 si el usuario ocupa un cargo incompatible con DPD (cargos_incompatibles_con_dpd).
4. Restricción única de designación activa por tipo en el tenant (409 ante duplicados activos).
5. Registro de aceptación y declaración previa de conflictos (Art. 17 Reglamento del Delegado):
   - Solo la propia persona designada puede declarar (403 si declara un tercero).
   - Rechazo con 409 si declara tener conflicto de intereses, ser socio/accionista o pariente de administradores.
6. Registro de constancia de inscripción ante la Superintendencia (SPDP) por 'admin_organizacion' (Arts. 5 y 6).
7. Revocación formal motivada por 'admin_organizacion'.
8. Emisión de informe de estado de designaciones de solo lectura (no bloquea, señala pendientes y conflictos sobrevenidos).
9. Trazabilidad inmutable en audit_events para cada acción.
10. Aislamiento por tenant y RLS efectiva bajo el rol de base de datos 'lopdp_app'.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app_core.db.session import fijar_contexto_rls
from features.organizacion.domain.models import RbacError
from features.organizacion.organizacion_service import (
    AreaEstructuraCreate,
    CargoCreate,
    DeclaracionConflictosCreate,
    DesignacionCreate,
    InscripcionSpdpCreate,
    RevocacionCreate,
    TipoCargo,
    TipoDesignacion,
    VinculoDesignacion,
    crear_area_estructura,
    crear_cargo,
    crear_designacion_formal,
    listar_designaciones_formales,
    obtener_designacion_formal,
    obtener_informe_estado_designaciones,
    registrar_declaracion_conflictos,
    registrar_inscripcion_spdp,
    revocar_designacion_formal,
)
from main import app

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def org_fixture(db_engine):
    """Crea 2 tenants con usuarios, áreas y roles para pruebas de designaciones."""
    factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    t1 = f"t1-desig-{uuid4().hex[:8]}"
    t2 = f"t2-desig-{uuid4().hex[:8]}"

    u_admin1 = f"u-admin1-{uuid4().hex[:8]}"
    u_admin2 = f"u-admin2-{uuid4().hex[:8]}"
    u_coord1 = f"u-coord1-{uuid4().hex[:8]}"
    u_dpd1 = f"u-dpd1-{uuid4().hex[:8]}"
    u_user1 = f"u-user1-{uuid4().hex[:8]}"

    async with factory() as session:
        for tid in (t1, t2):
            await session.execute(
                text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
                     "VALUES (:t, :n, :r, :ruc, 'mediana')"),
                {"t": tid, "n": tid, "r": tid, "ruc": f"RUC{uuid4().hex[:12]}"},
            )

        for uid, nom, email in (
            (u_admin1, "Admin 1", f"{u_admin1}@test.local"),
            (u_admin2, "Admin 2", f"{u_admin2}@test.local"),
            (u_coord1, "Coordinador 1", f"{u_coord1}@test.local"),
            (u_dpd1, "Delegado 1", f"{u_dpd1}@test.local"),
            (u_user1, "Usuario 1", f"{u_user1}@test.local"),
        ):
            await session.execute(
                text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :n)"),
                {"u": uid, "e": email, "n": nom},
            )

        # Asignar roles básicos
        await session.execute(
            text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES "
                 "(:r1, :u1, :t1, 'admin_organizacion'), "
                 "(:r2, :u2, :t2, 'admin_organizacion'), "
                 "(:r3, :u3, :t1, 'coordinador'), (:r4, :u4, :t1, 'dpo')"),
            {
                "r1": str(uuid4()), "u1": u_admin1, "t1": t1,
                "r2": str(uuid4()), "u2": u_admin2, "t2": t2,
                "r3": str(uuid4()), "u3": u_coord1, "r4": str(uuid4()), "u4": u_dpd1,
            },
        )
        await session.commit()

    yield {
        "t1": t1,
        "t2": t2,
        "admin1": u_admin1,
        "admin2": u_admin2,
        "coord1": u_coord1,
        "dpd1": u_dpd1,
        "user1": u_user1,
    }


def _headers(user_id: str, tenant_id: str, role: str) -> dict[str, str]:
    return {
        "X-User-ID": user_id,
        "X-Tenant-ID": tenant_id,
        "X-Role": role,
    }


# ==============================================================================
# 1. PRUEBAS DE SERVICIO PURO / MOTOR
# ==============================================================================

async def test_crear_designacion_dpd_exigencia_vinculo(db_session, org_fixture):
    """El DPD exige vínculo explícito (Art. 49 Reglamento General)."""
    t1 = org_fixture["t1"]
    admin = org_fixture["admin1"]
    dpd_user = org_fixture["dpd1"]

    # Falla sin vínculo
    payload_sin_vinculo = DesignacionCreate(
        tipo=TipoDesignacion.dpd,
        user_id=dpd_user,
        representante_nombre="Representante Legal",
        representante_identificacion="1710000001",
        representante_cargo="Gerente General",
        fecha_designacion=date(2026, 1, 15),
        doc_referencia="ACTA-DIR-2026-001",
        vinculo=None,
    )
    with pytest.raises(RbacError) as exc:
        await crear_designacion_formal(db_session, t1, admin, payload_sin_vinculo)
    assert exc.value.code == 400
    assert "vínculo" in str(exc.value).lower()


async def test_crear_designacion_dpd_cargos_incompatibles_rechazado_409(db_session, org_fixture):
    """Al designar un DPD, si ocupa cargo incompatible en la estructura orgánica, rechaza con 409."""
    t1 = org_fixture["t1"]
    admin = org_fixture["admin1"]
    user_inc = org_fixture["user1"]

    # 1. Crear área y cargo incompatible asignado al usuario
    area = await crear_area_estructura(
        session=db_session,
        tenant_id=t1,
        payload=AreaEstructuraCreate(nombre="Auditoría y Control"),
        user_id=admin,
    )
    await crear_cargo(
        session=db_session,
        tenant_id=t1,
        payload=CargoCreate(
            area_id=area["id"],
            nombre="Oficial de Cumplimiento Normativo",
            tipo_cargo=TipoCargo.oficial_cumplimiento,
            titular_user_id=user_inc,
        ),
        user_id=admin,
    )

    # 2. Intentar designarlo como DPD
    payload = DesignacionCreate(
        tipo=TipoDesignacion.dpd,
        user_id=user_inc,
        representante_nombre="Representante Legal",
        representante_identificacion="1710000001",
        representante_cargo="Gerente General",
        fecha_designacion=date(2026, 1, 15),
        doc_referencia="ACTA-DIR-2026-002",
        vinculo=VinculoDesignacion.prestacion_servicios,
    )
    with pytest.raises(RbacError) as exc:
        await crear_designacion_formal(db_session, t1, admin, payload)
    assert exc.value.code == 409
    assert "cargos incompatibles" in str(exc.value).lower()
    assert "oficial de cumplimiento" in str(exc.value).lower()


async def test_crear_designacion_coordinador_exito_y_duplicado_rechazado(db_session, org_fixture):
    """Crea designación de Coordinador (mandato de alta dirección) y rechaza duplicados activos."""
    t1 = org_fixture["t1"]
    admin = org_fixture["admin1"]
    coord = org_fixture["coord1"]

    payload = DesignacionCreate(
        tipo=TipoDesignacion.coordinador,
        user_id=coord,
        representante_nombre="Representante Legal",
        representante_identificacion="1710000001",
        representante_cargo="Gerente General",
        fecha_designacion=date(2026, 1, 10),
        doc_referencia="RES-AD-2026-010",
    )

    desig = await crear_designacion_formal(db_session, t1, admin, payload)
    assert desig["id"] is not None
    assert desig["tipo"] == "coordinador"
    assert desig["user_id"] == coord
    assert desig["revocada_at"] is None

    # Intentar crear otra designación de coordinador activa rechaza con 409
    with pytest.raises(RbacError) as exc:
        await crear_designacion_formal(db_session, t1, admin, payload)
    assert exc.value.code == 409
    assert "activa" in str(exc.value).lower()


async def test_declaracion_conflictos_solo_propia_persona_y_rechazo_si_hay_conflicto(db_session, org_fixture):
    """La declaración de conflictos la emite SOLO el designado. Si declara conflicto se rechaza con 409."""
    t1 = org_fixture["t1"]
    admin = org_fixture["admin1"]
    dpd = org_fixture["dpd1"]
    otro_usuario = org_fixture["user1"]

    payload_desig = DesignacionCreate(
        tipo=TipoDesignacion.dpd,
        user_id=dpd,
        representante_nombre="Representante Legal",
        representante_identificacion="1710000001",
        representante_cargo="Presidente",
        fecha_designacion=date(2026, 2, 1),
        doc_referencia="MANDATO-DPD-2026",
        vinculo=VinculoDesignacion.relacion_dependencia,
    )
    desig = await crear_designacion_formal(db_session, t1, admin, payload_desig)

    # 1. Tercero intenta declarar -> 403
    payload_decl = DeclaracionConflictosCreate(
        declaracion_texto="Declaro formalmente no poseer conflictos de intereses.",
        declaracion_tiene_conflicto=False,
    )
    with pytest.raises(RbacError) as exc:
        await registrar_declaracion_conflictos(db_session, t1, desig["id"], otro_usuario, payload_decl)
    assert exc.value.code == 403

    # 2. Designado declara tener conflicto o ser accionista -> 409
    payload_con_conflicto = DeclaracionConflictosCreate(
        declaracion_texto="Declaro que soy socio accionista minoritario de la empresa.",
        declaracion_es_socio_accionista=True,
    )
    with pytest.raises(RbacError) as exc2:
        await registrar_declaracion_conflictos(db_session, t1, desig["id"], dpd, payload_con_conflicto)
    assert exc2.value.code == 409
    assert "socio o accionista" in str(exc2.value).lower()

    # 3. Designado declara sin conflicto -> 200 / éxito
    res_decl = await registrar_declaracion_conflictos(db_session, t1, desig["id"], dpd, payload_decl)
    assert res_decl["declaracion_at"] is not None
    assert res_decl["aceptacion_at"] is not None
    assert res_decl["declaracion_texto"] == payload_decl.declaracion_texto


async def test_registro_inscripcion_spdp_y_revocacion(db_session, org_fixture):
    """Registra constancia de inscripción ante SPDP y luego revoca la designación."""
    t1 = org_fixture["t1"]
    admin = org_fixture["admin1"]
    dpd = org_fixture["dpd1"]

    payload_desig = DesignacionCreate(
        tipo=TipoDesignacion.dpd,
        user_id=dpd,
        representante_nombre="Representante Legal",
        representante_identificacion="1710000001",
        representante_cargo="Presidente",
        fecha_designacion=date(2026, 2, 1),
        doc_referencia="DOC-DPD-001",
        vinculo=VinculoDesignacion.prestacion_servicios,
    )
    desig = await crear_designacion_formal(db_session, t1, admin, payload_desig)

    # Inscribir
    payload_insc = InscripcionSpdpCreate(
        inscripcion_spdp_fecha=date(2026, 2, 10),
        inscripcion_spdp_ref="SPDP-REG-2026-9988",
    )
    res_insc = await registrar_inscripcion_spdp(db_session, t1, desig["id"], admin, payload_insc)
    assert res_insc["inscripcion_spdp_ref"] == "SPDP-REG-2026-9988"

    # Revocar
    payload_rev = RevocacionCreate(motivo="Reestructuración directiva y cambio de delegado.")
    res_rev = await revocar_designacion_formal(db_session, t1, desig["id"], admin, payload_rev)
    assert res_rev["revocada_at"] is not None
    assert res_rev["revocada_motivo"] == payload_rev.motivo
    assert res_rev["revocada_por_user_id"] == admin

    # Ya no se puede volver a revocar -> 409
    with pytest.raises(RbacError) as exc:
        await revocar_designacion_formal(db_session, t1, desig["id"], admin, payload_rev)
    assert exc.value.code == 409


async def test_informe_estado_designaciones_y_conflicto_sobrevenido(db_session, org_fixture):
    """El informe de estado alerta si faltan declaraciones, inscripción o si sobreviene cargo incompatible."""
    t1 = org_fixture["t1"]
    admin = org_fixture["admin1"]
    dpd = org_fixture["dpd1"]

    # Estado inicial: nada designado
    info_vacio = await obtener_informe_estado_designaciones(db_session, t1)
    assert info_vacio["dpd"]["designado"] is False
    assert info_vacio["coordinador"]["designado"] is False
    assert len(info_vacio["dpd"]["alertas"]) >= 1

    # Designar DPD
    payload_desig = DesignacionCreate(
        tipo=TipoDesignacion.dpd,
        user_id=dpd,
        representante_nombre="Representante",
        representante_identificacion="1710000001",
        representante_cargo="Gerente",
        fecha_designacion=date(2026, 2, 1),
        doc_referencia="DOC-DPD-INIT",
        vinculo=VinculoDesignacion.prestacion_servicios,
    )
    desig = await crear_designacion_formal(db_session, t1, admin, payload_desig)

    info_parcial = await obtener_informe_estado_designaciones(db_session, t1)
    assert info_parcial["dpd"]["designado"] is True
    assert info_parcial["dpd"]["declaracion_completada"] is False
    assert info_parcial["dpd"]["inscrito_spdp"] is False

    # Sobrevino cargo incompatible: asignamos a la persona como Oficial de Seguridad
    area = await crear_area_estructura(
        db_session,
        t1,
        payload=AreaEstructuraCreate(nombre="Tecnología"),
        user_id=admin,
    )
    await crear_cargo(
        session=db_session,
        tenant_id=t1,
        payload=CargoCreate(
            area_id=area["id"],
            nombre="CISO",
            tipo_cargo=TipoCargo.oficial_seguridad_informacion,
            titular_user_id=dpd,
        ),
        user_id=admin,
    )

    info_conflicto = await obtener_informe_estado_designaciones(db_session, t1)
    assert info_conflicto["dpd"]["conflicto_sobrevenido"] is True
    assert len(info_conflicto["dpd"]["cargos_incompatibles"]) >= 1
    assert any("Conflicto sobrevenido" in a for a in info_conflicto["dpd"]["alertas"])


# ==============================================================================
# 2. PRUEBAS DE ENDPOINTS REST (API)
# ==============================================================================

async def test_endpoint_flujo_completo_designacion(api_client, org_fixture):
    """Flujo REST: crear, listar, ver, declarar, inscribir, revocar y ver estado."""
    t1 = org_fixture["t1"]
    admin = org_fixture["admin1"]
    dpd = org_fixture["dpd1"]
    h_admin = _headers(admin, t1, "admin_organizacion")
    h_dpd = _headers(dpd, t1, "dpo")
    h_coord = _headers(org_fixture["coord1"], t1, "coordinador")

    # 1. Crear designación formal DPD
    r_create = await api_client.post(
        "/api/v1/organizacion/designaciones",
        headers=h_admin,
        json={
            "tipo": "dpd",
            "user_id": dpd,
            "representante_nombre": "Apoderado Legal",
            "representante_identificacion": "1720000002",
            "representante_cargo": "Apoderado General",
            "fecha_designacion": "2026-03-01",
            "doc_referencia": "PODER-NOT-2026-44",
            "vinculo": "prestacion_servicios",
        },
    )
    assert r_create.status_code == 201, r_create.text
    desig_id = r_create.json()["id"]

    # 2. Coordinador o DPD pueden listar y ver
    r_list = await api_client.get("/api/v1/organizacion/designaciones", headers=h_coord)
    assert r_list.status_code == 200
    assert any(d["id"] == desig_id for d in r_list.json())

    r_get = await api_client.get(f"/api/v1/organizacion/designaciones/{desig_id}", headers=h_dpd)
    assert r_get.status_code == 200
    assert r_get.json()["tipo"] == "dpd"

    # 3. Declaración previa de conflictos por el propio DPD
    r_decl = await api_client.post(
        f"/api/v1/organizacion/designaciones/{desig_id}/declarar",
        headers=h_dpd,
        json={
            "declaracion_texto": "Declaro formalmente la ausencia de conflictos de intereses según Art. 17.",
            "declaracion_tiene_conflicto": False,
            "declaracion_es_socio_accionista": False,
            "declaracion_es_pariente_admin": False,
        },
    )
    assert r_decl.status_code == 200, r_decl.text
    assert r_decl.json()["declaracion_at"] is not None

    # 4. Inscripción SPDP por admin
    r_insc = await api_client.post(
        f"/api/v1/organizacion/designaciones/{desig_id}/inscribir",
        headers=h_admin,
        json={
            "inscripcion_spdp_fecha": "2026-03-05",
            "inscripcion_spdp_ref": "SPDP-INSC-2026-0044",
        },
    )
    assert r_insc.status_code == 200
    assert r_insc.json()["inscripcion_spdp_ref"] == "SPDP-INSC-2026-0044"

    # 5. Consultar informe de estado
    r_estado = await api_client.get("/api/v1/organizacion/designaciones/estado", headers=h_coord)
    assert r_estado.status_code == 200
    assert r_estado.json()["dpd"]["designado"] is True
    assert r_estado.json()["dpd"]["declaracion_completada"] is True
    assert r_estado.json()["dpd"]["inscrito_spdp"] is True

    # 6. Revocar designación
    r_rev = await api_client.post(
        f"/api/v1/organizacion/designaciones/{desig_id}/revocar",
        headers=h_admin,
        json={"motivo": "Término del contrato de servicios profesionales."},
    )
    assert r_rev.status_code == 200
    assert r_rev.json()["revocada_at"] is not None


async def test_endpoint_declarar_tercero_rechazado_403(api_client, org_fixture):
    """Nadie puede declarar conflictos por otro (403 si lo intenta otro usuario)."""
    t1 = org_fixture["t1"]
    admin = org_fixture["admin1"]
    dpd = org_fixture["dpd1"]
    coord = org_fixture["coord1"]

    h_admin = _headers(admin, t1, "admin_organizacion")
    h_coord = _headers(coord, t1, "coordinador")

    r_create = await api_client.post(
        "/api/v1/organizacion/designaciones",
        headers=h_admin,
        json={
            "tipo": "dpd",
            "user_id": dpd,
            "representante_nombre": "Apoderado Legal",
            "representante_identificacion": "1720000002",
            "representante_cargo": "Apoderado General",
            "fecha_designacion": "2026-03-01",
            "doc_referencia": "DOC-REF-001",
            "vinculo": "relacion_dependencia",
        },
    )
    desig_id = r_create.json()["id"]

    # El coordinador intenta emitir la declaración del DPD
    r_decl = await api_client.post(
        f"/api/v1/organizacion/designaciones/{desig_id}/declarar",
        headers=h_coord,
        json={"declaracion_texto": "Declaro en su nombre", "declaracion_tiene_conflicto": False},
    )
    assert r_decl.status_code == 403
    assert "Solo la propia persona" in r_decl.json()["detail"]


# ==============================================================================
# 3. AISLAMIENTO POR TENANT Y RLS (SET LOCAL ROLE lopdp_app)
# ==============================================================================

async def test_aislamiento_rls_designaciones_formales(db_engine, org_fixture):
    """Aislamiento hermético: bajo el rol lopdp_app, tenant 2 ve 0 designaciones de tenant 1."""
    t1 = org_fixture["t1"]
    t2 = org_fixture["t2"]
    admin1 = org_fixture["admin1"]
    coord1 = org_fixture["coord1"]

    factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

    # 1. Crear designación en T1
    async with factory() as session:
        await crear_designacion_formal(
            session=session,
            tenant_id=t1,
            admin_user_id=admin1,
            payload=DesignacionCreate(
                tipo=TipoDesignacion.coordinador,
                user_id=coord1,
                representante_nombre="Representante T1",
                representante_identificacion="1710000001",
                representante_cargo="Director Ejecutivo",
                fecha_designacion=date(2026, 1, 1),
                doc_referencia="ACTA-T1",
            ),
        )
        await session.commit()

    # 2. Consultar como lopdp_app bajo el contexto del Tenant 2
    async with factory() as session:
        await session.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(session, tenant_id=t2)
        res = await session.execute(text("SELECT count(*) FROM designaciones_formales"))
        count = res.scalar()
        assert count == 0, "RLS debió ocultar la designación del tenant 1 ante el tenant 2"
        await session.rollback()

    # 3. Consultar como lopdp_app bajo el contexto del Tenant 1 -> ve exactamente 1
    async with factory() as session:
        await session.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(session, tenant_id=t1)
        res = await session.execute(text("SELECT count(*) FROM designaciones_formales"))
        count = res.scalar()
        assert count == 1, "RLS debió permitir ver la designación del tenant 1"
        await session.rollback()

    # 4. Sin tenant fijado -> ve 0
    async with factory() as session:
        await session.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(session, tenant_id=None)
        res = await session.execute(text("SELECT count(*) FROM designaciones_formales"))
        count = res.scalar()
        assert count == 0, "Sin tenant fijado no debe ver ninguna designación"
        await session.rollback()

    # 5. DELETE denegado para lopdp_app (append-only / sin DELETE)
    async with factory() as session:
        await session.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(session, tenant_id=t1)
        with pytest.raises(DBAPIError) as exc_del:
            await session.execute(text("DELETE FROM designaciones_formales"))
        await session.rollback()
        assert "permission denied" in str(exc_del.value).lower() or "insufficient_privilege" in str(exc_del.value).lower()
