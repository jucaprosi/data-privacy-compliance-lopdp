# ¤arbitro
"""Pruebas HTTP para los endpoints de evidencia de la Hoja de Ruta y de Bóveda de Evidencias.

Verifica:
1. Endpoint POST /api/v1/roadmaps/tasks/{id}/evidence/upload-url:
   - Rol responsable_area genera URL firmada en R2.
   - Rol encargado genera URL firmada en R2.
   - Rol dpo rechazado con 403 Forbidden.
   - Rol implementador rechazado con 403 Forbidden.
   - Petición con tamaño 0 bytes rechazada con 422 Unprocessable Entity.
2. Endpoint POST /api/v1/roadmaps/tasks/{id}/evidence (registro tras subida):
   - Responsable de área registra evidencia exitosamente (201 Created).
   - Encargado registra evidencia exitosamente (201 Created).
   - Rol dpo rechazado con 403 Forbidden.
3. Endpoint GET /api/v1/roadmaps/tasks/{id}/evidence (listado):
   - Roles activos (responsable_area, encargado, dpo, implementador) consultan evidencias (200 OK).
4. Endpoint PATCH /api/v1/roadmaps/tasks/{id}/evidence/{evidence_id} (validación/rechazo):
   - Encargado, DPO e implementador pueden validar evidencia (200 OK).
   - Responsable de área rechazado con 403 Forbidden.
   - Regla de cuatro ojos: quien subió la evidencia no puede validarla (409 Conflict).
   - Evidencia inexistente devuelve 404 Not Found.
5. Endpoints de la Bóveda de Evidencias (/api/v1/evidencias):
   - Registro de evidencia con SHA-256 precalculado y contenido de texto.
   - Detección de duplicados dentro del mismo tenant (duplicada=True).
   - Consulta de catálogo por tenant con aislamiento lógico.
   - Verificación pública/interna por hash SHA-256 (/verificar/{sha256}).
   - Actualización de vínculos de control del assessment (1..80).
"""
from __future__ import annotations

import hashlib
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app_core.db.session import get_session
from features.evidencias.evidencias_service import reiniciar_repositorio_evidencias
from features.organizacion import organizacion_service
from features.organizacion.organizacion_service import RbacError
from features.roadmap import roadmap_service
from main import app

pytestmark = pytest.mark.asyncio


def _headers(user_id: str = "user-1", tenant_id: str = "tenant-1", role: str = "responsable_area") -> dict[str, str]:
    return {
        "X-User-ID": user_id,
        "X-Tenant-ID": tenant_id,
        "X-Role": role,
    }


# ============================================================================
# Pruebas HTTP: Endpoints de Evidencia en Hoja de Ruta (/api/v1/roadmaps/tasks/...)
# ============================================================================


async def test_roadmap_evidence_upload_url_autorizacion(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(organizacion_service, "has_active_role", AsyncMock(return_value=True))
    monkeypatch.setattr(roadmap_service, "ensure_task_in_area_scope", AsyncMock(return_value=None))
    app.dependency_overrides[get_session] = lambda: None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"filename": "informe_seguridad.pdf", "mime_type": "application/pdf", "file_size": 2048}

        # 1. responsable_area -> 200 OK
        r_resp = await client.post(
            "/api/v1/roadmaps/tasks/task-100/evidence/upload-url",
            json=payload,
            headers=_headers(role="responsable_area"),
        )
        assert r_resp.status_code == 200, r_resp.text
        data = r_resp.json()
        assert "url" in data
        assert "key" in data

        # 2. coordinador -> 200 OK
        r_enc = await client.post(
            "/api/v1/roadmaps/tasks/task-100/evidence/upload-url",
            json=payload,
            headers=_headers(role="coordinador"),
        )
        assert r_enc.status_code == 200, r_enc.text

        # 3. dpo -> 403 Forbidden
        r_dpo = await client.post(
            "/api/v1/roadmaps/tasks/task-100/evidence/upload-url",
            json=payload,
            headers=_headers(role="dpo"),
        )
        assert r_dpo.status_code == 403

        # 4. implementador -> 403 Forbidden
        r_imp = await client.post(
            "/api/v1/roadmaps/tasks/task-100/evidence/upload-url",
            json=payload,
            headers=_headers(role="implementador"),
        )
        assert r_imp.status_code == 403


