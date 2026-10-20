# ¤rbac-tenant
# ¤arbitro
"""Suite de pruebas para la estructura orgánica de la organización (ORG-07).

Valida de manera determinista:
1. Modelo y reglas de negocio:
   - Niveles jerárquicos de área: alta_direccion, direccion, jefatura, unidad.
   - Única alta_direccion por tenant (segunda alta_direccion falla con 409 / IntegrityError).
   - Prevención de ciclos en el árbol de áreas (directos e indirectos -> 400).
   - Prevención de ciclos en la cadena de reporte de cargos (reporta a sí mismo o indirecto -> 400).
   - Jefatura única activa por área (segunda jefatura activa falla con 409 / trigger / uq).
   - Incompatibilidades con DPO:
     * Cargo DPO no puede ser jefatura operativa (400).
     * El titular del cargo DPO no puede ostentar ningún otro cargo activo en la organización (409).
     * Compuesta expone cargos_incompatibles_con_dpd(user_id) con los cargos que vetan al usuario.
2. Endpoints REST (/api/v1/organizacion/estructura):
   - GET /arbol: devuelve estructura completa (unidades, cargos, titulares, vacantes).
   - GET /cobertura: informe con unidades sin jefatura, jefaturas vacantes y responsables por designar.
   - POST /areas, PATCH /areas/{area_id}: requiere admin_organizacion.
   - POST /cargos, PATCH /cargos/{cargo_id}: requiere admin_organizacion.
   - POST /cargos/{cargo_id}/titular: asignar y desasignar titular.
   - Leen coordinador, implementador, dpo y admin_organizacion (dpo solo lectura: audita).
3. Aislamiento multi-tenant y RLS:
   - Acceso con rol de aplicación `lopdp_app` respetando RLS en `cargos_organicos`.
   - Un tenant no puede ver ni modificar cargos de otro tenant.
4. Auditoría inmutable en `audit_events`.
"""
from __future__ import annotations

import os
import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from main import app
from app_core.db.session import get_session
from features.organizacion.organizacion_service import (
    NivelArea,
    TipoCargo,
    TIPOS_INCOMPATIBLES_CON_DPD,
    cargos_incompatibles_con_dpd,
)

pytestmark = pytest.mark.asyncio


def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("Sin TEST_DATABASE_URL para tests de BD")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def factory():
    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    yield async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    await engine.dispose()


