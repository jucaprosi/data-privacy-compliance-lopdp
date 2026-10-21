from fastapi.testclient import TestClient
from main import app
from app_core.db.session import get_tenant_session
import pytest

client = TestClient(app)

# Mock de sesión de base de datos
async def mock_get_tenant_session():
    class MockResult:
        def scalars(self):
            class MockScalars:
                def all(self):
                    return []
            return MockScalars()
            
    class MockSession:
        async def execute(self, *args, **kwargs):
            return MockResult()
            
        async def commit(self):
            pass

        async def flush(self):
            pass
            
        async def refresh(self, *args):
            pass
            
        def add(self, *args, **kwargs):
            pass
            
    yield MockSession()

# Aplicar el mock a FastAPI
app.dependency_overrides[get_tenant_session] = mock_get_tenant_session

def test_get_arco_solicitudes_auth_valid():
    """Verificar que el endpoint GET responde 200 OK con X-Tenant-ID header."""
    headers = {
        "X-Tenant-ID": "00000000-0000-0000-0000-000000000001"
    }
    response = client.get("/api/v1/arco/solicitudes", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
