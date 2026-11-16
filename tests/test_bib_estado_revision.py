# ¤rbac-tenant
"""El estado del documento solo cambia por funciones acotadas (SECURITY DEFINER): lopdp_app no tiene UPDATE (estado)."""
from __future__ import annotations

from datetime import datetime, timezone
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from features.biblioteca.domain.revisiones import EnviarRevision
from features.biblioteca.services import revision_aprobacion


@pytest.mark.asyncio
async def test_cambio_estado_invoca_funciones_sql_dedicadas(monkeypatch):
    """Verifica por comportamiento que el servicio invoca las funciones de BD y no ejecuta UPDATE directo."""
    monkeypatch.setattr(revision_aprobacion, "contexto", AsyncMock())

    consultas: list[str] = []

    class MockResult:
        def __init__(self, val=None, mappings_val=None):
            self._val = val
            self._mappings_val = mappings_val or []

        def scalar(self):
            return self._val

        def mappings(self):
            return SimpleNamespace(
                first=lambda: self._mappings_val[0] if self._mappings_val else None,
                all=lambda: self._mappings_val,
            )

    fila_doc = {"revision": 1, "sha256": "h" * 64, "contenido_markdown": "Sin faltantes", "creado_por": "u-creador"}
    fila_rev = {
        "id": "rev-1", "documento_id": "doc-1", "revision": 1, "sha256": "h" * 64,
        "revisor_id": "u-revisor", "tipo_participacion": "revision", "estado": "asignada",
        "observaciones": None, "asignado_por": "u-creador", "asignado_en": datetime.now(timezone.utc),
        "decidido_por": None, "decidido_en": None, "criterio_aprobacion": None, "autoridad_id": None,
    }

    respuestas = [
        MockResult(mappings_val=[fila_doc]),
        MockResult(),
        MockResult(val=1),
        MockResult(mappings_val=[fila_rev]),
    ]

    async def mock_execute(sql, *args, **kwargs):
        consultas.append(str(sql))
        return respuestas.pop(0)

    session = SimpleNamespace(execute=AsyncMock(side_effect=mock_execute))
    await revision_aprobacion.enviar_a_revision(
        session, "tenant-1", "u-creador", "doc-1",
        EnviarRevision(revisor_id="u-revisor", tipo_participacion="revision"),
    )

    assert any("biblioteca_enviar_documento_a_revision" in q for q in consultas)
    assert not any("UPDATE biblioteca_documentos SET estado" in q for q in consultas)


@pytest.mark.asyncio
async def test_db_lopdp_app_no_puede_hacer_update_directo_de_estado():
    """Verifica en base real que el rol de aplicación carece de permiso para UPDATE en columna estado."""
    from conftest import exigir_base_de_pruebas

    url = os.environ.get("TEST_DATABASE_URL", "")
    if not url:
        pytest.skip("Sin TEST_DATABASE_URL para verificar permisos de rol en base")
    exigir_base_de_pruebas()
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_async_engine(url, echo=False)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            privilegios = (await conexion.execute(text(
                "SELECT column_name, privilege_type FROM information_schema.column_privileges "
                "WHERE grantee='lopdp_app' AND table_name='biblioteca_documentos' AND privilege_type='UPDATE'"
            ))).mappings().all()
            columnas_update = {f["column_name"] for f in privilegios}
            assert "estado" not in columnas_update
        finally:
            await transaccion.rollback()
    await engine.dispose()
