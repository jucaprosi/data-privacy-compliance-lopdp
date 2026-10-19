import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.anyio
async def test_flujo_completo_rls_arco():
    """Valida que el flujo HTTP use el contrato persistente y no el mock antiguo."""
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