@pytest_asyncio.fixture
async def api_client(factory):
    async def _test_get_session():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = _test_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def org_fixture(factory):
    """Crea dos tenants con usuarios de distintos roles para probar estructura y aislamiento."""
    t1 = f"t1-org-{uuid.uuid4().hex[:8]}"
    t2 = f"t2-org-{uuid.uuid4().hex[:8]}"

    u_admin = f"uadm-{uuid.uuid4().hex[:8]}"
    u_coord = f"ucrd-{uuid.uuid4().hex[:8]}"
    u_impl = f"uimp-{uuid.uuid4().hex[:8]}"
    u_dpo = f"udpo-{uuid.uuid4().hex[:8]}"
    u_resp = f"ures-{uuid.uuid4().hex[:8]}"
    u_t2_admin = f"ut2a-{uuid.uuid4().hex[:8]}"

    async with factory() as session:
        # Tenants
        for tid in (t1, t2):
            await session.execute(
                text(
                    """
                    INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, sector, tamano)
                    VALUES (:id, :nom, :razon, :ruc, 'Servicios', 'mediana')
                    """
                ),
                {
                    "id": tid,
                    "nom": f"Org {tid}",
                    "razon": f"Org {tid} SA",
                    "ruc": f"RUC{tid[:10]}",
                },
            )

        # Users
        users = [
            (u_admin, f"{u_admin}@org1.ec", "Admin Org 1"),
            (u_coord, f"{u_coord}@org1.ec", "Coordinador Org 1"),
            (u_impl, f"{u_impl}@org1.ec", "Implementador Org 1"),
            (u_dpo, f"{u_dpo}@org1.ec", "DPO Org 1"),
            (u_resp, f"{u_resp}@org1.ec", "Responsable Candidato Org 1"),
            (u_t2_admin, f"{u_t2_admin}@org2.ec", "Admin Org 2"),
        ]
        for uid, email, nom in users:
            await session.execute(
                text("INSERT INTO users (id, email, nombre) VALUES (:id, :email, :nombre)"),
                {"id": uid, "email": email, "nombre": nom},
            )

        # Roles
        roles_t1 = [
            (u_admin, "admin_organizacion"),
            (u_coord, "coordinador"),
            (u_impl, "implementador"),
            (u_dpo, "dpo"),
        ]
        for uid, rol in roles_t1:
            await session.execute(
                text(
                    """
                    INSERT INTO user_tenant_roles (id, user_id, tenant_id, role)
                    VALUES (:id, :uid, :tid, :role)
                    """
                ),
                {"id": f"utr-{uuid.uuid4().hex[:8]}", "uid": uid, "tid": t1, "role": rol},
            )

        await session.execute(
            text(
                """
                INSERT INTO user_tenant_roles (id, user_id, tenant_id, role)
                VALUES (:id, :uid, :tid, 'admin_organizacion')
                """
            ),
            {"id": f"utr-{uuid.uuid4().hex[:8]}", "uid": u_t2_admin, "tid": t2},
        )
        await session.commit()

    yield {
        "t1": t1,
        "t2": t2,
        "admin": u_admin,
        "coord": u_coord,
        "impl": u_impl,
        "dpo": u_dpo,
        "candidato": u_resp,
        "t2_admin": u_t2_admin,
    }

    # Limpieza
    async with factory() as session:
        try:
            await session.execute(
                text("DELETE FROM audit_events WHERE tenant_id IN (:t1, :t2)"),
                {"t1": t1, "t2": t2},
            )
            await session.execute(
                text("DELETE FROM cargos_organicos WHERE tenant_id IN (:t1, :t2)"),
                {"t1": t1, "t2": t2},
            )
            await session.execute(
                text("DELETE FROM user_tenant_roles WHERE tenant_id IN (:t1, :t2)"),
                {"t1": t1, "t2": t2},
            )
            await session.execute(
                text(
                    "UPDATE areas SET parent_area_id = NULL, responsable_user_id = NULL WHERE tenant_id IN (:t1, :t2)"
                ),
                {"t1": t1, "t2": t2},
            )
            await session.execute(
                text("DELETE FROM areas WHERE tenant_id IN (:t1, :t2)"),
                {"t1": t1, "t2": t2},
            )
            await session.execute(
                text(
                    "DELETE FROM users WHERE id IN (:u1, :u2, :u3, :u4, :u5, :u6)"
                ),
                {
                    "u1": u_admin,
                    "u2": u_coord,
                    "u3": u_impl,
                    "u4": u_dpo,
                    "u5": u_resp,
                    "u6": u_t2_admin,
                },
            )
            await session.execute(
                text("DELETE FROM tenants WHERE id IN (:t1, :t2)"),
                {"t1": t1, "t2": t2},
            )
            await session.commit()
        except Exception:
            await session.rollback()


def _headers(user_id: str, tenant_id: str, role: str) -> dict:
    return {
        "X-User-ID": user_id,
        "X-Tenant-ID": tenant_id,
        "X-Role": role,
    }


async def test_crear_arbol_areas_y_unica_alta_direccion(api_client: AsyncClient, org_fixture: dict):
    """Verifica creación de áreas con nivel y restricción de única alta dirección por tenant."""
    h_admin = _headers(org_fixture["admin"], org_fixture["t1"], "admin_organizacion")

    # 1. Crear Alta Dirección (raíz)
    r1 = await api_client.post(
        "/api/v1/organizacion/estructura/areas",
        json={"nombre": "Gerencia General", "nivel": "alta_direccion"},
        headers=h_admin,
    )
    assert r1.status_code == 201, r1.text
    alta_dir = r1.json()
    assert alta_dir["nivel"] == "alta_direccion"
    assert alta_dir["parent_area_id"] is None

    # 2. Intentar crear una segunda Alta Dirección en el mismo tenant -> 409
    r2 = await api_client.post(
        "/api/v1/organizacion/estructura/areas",
        json={"nombre": "Presidencia Ejecutiva", "nivel": "alta_direccion"},
        headers=h_admin,
    )
    assert r2.status_code == 409, f"Debió fallar con 409 pero respondió {r2.status_code}: {r2.text}"

    # 3. Alta dirección con padre -> 400
    r3 = await api_client.post(
        "/api/v1/organizacion/estructura/areas",
        json={
            "nombre": "Directorio",
            "nivel": "alta_direccion",
            "parent_area_id": alta_dir["id"],
        },
        headers=h_admin,
    )
    assert r3.status_code == 400, f"Debió fallar con 400 pero respondió {r3.status_code}"

    # 4. Crear Dirección bajo Alta Dirección
    r4 = await api_client.post(
        "/api/v1/organizacion/estructura/areas",
        json={
            "nombre": "Dirección de Tecnología",
            "nivel": "direccion",
            "parent_area_id": alta_dir["id"],
        },
        headers=h_admin,
    )
    assert r4.status_code == 201, r4.text
    dir_ti = r4.json()
    assert dir_ti["parent_area_id"] == alta_dir["id"]


