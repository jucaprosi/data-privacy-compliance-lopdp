# ¤adpa ¤rbac-tenant ¤arbitro
# ¤¤qa-engineer
"""Árbitro BIB-306: cronología, conservación y restauración trazable.

Mutación decisiva: en `features/biblioteca/services/conservacion.py`, eliminar el primer `if`
de `exigir_eliminable` permite eliminar con bloqueo legal. Hace fallar
`test_bloqueo_legal_prevalece_sobre_politica_y_vencimiento`.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import importlib.util

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from tests._alembic_salas import cabeza_de_sala

from api.errores import ErrorNegocio
from app_core.errors import CATALOGO_ERRORES
from features.biblioteca import biblioteca_service as bib

ROOT = Path(__file__).resolve().parents[1]
MIGRACION = next((ROOT / "alembic/versions").glob("*_biblioteca_conservacion.py"), None)


def conservacion(**cambios):
    base = dict(documento_id="doc", retenido_hasta=None, bloqueo_legal=False, motivo="Prueba",
                politica_id=None, politica_aprobada=False, actualizado_por="actor",
                actualizado_en=datetime.now(timezone.utc))
    return bib.ConservacionDocumento(**(base | cambios))


def test_bloqueo_legal_prevalece_sobre_politica_y_vencimiento():
    vencida = datetime.now(timezone.utc) - timedelta(days=1)
    with pytest.raises(ErrorNegocio) as exc:
        bib.exigir_eliminable(conservacion(bloqueo_legal=True, politica_id="POL-1",
                                          politica_aprobada=True, retenido_hasta=vencida))
    assert exc.value.code == "BIB_BLOQUEO_LEGAL_ACTIVO"


def test_sin_politica_aprobada_o_con_retencion_no_es_eliminable():
    with pytest.raises(ErrorNegocio) as exc:
        bib.exigir_eliminable(conservacion())
    assert exc.value.code == "BIB_POLITICA_CONSERVACION_PENDIENTE"
    with pytest.raises(ErrorNegocio) as exc:
        bib.exigir_eliminable(conservacion(politica_id="POL-1", politica_aprobada=True,
                                          retenido_hasta=datetime.now(timezone.utc) + timedelta(days=1)))
    assert exc.value.code == "BIB_RETENCION_ACTIVA"


def test_solo_politica_aprobada_vencida_sin_bloqueo_supera_la_compuerta():
    bib.exigir_eliminable(conservacion(politica_id="POL-1", politica_aprobada=True,
                                      retenido_hasta=datetime.now(timezone.utc) - timedelta(seconds=1)))


def test_contratos_cronologia_y_restauracion_no_aceptan_tenant_del_cliente():
    evento = bib.RegistrarEvento(tipo="notificacion", detalle={"canal": "correo"})
    assert evento.tipo == "notificacion"
    with pytest.raises(ValueError):
        bib.RestaurarRevision(revision_origen=1, motivo="volver", tenant_id="otra")


def test_compuerta_errores_router_y_archivos_bajo_500_lineas():
    esperados = ("cronologia", "registrar_evento", "restaurar_revision", "obtener_conservacion",
                 "cambiar_conservacion", "exigir_eliminable")
    assert all(nombre in bib.__all__ and hasattr(bib, nombre) for nombre in esperados)
    for codigo in ("BIB_BLOQUEO_LEGAL_ACTIVO", "BIB_RETENCION_ACTIVA",
                   "BIB_POLITICA_CONSERVACION_PENDIENTE", "BIB_REVISION_NO_ENCONTRADA"):
        assert CATALOGO_ERRORES[codigo].status_code in (404, 409)
    from api.routers import biblioteca_historial as router
    assert router.AUTO_REGISTRO is True
    rutas = {r.path for r in router.router.routes}
    assert "/biblioteca/documentos/{documento_id}/cronologia" in rutas
    assert "/biblioteca/documentos/{documento_id}/restauraciones" in rutas
    for relativa in ("features/biblioteca/services/conservacion.py", "features/biblioteca/services/historial.py",
                     "api/routers/biblioteca_historial.py"):
        assert len((ROOT / relativa).read_text(encoding="utf-8").splitlines()) <= 500


def test_migracion_rls_forzada_historial_inmutable_y_sin_permiso_delete():
    assert MIGRACION is not None
    spec = importlib.util.spec_from_file_location("bib306_migracion", MIGRACION)
    migracion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migracion)
    assert len(migracion.revision) <= 32
    cfg = Config(str(ROOT / "alembic.ini")); cfg.set_main_option("script_location", str(ROOT / "alembic"))
    guion = ScriptDirectory.from_config(cfg)
    assert cabeza_de_sala("biblioteca", guion) and guion.get_revision(migracion.revision) is not None
    sql = []
    class Operaciones:
        def execute(self, consulta): sql.append(consulta)
    migracion.op = Operaciones(); migracion.upgrade(); texto = "\n".join(sql)
    for tabla in ("biblioteca_conservacion", "biblioteca_eventos_documento"):
        assert f"ALTER TABLE {tabla} ENABLE ROW LEVEL SECURITY" in texto
        assert f"ALTER TABLE {tabla} FORCE ROW LEVEL SECURITY" in texto
    assert "BEFORE UPDATE OR DELETE ON biblioteca_eventos_documento" in texto
    permisos = "\n".join(line for line in texto.splitlines() if line.strip().startswith("GRANT"))
    assert "DELETE" not in permisos and "GRANT ALL" not in permisos


def test_secciones_bib_306_son_unicas_y_migracion_conserva_historial():
    for relativa, marca in (("features/biblioteca/biblioteca_service.py", "#"),
                            ("features/biblioteca/domain/errores.py", "#"),
                            ("frontend/src/components/biblioteca/vistas/index.ts", "//")):
        texto = (ROOT / relativa).read_text(encoding="utf-8")
        assert texto.count(f"{marca} === BIB-306 ===") == 1
        assert texto.count(f"{marca} === fin BIB-306 ===") == 1
    migracion = MIGRACION.read_text(encoding="utf-8")
    assert "REFERENCES biblioteca_documentos(id)" in migracion
    assert "DROP TABLE biblioteca_documentos" not in migracion
