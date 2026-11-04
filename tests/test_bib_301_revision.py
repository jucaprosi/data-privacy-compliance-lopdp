# ¤adpa ¤rbac-tenant ¤arbitro
"""Contrato BIB-301; la persistencia real se acredita solo con el arnés PostgreSQL."""
import importlib.util
import os
from datetime import datetime, timezone
from pathlib import Path
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from api.errores import ErrorNegocio
from app_core.errors import CATALOGO_ERRORES
from features.biblioteca import biblioteca_service as bib
from features.biblioteca.domain.revisiones import DelegarAutoridad, EnviarRevision

ROOT = Path(__file__).resolve().parents[1]
MIGRACION = ROOT / "alembic/versions/bib301_biblioteca_aprobaciones.py"


def test_contratos_rechazan_campos_de_identidad_y_vigencia_invalida():
    with pytest.raises(Exception):
        EnviarRevision(revisor_id="r", tenant_id="ajeno")
    ahora = datetime.now(timezone.utc)
    entrada = DelegarAutoridad(usuario_id="u", criterio="Delegación formal", vigente_desde=ahora)
    assert entrada.vigente_hasta is None


def test_compuerta_errores_y_router_autoregistrado():
    for nombre in ("enviar_a_revision", "devolver_revision", "aprobar_revision", "delegar_autoridad", "abrir_nueva_revision"):
        assert nombre in bib.__all__ and hasattr(bib, nombre)
    for codigo in ("BIB_SEPARACION_FUNCIONES", "BIB_AUTORIDAD_NO_VIGENTE", "BIB_REVISION_DOCUMENTAL_DESFASADA"):
        assert codigo in CATALOGO_ERRORES
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://usuario:clave@localhost/pruebas")
    from api.routers import biblioteca_revisiones as r
    assert r.AUTO_REGISTRO is True
    rutas = {ruta.path for ruta in r.router.routes}
    assert "/biblioteca/revisiones/{revision_id}/aprobar" in rutas


def test_migracion_una_cabeza_rls_y_grants_minimos():
    spec = importlib.util.spec_from_file_location("bib301_migracion", MIGRACION)
    modulo = importlib.util.module_from_spec(spec); spec.loader.exec_module(modulo)
    assert len(modulo.revision) <= 32
    cfg = Config(str(ROOT / "alembic.ini")); cfg.set_main_option("script_location", str(ROOT / "alembic"))
    guion = ScriptDirectory.from_config(cfg)
    assert guion.get_heads() == [modulo.revision]
    sql = []
    class Op: 
        def execute(self, valor): sql.append(valor)
    modulo.op = Op(); modulo.upgrade(); texto = "\n".join(sql)
    for tabla in ("biblioteca_revisiones", "biblioteca_autoridades_aprobacion"):
        assert f"ALTER TABLE {tabla} FORCE ROW LEVEL SECURITY" in texto
        assert f"tenant_isolation_{tabla}" in texto
    assert "GRANT ALL" not in texto and "DELETE" not in texto


class SesionFalsa:
    """SQL mínimo que prueba la barrera decisiva sin fingir RLS."""
    def __init__(self): self.consultas = []
    async def execute(self, consulta, parametros=None):
        self.consultas.append((str(consulta), parametros or {}))
        class R:
            def mappings(self): return self
            def first(self): return {"id":"rev","documento_id":"doc","revision":2,"sha256":"h","revisor_id":"autor",
                "tipo_participacion":"revision","estado":"asignada","observaciones":None,"asignado_por":"otro",
                "asignado_en":datetime.now(timezone.utc),"decidido_por":None,"decidido_en":None,
                "criterio_aprobacion":None,"autoridad_id":None}
            def scalar(self): return "autor"
        return R()


@pytest.mark.asyncio
async def test_mutacion_autoaprobacion_es_bloqueada_antes_de_buscar_autoridad(monkeypatch):
    from features.biblioteca.services import revision_aprobacion as servicio
    async def nada(*_): return None
    monkeypatch.setattr(servicio, "contexto", nada)
    with pytest.raises(ErrorNegocio) as error:
        await servicio.aprobar_revision(SesionFalsa(), "tenant", "autor", "rev", bib.AprobarRevision(criterio="Revisión conforme"))
    assert error.value.code == "BIB_SEPARACION_FUNCIONES"

