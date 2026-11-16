# ¤adpa ¤rbac-tenant ¤arbitro
# ¤¤qa-engineer
"""Árbitro BIB-306: cronología, conservación y restauración trazable.

Mutación decisiva: en `features/biblioteca/services/conservacion.py`, eliminar el primer `if`
de `exigir_eliminable` permite eliminar con bloqueo legal. Hace fallar
`test_bloqueo_legal_prevalece_sobre_politica_y_vencimiento`.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
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


@pytest.mark.asyncio
async def test_cambiar_conservacion_no_elimina_historial(monkeypatch):
    """Comprueba que la actualización de conservación no ejecuta DELETE ni altera el historial."""
    monkeypatch.setattr("features.biblioteca.services.conservacion.contexto", AsyncMock())
    monkeypatch.setattr("features.biblioteca.services.conservacion.obtener_documento", AsyncMock())

    fila_cons = {
        "documento_id": "doc-1", "retenido_hasta": None, "bloqueo_legal": True,
        "motivo": "Bloqueo legal orden judicial", "politica_id": "pol-1",
        "politica_aprobada": True, "actualizado_por": "u-1", "actualizado_en": None,
    }
    class MockResult:
        def mappings(self):
            return SimpleNamespace(first=lambda: fila_cons)

    consultas = []
    async def mock_execute(sql, *args, **kwargs):
        consultas.append(str(sql))
        return MockResult()

    session = SimpleNamespace(execute=AsyncMock(side_effect=mock_execute))
    cambio = bib.CambiarConservacion(
        bloqueo_legal=True, motivo="Bloqueo legal orden judicial",
        politica_id="pol-1", politica_aprobada=True,
    )
    resultado = await bib.cambiar_conservacion(session, "tenant-1", "u-1", "doc-1", cambio)
    assert resultado.bloqueo_legal is True
    assert not any("DELETE" in q.upper() for q in consultas)
    assert not any("DROP" in q.upper() for q in consultas)