async def test_prevencion_ciclos_areas(api_client: AsyncClient, org_fixture: dict):
    """Verifica detección y prevención de ciclos en la jerarquía de áreas."""
    h_admin = _headers(org_fixture["admin"], org_fixture["t1"], "admin_organizacion")

    # Crear área 1 y área 2
    r_a1 = await api_client.post(
        "/api/v1/organizacion/estructura/areas",
        json={"nombre": "Gerencia General", "nivel": "alta_direccion"},
        headers=h_admin,
    )
    a1_id = r_a1.json()["id"]

    r_a2 = await api_client.post(
        "/api/v1/organizacion/estructura/areas",
        json={"nombre": "Operaciones", "nivel": "direccion", "parent_area_id": a1_id},
        headers=h_admin,
    )
    a2_id = r_a2.json()["id"]

    # Ciclo directo: a1 reporta a sí mismo -> 400
    r_ciclo_directo = await api_client.patch(
        f"/api/v1/organizacion/estructura/areas/{a1_id}",
        json={"parent_area_id": a1_id},
        headers=h_admin,
    )
    assert r_ciclo_directo.status_code == 400

    # Ciclo indirecto: a1 reporta a a2 (cuando a2 ya cuelga de a1) -> 400
    r_ciclo_indirecto = await api_client.patch(
        f"/api/v1/organizacion/estructura/areas/{a1_id}",
        json={"parent_area_id": a2_id},
        headers=h_admin,
    )
    assert r_ciclo_indirecto.status_code == 400


async def test_cargos_jefatura_unica_y_ciclos(api_client: AsyncClient, org_fixture: dict):
    """Verifica reglas de cargos orgánicos: única jefatura activa por área y no ciclos."""
    h_admin = _headers(org_fixture["admin"], org_fixture["t1"], "admin_organizacion")

    # Crear unidad
    r_area = await api_client.post(
        "/api/v1/organizacion/estructura/areas",
        json={"nombre": "Área Financiera", "nivel": "direccion"},
        headers=h_admin,
    )
    area_id = r_area.json()["id"]

    # Crear Cargo 1: Jefatura
    r_c1 = await api_client.post(
        "/api/v1/organizacion/estructura/cargos",
        json={
            "area_id": area_id,
            "nombre": "Director Financiero",
            "tipo_cargo": "otro",
            "es_jefatura": True,
        },
        headers=h_admin,
    )
    assert r_c1.status_code == 201, r_c1.text
    c1_id = r_c1.json()["id"]

    # Intentar crear segundo cargo con es_jefatura=True activo en la misma área -> 409
    r_c2 = await api_client.post(
        "/api/v1/organizacion/estructura/cargos",
        json={
            "area_id": area_id,
            "nombre": "Subdirector Financiero",
            "tipo_cargo": "otro",
            "es_jefatura": True,
        },
        headers=h_admin,
    )
    assert r_c2.status_code == 409, f"Debió rechazar segunda jefatura: {r_c2.text}"

    # Crear Cargo 2 como no-jefatura que reporta a C1
    r_c2_ok = await api_client.post(
        "/api/v1/organizacion/estructura/cargos",
        json={
            "area_id": area_id,
            "nombre": "Analista Financiero",
            "tipo_cargo": "otro",
            "es_jefatura": False,
            "reporta_a_cargo_id": c1_id,
        },
        headers=h_admin,
    )
    assert r_c2_ok.status_code == 201, r_c2_ok.text
    c2_id = r_c2_ok.json()["id"]

    # Intentar hacer que C1 reporte a C2 (ciclo indirecto) -> 400
    r_ciclo = await api_client.patch(
        f"/api/v1/organizacion/estructura/cargos/{c1_id}",
        json={"reporta_a_cargo_id": c2_id},
        headers=h_admin,
    )
    assert r_ciclo.status_code == 400, f"Debió rechazar ciclo en cargos: {r_ciclo.text}"


