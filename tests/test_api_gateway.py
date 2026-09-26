"""Suite de Pruebas de Integración para la Pasarela REST API Gateway.
Verifica que los endpoints HTTP expongan adecuadamente las 7 salas ADPA manteniendo aislamiento y contratos.
"""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_api_health_check():
    """Valida los endpoints de estado operativo del sistema."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"
    assert len(data["salas_adpa"]) == 8

def test_diagnostico_endpoints():
    """Valida la consulta de preguntas podadas y cálculo de scoring vía REST."""
    headers = {"X-Tenant-ID": "tenant-corp-test"}
    
    # 1. Obtener preguntas
    ficha_payload = {
        "sector": "Banca y Finanzas",
        "tamano": "Corporativo",
        "emplea_nube": True,
        "trata_datos_salud": False,
        "emplea_ia": True,
        "videovigilancia": True,
        "transferencias_internacionales": False,
    }
    resp_preguntas = client.post("/api/v1/diagnostico/preguntas", json=ficha_payload, headers=headers)
    assert resp_preguntas.status_code == 200
    p_data = resp_preguntas.json()
    assert p_data["tenant_id"] == "tenant-corp-test"
    assert p_data["total_preguntas"] == 49 # Exactamente 48 núcleo + 1 condicional IA activada
    assert len(p_data["preguntas"]) == 49

    
    # 2. Evaluar scoring
    eval_payload = {
        "respuestas": [
            {
                "id_pregunta": "G01-P01",
                "respuesta_afirmativa": True,
                "nivel_evidencia": "E3_PROBADA",
                "rationale": "Política aprobada por directorio",
            },
            {
                "id_pregunta": "G01-P02",
                "respuesta_afirmativa": False,
                "nivel_evidencia": "E0_SIN_EVIDENCIA",
                "rationale": "Sin comité de privacidad formal",
            }
        ]
    }
    resp_eval = client.post("/api/v1/diagnostico/evaluar", json=eval_payload, headers=headers)
    assert resp_eval.status_code == 200
    scoring = resp_eval.json()["scoring"]
    assert scoring["porcentaje_conformidad_juridica"] == 50.0
    assert scoring["brechas_criticas_abiertas"] == 1
    
    # 3. Generar informes
    report_payload = {
        "ficha": ficha_payload,
        "respuestas": eval_payload["respuestas"],
    }
    resp_md = client.post("/api/v1/diagnostico/informe/markdown", json=report_payload, headers=headers)
    assert resp_md.status_code == 200
    assert "Informe Ejecutivo de Diagnóstico" in resp_md.json()["informe_markdown"]
    
    resp_html = client.post("/api/v1/diagnostico/informe/html", json=report_payload, headers=headers)
    assert resp_html.status_code == 200
    assert "<!DOCTYPE html>" in resp_html.json()["informe_html"]

def test_rat_endpoints():
    """Valida la creación y consulta de actividades de tratamiento en el RAT."""
    headers = {"X-Tenant-ID": "tenant-rat-01"}
    
    payload = {
        "codigo": "RAT-NOMINA-001",
        "nombre": "Gestión de Nómina y Remuneraciones",
        "area_responsable": "Talento Humano",
        "finalidad": "Pago de remuneraciones y obligaciones IESS",
        "base_legal": "CUMPLIMIENTO_CONTRATO",
        "categorias_titulares": ["EMPLEADOS"],
        "datos_sensibles": False,
        "volumen_titulares_estimado": 250,
        "transferencia_internacional": False,
        "requiere_eipd": False,
        "es_gran_escala": False,
    }
    resp_crear = client.post("/api/v1/rat/actividades", json=payload, headers=headers)
    assert resp_crear.status_code == 200
    act_data = resp_crear.json()["actividad"]
    assert act_data["codigo"] == "RAT-NOMINA-001"
    
    resp_listar = client.get("/api/v1/rat/actividades", headers=headers)
    assert resp_listar.status_code == 200
    assert resp_listar.json()["total"] >= 1

def test_mtge_endpoint():
    """Valida el cálculo de umbral MTGE para tratamiento a gran escala."""
    payload = {
        "actividad_rat_id": "act-test-01",
        "numero_titulares": 60000,
        "volumen_datos_por_titular": 15,
        "trata_datos_sensibles": True,
        "frecuencia_permanente": True,
        "alcance": "NACIONAL",
        "es_caso_directo_salud_masiva": False,
        "es_caso_directo_perfilamiento_ia": False,
    }
    resp = client.post("/api/v1/riesgos/mtge/evaluar", json=payload)
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["es_gran_escala"] is True
    assert res_data["detona_dpo_obligatorio"] is True

def test_dpo_cockpit_endpoints():
    """Valida la emisión de dictámenes y bitácora del DPO."""
    headers = {"X-Tenant-ID": "tenant-dpo-01"}
    payload = {
        "dpo_id": "dpo-cert-01",
        "tipo": "OPINION_CONSULTIVA",
        "asunto": "Evaluación de nuevo proveedor cloud",
        "referencia_normativa": "Art. 50 LOPDP",
        "cuerpo": "Se recomienda incluir cláusulas tipo de protección de datos en el contrato.",
    }
    resp_emitir = client.post("/api/v1/dpo/dictamenes", json=payload, headers=headers)
    assert resp_emitir.status_code == 200
    dictamen_id = resp_emitir.json()["dictamen"]["id"]
    
    resp_bitacora = client.get("/api/v1/dpo/bitacora", headers=headers)
    assert resp_bitacora.status_code == 200
    assert resp_bitacora.json()["total"] >= 1
    
    resp_acuse = client.post(f"/api/v1/dpo/dictamenes/{dictamen_id}/acuse")
    assert resp_acuse.status_code == 200
    assert resp_acuse.json()["dictamen"]["acuse_recibo_alta_direccion"] is True

def test_auditoria_capa_endpoints():
    """Valida el registro de hallazgos y verificación independiente."""
    headers = {"X-Tenant-ID": "tenant-capa-01"}
    payload = {
        "control_id": "G08-P01",
        "severidad": "NO_CONFORMIDAD_MENOR",
        "descripcion_hallazgo": "Copias de respaldo sin cifrado en reposo",
        "causa_raiz": "Falta de política técnica formal",
        "accion_correctiva": "Habilitar cifrado AES-256 en buckets de respaldo",
        "responsable_implementacion_id": "dev-ops-01",
    }
    resp_crear = client.post("/api/v1/capa/tickets", json=payload, headers=headers)
    assert resp_crear.status_code == 200
    ticket_id = resp_crear.json()["ticket"]["id"]
    
    # Intento de auto-cierre debe fallar con 403 (SoD)
    auto_cierre = {
        "auditor_id": "dev-ops-01", # El mismo responsable
        "evidencia_id": "evd-01",
    }
    resp_fallo = client.post(f"/api/v1/capa/tickets/{ticket_id}/cerrar", json=auto_cierre)
    assert resp_fallo.status_code == 403
    
    # Cierre por auditor independiente debe tener éxito
    cierre_ok = {
        "auditor_id": "auditor-independiente-01",
        "evidencia_id": "evd-01",
    }
    resp_ok = client.post(f"/api/v1/capa/tickets/{ticket_id}/cerrar", json=cierre_ok)
    assert resp_ok.status_code == 200
    assert resp_ok.json()["ticket"]["estado"] == "CERRADO_VERIFICADO"

def test_evidencias_endpoints():
    """Valida el registro de evidencia con cómputo de hash SHA-256."""
    headers = {"X-Tenant-ID": "tenant-evd-01"}
    payload = {
        "codigo": "EVD-2026-001",
        "nombre_archivo": "politica_privacidad_v1.pdf",
        "storage_path": "/s3/docs/politica_v1.pdf",
        "calidad": "E3_PROBADA",
        "propietario_id": "dpo-01",
        "contenido_texto_o_hash": "Texto legal verificado para hash criptográfico",
    }
    resp_reg = client.post("/api/v1/evidencias", json=payload, headers=headers)
    assert resp_reg.status_code == 200
    evd = resp_reg.json()["evidencia"]
    assert len(evd["sha256_hash"]) == 64
    assert evd["sha256_hash"] == "bcf5b4a1df9107c439079d8ab6a97d481ef1c9d41922afa97587db647978aa68"
    
    resp_list = client.get("/api/v1/evidencias", headers=headers)
    assert resp_list.status_code == 200
    assert resp_list.json()["total"] >= 1

def test_rag_endpoint():
    """Valida la consulta al copiloto RAG con citas jurídicas verificadas y manejo de incertidumbre."""
    headers = {"X-Tenant-ID": "tenant-rag-01"}
    
    # 1. Caso afirmativo con cita normativa oficial
    payload_ok = {
        "pregunta": "¿Cuándo es obligatorio nombrar un Delegado de Protección de Datos DPD según la ley ecuatoriana?"
    }
    resp_ok = client.post("/api/v1/rag/consulta", json=payload_ok, headers=headers)
    assert resp_ok.status_code == 200
    data_ok = resp_ok.json()
    assert data_ok["fuente_oficial_verificada"] is True
    assert len(data_ok["citas_normativas"]) > 0
    assert "Artículo 48" in data_ok["citas_normativas"][0]

    # 2. Caso fuera de corpus: Incertidumbre legal garantizada sin alucinación
    payload_fuera = {
        "pregunta": "¿Cuál es la regulación de pesca deportiva en altamar?"
    }
    resp_fuera = client.post("/api/v1/rag/consulta", json=payload_fuera, headers=headers)
    assert resp_fuera.status_code == 200
    data_fuera = resp_fuera.json()
    assert data_fuera["fuente_oficial_verificada"] is False
    assert len(data_fuera["citas_normativas"]) == 0
    assert "No puedo responder esto basándome en la normativa indexada." in data_fuera["respuesta"]

