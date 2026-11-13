import pytest
from fastapi.testclient import TestClient
from main import app
from app_core.db.session import get_tenant_session
from features.ai_copilot.services import assistant_provider

client = TestClient(app)


@pytest.fixture(autouse=True)
def proveedores_en_modo_local(monkeypatch):
    """Aísla la suite de la compuerta: el asistente responde con el respaldo local."""
    from types import SimpleNamespace

    async def prohibido(*args, **kwargs):
        raise AssertionError("La suite del copiloto no debe llamar a la compuerta de inferencia")

    monkeypatch.setattr(assistant_provider, "pasillo_inferencia", SimpleNamespace(
        estado=lambda: SimpleNamespace(disponible=False), generar_estructurado=prohibido,
    ))

class MockSession:
    async def commit(self): pass
    def add(self, *args, **kwargs): pass
    async def execute(self, *args, **kwargs):
        class MockResult:
            def scalars(self):
                class MockScalars:
                    def all(self): return []
                return MockScalars()
        return MockResult()

async def override_get_db():
    yield MockSession()

app.dependency_overrides[get_tenant_session] = override_get_db

@pytest.fixture
def compuerta_falsa(monkeypatch):
    """Doble de la compuerta de inferencia para el diagnóstico: sin red, sin Vertex, sin clave."""
    from types import SimpleNamespace
    from app_core.pasillo import inferencia as pasillo_inferencia

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    traza = SimpleNamespace(prompt_id="ai_copilot.plan_mitigacion", prompt_version=1)

    async def generar_trazado(prompt, valores, esquema, *, modelo, org_id, corpus_sha256=None):
        brechas = ["Falta cláusula en NDA", "Política de retención vencida"]
        plan = esquema.model_validate({
            "analisis_general": "Plan de mitigación de prueba.",
            "tareas_propuestas": [{"descripcion": b, "impacto_riesgo": "ALTO"} for b in brechas],
        })
        return plan, traza

    async def registrar_traza(session, traza, entidad, entidad_id):
        return None

    monkeypatch.setattr(pasillo_inferencia, "generar_trazado", generar_trazado)
    monkeypatch.setattr(pasillo_inferencia, "registrar_traza", registrar_traza)


def test_ai_copilot_diagnosticar_mock(compuerta_falsa):
    headers = {"X-Tenant-ID": "tenant-corp-test"}
    payload = {
        "id_diagnostico": "DIAG-12345",
        "normativa": "LOPDP",
        "brechas_identificadas": ["Falta cláusula en NDA", "Política de retención vencida"],
        "scoring_global": 2.5
    }
    
    response = client.post("/api/v1/ai/diagnosticar", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert "analisis_general" in data
    assert len(data["tareas_propuestas"]) == 2
    assert data["tareas_propuestas"][0]["impacto_riesgo"] == "ALTO"

def test_ai_copilot_listar_mitigaciones():
    headers = {"X-Tenant-ID": "tenant-corp-test"}
    response = client.get("/api/v1/ai/mitigaciones", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_asistente_resuelve_brecha_con_articulo_y_plan():
    payload = {
        "pregunta": "¿Cómo implemento esta brecha y qué evidencia preparo?",
        "brechas": [{
            "pregunta_id": 21,
            "control": "Gestión del consentimiento",
            "dimension_id": "D03",
            "severidad": "Alto",
        }],
        "historial": [],
        "brecha_id": 21,
        "estado": "Implementación",
    }
    response = client.post(
        "/api/v1/ai_copilot/consulta", json=payload,
        headers={"X-Tenant-ID": "tenant-corp-test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["modo"] == "local"
    assert data["dlp_aplicado"] is True
    assert data["planes"][0]["pasos"]
    assert any("Art. 8" in f["articulo"] for f in data["planes"][0]["fundamento"])
    assert "DPD" not in data["planes"][0]["responsable_sugerido"]


def test_asistente_acepta_estado_de_seguimiento_y_rechaza_otro_valor():
    payload = {
        "pregunta": "¿Qué debo revisar después de implementar el consentimiento?",
        "brechas": [{
            "pregunta_id": 21, "control": "Gestión del consentimiento",
            "dimension_id": "D03", "severidad": "Alto",
        }],
        "historial": [], "brecha_id": 21, "estado": "Seguimiento",
    }
    response = client.post(
        "/api/v1/ai_copilot/consulta", json=payload,
        headers={"X-Tenant-ID": "tenant-corp-test"},
    )
    assert response.status_code == 200
    assert "Seguimiento" in response.json()["respuesta"]

    payload["estado"] = "Cerrado"
    invalida = client.post(
        "/api/v1/ai_copilot/consulta", json=payload,
        headers={"X-Tenant-ID": "tenant-corp-test"},
    )
    assert invalida.status_code == 422


def test_asistente_consulta_general_y_dlp_preinferencia():
    response = client.post(
        "/api/v1/ai_copilot/consulta",
        json={
            "pregunta": "¿Qué requisitos tiene el consentimiento? Contacto 099 123 4567",
            "brechas": [], "historial": [],
        },
        headers={"X-Tenant-ID": "tenant-corp-test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "099 123 4567" not in data["pregunta"]
    assert any("Art. 8" in f["articulo"] for f in data["fundamentos"])


def test_estado_declara_coherencia_del_proveedor_activo():
    response = client.get(
        "/api/v1/ai_copilot/estado", headers={"X-Tenant-ID": "tenant-corp-test"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["inferencia_externa_habilitada"], bool)
    assert data["modo"] == ("externo" if data["inferencia_externa_habilitada"] else "local")