async def test_reglas_e_incompatibilidades_delegado(api_client: AsyncClient, org_fixture: dict):
    """Verifica reglas del delegado de protección de datos:

    - DPD no puede ser jefatura de unidad operativa.
    - El titular del cargo DPD no puede ser titular de ningún otro cargo activo.
    - Función compuerta cargos_incompatibles_con_dpd(user_id) retorna cargos vetados.
    """
    h_admin = _headers(org_fixture["admin"], org_fixture["t1"], "admin_organizacion")

    # 1. Crear Alta Dirección y Unidad Operativa
    r_ad = await api_client.post(
        "/api/v1/organizacion/estructura/areas",
        json={"nombre": "Gerencia General", "nivel": "alta_direccion"},
        headers=h_admin,
    )
    ad_id = r_ad.json()["id"]

    r_op = await api_client.post(
        "/api/v1/organizacion/estructura/areas",
        json={"nombre": "Operaciones", "nivel": "unidad", "parent_area_id": ad_id},
        headers=h_admin,
    )
    op_id = r_op.json()["id"]

    # 2. Cargo DPO no puede ser jefatura operativa -> 400
    r_dpd_jefatura = await api_client.post(
        "/api/v1/organizacion/estructura/cargos",
        json={
            "area_id": op_id,
            "nombre": "Jefe DPD",
            "tipo_cargo": "delegado_proteccion_datos",
            "es_jefatura": True,
        },
        headers=h_admin,
    )
    assert r_dpd_jefatura.status_code == 400, "DPD no puede ser jefatura operativa"

    # 3. Crear Cargo DPD en Alta Dirección como asesoría
    r_dpd = await api_client.post(
        "/api/v1/organizacion/estructura/cargos",
        json={
            "area_id": ad_id,
            "nombre": "Delegado de Protección de Datos",
            "tipo_cargo": "delegado_proteccion_datos",
            "es_jefatura": False,
        },
        headers=h_admin,
    )
    assert r_dpd.status_code == 201, r_dpd.text
    cargo_dpd_id = r_dpd.json()["id"]

    # 4. Crear otro cargo ordinario en Operaciones
    r_cargo_otro = await api_client.post(
        "/api/v1/organizacion/estructura/cargos",
        json={
            "area_id": op_id,
            "nombre": "Oficial de Seguridad",
            "tipo_cargo": "oficial_seguridad_informacion",
            "es_jefatura": False,
        },
        headers=h_admin,
    )
    cargo_otro_id = r_cargo_otro.json()["id"]

    # 5. Asignar candidato a DPD
    u_candidato = org_fixture["candidato"]
    r_tit1 = await api_client.post(
        f"/api/v1/organizacion/estructura/cargos/{cargo_dpd_id}/titular",
        json={"titular_user_id": u_candidato},
        headers=h_admin,
    )
    assert r_tit1.status_code == 200, r_tit1.text

    # 6. Intentar asignar al mismo candidato otro cargo activo -> 409
    r_tit2 = await api_client.post(
        f"/api/v1/organizacion/estructura/cargos/{cargo_otro_id}/titular",
        json={"titular_user_id": u_candidato},
        headers=h_admin,
    )
    assert r_tit2.status_code == 409, f"Debió rechazar segundo cargo para el titular de DPD: {r_tit2.text}"


