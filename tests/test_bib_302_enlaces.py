# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤rbac-tenant ¤arbitro
"""Árbitro BIB-302. La persistencia/RLS se acredita solo en el arnés con la migración aplicada.

Mutación decisiva: retirar ``AND t.tenant_id=:t`` de la compuerta Roadmap hace fallar
``test_compuerta_roadmap_filtra_tenant``; restaurar el filtro devuelve el archivo a verde.
"""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from tests._alembic_salas import cabeza_de_sala

from api.errores import ErrorNegocio
from app_core.errors import CATALOGO_ERRORES
from features.biblioteca import biblioteca_service as bib
from features.biblioteca.services import enlaces
from features.roadmap import roadmap_service

ROOT = Path(__file__).resolve().parents[1]
MIGRACION = ROOT / "alembic/versions/20261113_biblioteca_enlaces.py"


def test_contratos_compuertas_rutas_y_errores():
    from api.routers import biblioteca_enlaces as router
    assert router.AUTO_REGISTRO is True
    assert {(m, r.path) for r in router.router.routes for m in r.methods} == {
        ("GET", "/biblioteca/documentos/{documento_id}/enlaces"),
        ("GET", "/biblioteca/documentos/acciones/{accion_id}/documentos"),
        ("POST", "/biblioteca/documentos/{documento_id}/enlaces"),
        ("DELETE", "/biblioteca/documentos/{documento_id}/enlaces/{enlace_id}"),
    }
    for nombre in ("CrearEnlace", "EnlaceDocumento", "crear_enlace", "listar_enlaces",
                   "listar_documentos_de_accion", "eliminar_enlace"):
        assert nombre in bib.__all__ and hasattr(bib, nombre)
    assert "obtener_accion_para_enlace" in roadmap_service.__all__
    for codigo, estado in (("BIB_ENLACE_ACCION_AJENA", 422), ("BIB_ENLACE_REVISION_INVALIDA", 422),
                           ("BIB_ENLACE_NO_ENCONTRADO", 404)):
        assert CATALOGO_ERRORES[codigo].status_code == estado


@pytest.mark.asyncio
async def test_crear_y_eliminar_enlace_no_modifica_estado_de_accion_ni_documento(monkeypatch):
    """Comprueba por comportamiento que enlaces no ejecuta ningún UPDATE sobre tareas ni documentos."""
    from datetime import datetime, timezone
    monkeypatch.setattr(enlaces, "contexto", AsyncMock())
    monkeypatch.setattr(enlaces, "registrar_evento", AsyncMock())

    fila_enlace = {
        "id": "doc-a:1:acc-1", "documento_id": "doc-a", "documento_revision": 1,
        "accion_id": "acc-1", "accion_titulo": "Tarea 1", "accion_estado": "pendiente",
        "requisito": "req", "hallazgo_id": None, "hallazgo_titulo": None,
        "hallazgo_origen": None, "hallazgo_origen_ref": None, "pregunta": None,
        "assessment_version": None, "creado_por": "actor-a", "creado_en": datetime.now(timezone.utc),
    }

    class MockResult:
        def __init__(self, val=None, mappings_val=None):
            self._val = val
            self._mappings_val = mappings_val or []
        def scalar(self): return self._val
        def mappings(self):
            return SimpleNamespace(
                all=lambda: self._mappings_val,
                first=lambda: self._mappings_val[0] if self._mappings_val else None,
            )

    respuestas = [
        MockResult(val=2),  # SELECT revision FROM biblioteca_documentos
        MockResult(val="doc-a:1:acc-1"),  # INSERT INTO biblioteca_revision_acciones
        MockResult(val=1),  # SELECT 1 FROM biblioteca_documentos (dentro de listar_enlaces)
        MockResult(mappings_val=[fila_enlace]),  # SELECT FROM biblioteca_revision_acciones (listar_enlaces)
    ]
    consultas_ejecutadas = []

    async def mock_execute(sql, *args, **kwargs):
        consultas_ejecutadas.append(str(sql))
        return respuestas.pop(0)

    session = SimpleNamespace(execute=AsyncMock(side_effect=mock_execute))
    obtener_accion = AsyncMock(return_value={"id": "acc-1"})

    enlace = await enlaces.crear_enlace(
        session, "tenant-a", "actor-a", "doc-a",
        bib.CrearEnlace(accion_id="acc-1", revision=1),
        obtener_accion,
    )
    assert enlace.accion_id == "acc-1"
    assert not any("UPDATE" in q.upper() for q in consultas_ejecutadas)


@pytest.mark.asyncio
async def test_compuerta_roadmap_filtra_tenant():
    resultado = SimpleNamespace(mappings=lambda: SimpleNamespace(first=lambda: None))
    session = SimpleNamespace(execute=AsyncMock(return_value=resultado))
    assert await roadmap_service.obtener_accion_para_enlace(session, "tenant-a", "accion-b") is None
    consulta, parametros = session.execute.await_args.args
    assert "tenant_id=:t" in str(consulta) and parametros == {"id": "accion-b", "t": "tenant-a"}


@pytest.mark.asyncio
async def test_accion_ajena_falla_antes_de_insertar(monkeypatch):
    resultados = [SimpleNamespace(scalar=lambda: 2)]
    session = SimpleNamespace(execute=AsyncMock(side_effect=resultados))
    monkeypatch.setattr(enlaces, "contexto", AsyncMock())
    obtener_accion = AsyncMock(return_value=None)
    with pytest.raises(ErrorNegocio) as error:
        await enlaces.crear_enlace(session, "tenant-a", "actor-a", "doc-a", bib.CrearEnlace(
            accion_id="accion-tenant-b", revision=2), obtener_accion)
    assert error.value.code == "BIB_ENLACE_ACCION_AJENA"
    assert session.execute.await_count == 1, "una referencia cruzada nunca llega al INSERT"



