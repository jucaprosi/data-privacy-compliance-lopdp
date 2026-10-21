import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from main import app
from app_core.db.session import get_tenant_session, async_session_factory, fijar_contexto_rls
from app_core.security import get_current_tenant
from fastapi import Depends

@pytest.mark.anyio
async def test_flujo_completo_rls_arco():
    """Valida que el flujo HTTP use el contrato persistente y el aislamiento RLS."""
    # Para evaluar RLS en tests contra Neon (donde TEST_DATABASE_URL se conecta con
    # el rol dueño lopdp_beta_owner que posee BYPASSRLS), la sesión asume el rol
    # restringido de la aplicación 'lopdp_app' (sin BYPASSRLS) vía SET LOCAL ROLE,
    # replicando exactamente el comportamiento en producción (Aportes 87 y 89).
    async def override_get_tenant_session(tenant_id: str = Depends(get_current_tenant)):
        async with async_session_factory() as session:
            has_role = (await session.execute(text("SELECT 1 FROM pg_roles WHERE rolname = 'lopdp_app'"))).first()
            if has_role:
                await session.execute(text("SET LOCAL ROLE lopdp_app"))
            await fijar_contexto_rls(session, tenant_id)
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_tenant_session] = override_get_tenant_session
    try:
        # Usar ASGITransport para httpx asíncrono sobre FastAPI
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. POST usando un tenant
            headers_tenant_1 = {"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"}
            payload = {
                "tenant_id": "00000000-0000-0000-0000-000000000099",
                "tipo_solicitud": "ACCESO",
                "cedula_solicitante": "1712345678",
                "nombre_solicitante": "Titular de prueba",
            }
            resp_post = await client.post("/api/v1/arco/solicitudes", json=payload, headers=headers_tenant_1)
            assert resp_post.status_code == 200
            assert resp_post.json()["tenant_id"] == headers_tenant_1["X-Tenant-ID"]
            
            # 2. GET con el mismo tenant para verificar existencia
            resp_get_1 = await client.get("/api/v1/arco/solicitudes", headers=headers_tenant_1)
            assert resp_get_1.status_code == 200
            assert len(resp_get_1.json()) >= 1
            
            # 3. GET con Tenant distinto probando RLS
            headers_tenant_999 = {"X-Tenant-ID": "00000000-0000-0000-0000-000000000999"}
            resp_get_999 = await client.get("/api/v1/arco/solicitudes", headers=headers_tenant_999)
            assert resp_get_999.status_code == 200
            # Assert riguroso == 0 (RLS Isolation)
            assert len(resp_get_999.json()) == 0
    finally:
        app.dependency_overrides.pop(get_tenant_session, None)