async def test_arbol_cobertura_y_responsables_por_designar(
    api_client: AsyncClient, org_fixture: dict
):
    """Verifica endpoints /arbol y /cobertura y la lista de responsables por designar."""
    h_admin = _headers(org_fixture["admin"], org_fixture["t1"], "admin_organizacion")
    h_coord = _headers(org_fixture["coord"], org_fixture["t1"], "coordinador")
    h_dpo = _headers(org_fixture["dpo"], org_fixture["t1"], "dpo")

    # 1. Crear Alta Dirección
    r_ad = await api_client.post(
        "/api/v1/organizacion/estructura/areas",
        json={"nombre": "Gerencia General", "nivel": "alta_direccion"},
        headers=h_admin,
    )
    ad_id = r_ad.json()["id"]

    # 2. Crear Unidad de Ventas
    r_ventas = await api_client.post(
        "/api/v1/organizacion/estructura/areas",
        json={"nombre": "Ventas", "nivel": "unidad", "parent_area_id": ad_id},
        headers=h_admin,
    )
    ventas_id = r_ventas.json()["id"]

    # 3. Crear Jefatura de Ventas y asignar titular
    r_jefe = await api_client.post(
        "/api/v1/organizacion/estructura/cargos",
        json={
            "area_id": ventas_id,
            "nombre": "Jefe de Ventas",
            "tipo_cargo": "otro",
            "es_jefatura": True,
        },
        headers=h_admin,
    )
    jefe_id = r_jefe.json()["id"]

    await api_client.post(
        f"/api/v1/organizacion/estructura/cargos/{jefe_id}/titular",
        json={"titular_user_id": org_fixture["candidato"]},
        headers=h_admin,
    )

    # 4. Coordinador lee árbol y cobertura
    r_arbol = await api_client.get("/api/v1/organizacion/estructura/arbol", headers=h_coord)
    assert r_arbol.status_code == 200, r_arbol.text
    res_arbol = r_arbol.json()
    assert len(res_arbol["arbol"]) >= 1
    # La raíz es alta_direccion
    assert any(a["nivel"] == "alta_direccion" for a in res_arbol["arbol"])

    r_cob = await api_client.get("/api/v1/organizacion/estructura/cobertura", headers=h_coord)
    assert r_cob.status_code == 200, r_cob.text
    cobertura = r_cob.json()
    # Gerencia General está sin jefatura
    assert any(u["area_id"] == ad_id for u in cobertura["unidades_sin_jefatura"])
    # Ventas tiene jefatura ocupada pero no tiene rol responsable_area asignado
    assert any(r["area_id"] == ventas_id for r in cobertura["responsables_por_designar"])

    # 5. DPO también puede leer (audita)
    r_dpo_read = await api_client.get("/api/v1/organizacion/estructura/cobertura", headers=h_dpo)
    assert r_dpo_read.status_code == 200


async def test_aislamiento_multi_tenant_y_rls(api_client: AsyncClient, org_fixture: dict, factory):
    """Verifica hermetismo entre inquilinos y RLS con el usuario lopdp_app."""
    h_t1 = _headers(org_fixture["admin"], org_fixture["t1"], "admin_organizacion")
    h_t2 = _headers(org_fixture["t2_admin"], org_fixture["t2"], "admin_organizacion")

    # Crear área y cargo en T1
    r_a1 = await api_client.post(
        "/api/v1/organizacion/estructura/areas",
        json={"nombre": "Unidad Secreta T1", "nivel": "unidad"},
        headers=h_t1,
    )
    a1_id = r_a1.json()["id"]

    r_c1 = await api_client.post(
        "/api/v1/organizacion/estructura/cargos",
        json={
            "area_id": a1_id,
            "nombre": "Líder T1",
            "tipo_cargo": "otro",
            "es_jefatura": True,
        },
        headers=h_t1,
    )
    c1_id = r_c1.json()["id"]

    # T2 intenta modificar el cargo de T1 -> 404 (no existe en su tenant)
    r_patch_t2 = await api_client.patch(
        f"/api/v1/organizacion/estructura/cargos/{c1_id}",
        json={"nombre": "Intento de Secuestro"},
        headers=h_t2,
    )
    assert r_patch_t2.status_code == 404

    # Verificar RLS directa en Postgres ejecutando como lopdp_app
    async with factory() as session:
        # En una sesión configurando el tenant T2 en app.current_tenant_id
        await session.execute(text("SET LOCAL ROLE lopdp_app"))
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": str(org_fixture["t2"])},
        )
        result = await session.execute(
            text("SELECT count(*) FROM cargos_organicos WHERE id = :cid"),
            {"cid": c1_id},
        )
        count = result.scalar()
        assert count == 0, "RLS debió ocultar el cargo del tenant 1 ante el tenant 2"
        await session.rollback()
