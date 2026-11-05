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


def test_migracion_n_m_rls_forzada_referencias_y_una_cabeza():
    spec = importlib.util.spec_from_file_location("bib302_migracion", MIGRACION)
    migracion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migracion)
    assert len(migracion.revision) <= 32
    cfg = Config(str(ROOT / "alembic.ini")); cfg.set_main_option("script_location", str(ROOT / "alembic"))
    guion = ScriptDirectory.from_config(cfg)
    assert len(guion.get_heads()) == 1 and guion.get_revision(migracion.revision) is not None
    assert guion.get_revision(migracion.down_revision) is not None
    sql = []
    migracion.op = SimpleNamespace(execute=sql.append)
    migracion.upgrade()
    texto = "\n".join(sql)
    assert "UNIQUE (tenant_id,documento_id,documento_revision,accion_id)" in texto
    assert "biblioteca_documentos_historial" in texto and "roadmap_tasks" in texto
    assert "NEW.tenant_id" in texto and "BIB_ENLACE_ACCION_AJENA" in texto
    assert "ENABLE ROW LEVEL SECURITY" in texto and "FORCE ROW LEVEL SECURITY" in texto
    assert "WITH CHECK (tenant_id::text=current_setting('app.current_tenant_id',true))" in texto
    assert "GRANT SELECT,INSERT,DELETE" in texto and "GRANT ALL" not in texto


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


def test_no_hay_cambio_automatico_de_estados_y_limite_adpa():
    codigo = (ROOT / "features/biblioteca/services/enlaces.py").read_text(encoding="utf-8")
    assert "UPDATE roadmap_tasks" not in codigo and "UPDATE hallazgos" not in codigo
    assert "UPDATE biblioteca_documentos" not in codigo
    for relativa in ("features/biblioteca/services/enlaces.py", "features/roadmap/roadmap_service.py",
                     "api/routers/biblioteca_enlaces.py"):
        assert len((ROOT / relativa).read_text(encoding="utf-8").splitlines()) <= 500
