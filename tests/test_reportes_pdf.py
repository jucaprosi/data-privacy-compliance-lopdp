from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)

def test_exportar_pdf_diagnostico_content_type():
    """Verifica que el export de PDF devuelve Content-Type: application/pdf y 200 OK."""
    # Tenant válido según nuestro mock local (security.py requiere Bearer jwt_mock_tenant_...)
    headers = {
        "Authorization": "Bearer jwt_mock_tenant_00000000-0000-0000-0000-000000000001"
    }
    
    # Hacer GET al endpoint creado
    # El id_diagnostico puede ser cualquier string en este momento ya que es mock
    diagnostico_id = "diag-test-123"
    response = client.get(f"/api/v1/diagnostico/{diagnostico_id}/exportar", headers=headers)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    
    # Verificar que devuelva algo de contenido
    assert len(response.content) > 0
    
    # Validar firma PDF básica (%PDF-)
    assert response.content.startswith(b"%PDF-")
