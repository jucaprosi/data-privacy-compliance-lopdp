import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.anyio
async def test_flujo_completo_rls_arco():
    """Valida el flujo E2E y el Row-Level Security (RLS) en FastAPI."""
    # Usar ASGITransport para httpx asíncrono sobre FastAPI
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. POST usando un tenant
        headers_tenant_1 = {"Authorization": "Bearer jwt_mock_tenant_1"}
        payload = {
            "id": "req-1",
            "tenant_id": "jwt_mock_tenant_1",
            "titular_id": "titular-abc",
            "tipo_derecho": "ACCESO",
            "estado": "ABIERTO"
        }
        resp_post = await client.post("/api/v1/arco/solicitudes", json=payload, headers=headers_tenant_1)
        assert resp_post.status_code == 200
        
        # 2. GET con el mismo tenant para verificar existencia
        resp_get_1 = await client.get("/api/v1/arco/solicitudes", headers=headers_tenant_1)
        assert resp_get_1.status_code == 200
        assert len(resp_get_1.json()) >= 1
        
        # 3. GET con Tenant distinto probando RLS
        headers_tenant_999 = {"Authorization": "Bearer jwt_mock_tenant_999"}
        resp_get_999 = await client.get("/api/v1/arco/solicitudes", headers=headers_tenant_999)
        assert resp_get_999.status_code == 200
        # Assert riguroso == 0 (RLS Isolation)
        assert len(resp_get_999.json()) == 0
