# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤arbitro
import os
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

from api.errores import ErrorNegocio
from features.biblioteca.services import impacto
from features.notificaciones.notificaciones_service import construir_aviso_impacto

RAIZ = Path(__file__).parents[1]


def test_aviso_no_expone_contenido_sensible_ni_acredita_envio():
    aviso = construir_aviso_impacto("exp-1", "tenant-1", "https://app.example")
    assert aviso == {
        "tipo": "biblioteca_version_publicada", "tenant_id": "tenant-1", "expediente_id": "exp-1",
        "asunto": "Revisión documental pendiente",
        "mensaje": "Hay una nueva versión disponible. Registra la decisión de tu organización.",
        "enlace": "https://app.example/biblioteca?impacto=exp-1",
    }
    assert "enviado" not in str(aviso).lower()


@pytest.mark.asyncio
async def test_decision_invalida_falla_antes_de_persistir():
    session = AsyncMock()
    with pytest.raises(ErrorNegocio) as exc:
        await impacto.decidir(session, "tenant", "actor", "exp", "ignorar", "")
    assert exc.value.code == "BIB_IMPACTO_DECISION_INVALIDA"
    session.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_servicio_no_actualiza_documentos_al_decidir():
    from types import SimpleNamespace
    mock_res = SimpleNamespace(mappings=lambda: SimpleNamespace(first=lambda: {
        "id": "exp-1", "decision": "actualizar", "motivo": "ok",
    }))
    session = SimpleNamespace(execute=AsyncMock(return_value=mock_res))
    resultado = await impacto.decidir(session, "tenant-1", "actor-1", "exp-1", "actualizar", "motivo valido")
    assert resultado["decision"] == "actualizar"
    sentencias = [str(llamada.args[0]) for llamada in session.execute.call_args_list]
    assert all("biblioteca_documentos" not in s for s in sentencias)
    assert any("biblioteca_impactos_organizacion" in s for s in sentencias)


@pytest.mark.asyncio
async def test_db_disparador_preserva_documento_aprobado_inmutable():
    from conftest import exigir_base_de_pruebas
    url = os.environ.get("TEST_DATABASE_URL", "")
    if not url:
        pytest.skip("Sin TEST_DATABASE_URL para prueba de disparador")
    exigir_base_de_pruebas()
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_async_engine(url, echo=False)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            tid = f"org-imp-{uuid4().hex[:8]}"
            uid = f"usr-imp-{uuid4().hex[:8]}"
            did = f"doc-imp-{uuid4().hex[:8]}"
            await conexion.execute(text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:id, 'T', 'T', :ruc)"),
                                   {"id": tid, "ruc": str(uuid4().int)[:13]})
            await conexion.execute(text("INSERT INTO users (id, email, nombre) VALUES (:id, :e, 'U')"),
                                   {"id": uid, "e": f"{uid}@test.local"})
            import hashlib
            sha_original = hashlib.sha256("Original".encode("utf-8")).hexdigest()
            await conexion.execute(text(
                "INSERT INTO biblioteca_documentos "
                "(id, tenant_id, codigo, nombre, origen, contenido_markdown, sha256, estado, creado_por, fecha_emision, proxima_revision, aprobado_por, aprobado_en) "
                "VALUES (:id, :tid, 'DOC-001', 'Documento Aprobado', 'propio', 'Original', :sha, 'aprobado', :uid, CURRENT_DATE, CURRENT_DATE + 365, :uid, now())"
            ), {"id": did, "tid": tid, "uid": uid, "sha": sha_original})
            sha_modificado = hashlib.sha256("Modificado".encode("utf-8")).hexdigest()
            with pytest.raises(DBAPIError) as exc:
                await conexion.execute(text(
                    "UPDATE biblioteca_documentos SET contenido_markdown = 'Modificado', sha256 = :sha WHERE id = :id"
                ), {"id": did, "sha": sha_modificado})
            assert "BIB_DOCUMENTO_APROBADO_INMUTABLE" in str(exc.value)
        finally:
            await transaccion.rollback()
    await engine.dispose()