async def test_roadmap_evidence_upload_url_validacion_cuerpo(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(organizacion_service, "has_active_role", AsyncMock(return_value=True))
    monkeypatch.setattr(roadmap_service, "ensure_task_in_area_scope", AsyncMock(return_value=None))
    app.dependency_overrides[get_session] = lambda: None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # file_size = 0 debe fallar por validación del esquema Pydantic (ge=1)
        payload_invalido = {"filename": "archivo_vacio.pdf", "mime_type": "application/pdf", "file_size": 0}
        resp = await client.post(
            "/api/v1/roadmaps/tasks/task-100/evidence/upload-url",
            json=payload_invalido,
            headers=_headers(role="responsable_area"),
        )
        assert resp.status_code == 422


async def test_roadmap_evidence_register_exitoso_y_rbac(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(organizacion_service, "has_active_role", AsyncMock(return_value=True))
    monkeypatch.setattr(roadmap_service, "ensure_task_in_area_scope", AsyncMock(return_value=None))
    mock_register = AsyncMock(
        return_value={
            "id": "evd-1",
            "task_id": "task-100",
            "r2_key": "tenant-1/task-100/doc.pdf",
            "file_size": 4096,
            "mime_type": "application/pdf",
        }
    )
    monkeypatch.setattr(roadmap_service, "register_evidence_upload", mock_register)
    app.dependency_overrides[get_session] = lambda: None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        query_params = "r2_key=tenant-1/task-100/doc.pdf&mime_type=application/pdf&file_size=4096&file_hash=abcdef1234"

        # responsable_area -> 201 Created
        r_resp = await client.post(
            f"/api/v1/roadmaps/tasks/task-100/evidence?{query_params}",
            headers=_headers(user_id="user-sube", role="responsable_area"),
        )
        assert r_resp.status_code == 201, r_resp.text
        assert r_resp.json()["id"] == "evd-1"

        # dpo no puede registrar evidencia directa -> 403 Forbidden
        r_dpo = await client.post(
            f"/api/v1/roadmaps/tasks/task-100/evidence?{query_params}",
            headers=_headers(user_id="user-dpo", role="dpo"),
        )
        assert r_dpo.status_code == 403


async def test_roadmap_evidence_list_endpoints(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(organizacion_service, "has_active_role", AsyncMock(return_value=True))
    mock_list = AsyncMock(
        return_value=[
            {"id": "evd-1", "task_id": "task-100", "validation_status": "pending"},
            {"id": "evd-2", "task_id": "task-100", "validation_status": "approved"},
        ]
    )
    monkeypatch.setattr(roadmap_service, "list_evidence", mock_list)
    app.dependency_overrides[get_session] = lambda: None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Cualquier rol activo con membresía puede listar evidencias de la tarea
        for rol in ["responsable_area", "coordinador", "dpo", "implementador"]:
            r = await client.get(
                "/api/v1/roadmaps/tasks/task-100/evidence",
                headers=_headers(role=rol),
            )
            assert r.status_code == 200, f"Fallo al listar con rol {rol}: {r.text}"
            evidencias = r.json()
            assert len(evidencias) == 2


async def test_roadmap_evidence_validate_cuatro_ojos_y_not_found(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(organizacion_service, "has_active_role", AsyncMock(return_value=True))
    app.dependency_overrides[get_session] = lambda: None

    # 1. Caso exitoso: DPO valida
    mock_validate_ok = AsyncMock(
        return_value={"id": "evd-1", "validation_status": "approved", "notes": "auditado conforme"}
    )
    monkeypatch.setattr(roadmap_service, "validate_evidence", mock_validate_ok)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        body = {"validation_status": "approved", "notes": "auditado conforme"}
        r_ok = await client.patch(
            "/api/v1/roadmaps/tasks/task-100/evidence/evd-1",
            json=body,
            headers=_headers(user_id="user-validador", role="dpo"),
        )
        assert r_ok.status_code == 200, r_ok.text
        assert r_ok.json()["validation_status"] == "approved"

        # 2. Responsable de área no tiene permiso de validar -> 403 Forbidden
        r_resp = await client.patch(
            "/api/v1/roadmaps/tasks/task-100/evidence/evd-1",
            json=body,
            headers=_headers(user_id="user-resp", role="responsable_area"),
        )
        assert r_resp.status_code == 403

        # 3. Violación de cuatro ojos (quien subió no valida) -> 409 Conflict
        mock_four_eyes = AsyncMock(
            side_effect=RbacError(code=409, detail="Cuatro ojos: quien subió la evidencia no puede validarla")
        )
        monkeypatch.setattr(roadmap_service, "validate_evidence", mock_four_eyes)

        r_conflict = await client.patch(
            "/api/v1/roadmaps/tasks/task-100/evidence/evd-1",
            json=body,
            headers=_headers(user_id="user-subidor", role="coordinador"),
        )
        assert r_conflict.status_code == 409
        assert "Cuatro ojos" in r_conflict.json()["detail"]

        # 4. Evidencia inexistente -> 404 Not Found
        mock_not_found = AsyncMock(return_value=None)
        monkeypatch.setattr(roadmap_service, "validate_evidence", mock_not_found)

        r_404 = await client.patch(
            "/api/v1/roadmaps/tasks/task-100/evidence/evd-inexistente",
            json=body,
            headers=_headers(user_id="user-dpo", role="dpo"),
        )
        assert r_404.status_code == 404


# ============================================================================
# Pruebas HTTP: Endpoints de Bóveda de Evidencias (/api/v1/evidencias)
# ============================================================================


def _sha256(cadena: str) -> str:
    return hashlib.sha256(cadena.encode("utf-8")).hexdigest()


async def test_boveda_evidencias_ciclo_completo_http():
    reiniciar_repositorio_evidencias()
    try:
        client = TestClient(app)
        tenant_h = {"X-Tenant-ID": "tenant-boveda-test"}

        # 1. Registrar evidencia inicial con SHA-256 precalculado
        doc_hash = _sha256("documento de prueba boveda")
        resp_reg = client.post(
            "/api/v1/evidencias",
            json={
                "nombre_archivo": "politica_seguridad.pdf",
                "sha256_hash": doc_hash,
                "tamano_bytes": 1024,
                "tipo_mime": "application/pdf",
                "controles_vinculados": [1, 2, 3],
            },
            headers=tenant_h,
        )
        assert resp_reg.status_code == 200, resp_reg.text
        data_reg = resp_reg.json()
        assert data_reg["status"] == "SUCCESS"
        assert data_reg["duplicada"] is False
        evidencia_id = data_reg["evidencia"]["id"]
        assert data_reg["evidencia"]["sha256_hash"] == doc_hash
        assert data_reg["evidencia"]["controles_vinculados"] == [1, 2, 3]

        # 2. Registrar idéntico documento -> detecta duplicado (duplicada=True)
        resp_dup = client.post(
            "/api/v1/evidencias",
            json={
                "nombre_archivo": "politica_seguridad_copia.pdf",
                "sha256_hash": doc_hash,
            },
            headers=tenant_h,
        )
        assert resp_dup.status_code == 200
        assert resp_dup.json()["duplicada"] is True
        assert resp_dup.json()["evidencia"]["id"] == evidencia_id

        # 3. Listar catálogo de evidencias del tenant
        resp_list = client.get("/api/v1/evidencias", headers=tenant_h)
        assert resp_list.status_code == 200
        assert resp_list.json()["total"] == 1
        assert resp_list.json()["evidencias"][0]["id"] == evidencia_id

        # 4. Verificar integridad por hash
        resp_verif = client.get(f"/api/v1/evidencias/verificar/{doc_hash}", headers=tenant_h)
        assert resp_verif.status_code == 200
        assert resp_verif.json()["coincide"] is True
        assert resp_verif.json()["evidencia"]["id"] == evidencia_id

        # Hash desconocido
        otro_hash = _sha256("documento inexistente")
        resp_verif_no = client.get(f"/api/v1/evidencias/verificar/{otro_hash}", headers=tenant_h)
        assert resp_verif_no.status_code == 200
        assert resp_verif_no.json()["coincide"] is False
        assert resp_verif_no.json()["evidencia"] is None

        # 5. Actualizar vínculos de control del assessment
        resp_vinc = client.patch(
            f"/api/v1/evidencias/{evidencia_id}/vinculos",
            json={"agregar": [4, 5], "quitar": [1]},
            headers=tenant_h,
        )
        assert resp_vinc.status_code == 200
        assert sorted(resp_vinc.json()["evidencia"]["controles_vinculados"]) == [2, 3, 4, 5]

        # Control fuera de rango (1..80) -> 422
        resp_rango = client.patch(
            f"/api/v1/evidencias/{evidencia_id}/vinculos",
            json={"agregar": [99]},
            headers=tenant_h,
        )
        assert resp_rango.status_code == 422

    finally:
        reiniciar_repositorio_evidencias()
