"""DER-06b · Activar los tipos nuevos de solicitud: TIPOS_ACTIVOS y textos de la interfaz.

`¤regulation-code` `¤arbitro`

Contra la PostgreSQL 16 de pruebas migrada (TEST_DATABASE_URL). Valores simulados.
Cada prueba lleva su mutación.
"""
import re
import uuid
from pathlib import Path

import pytest
from sqlalchemy import text

from features.derechos_arco import derechos_arco_service as compuerta
from features.derechos_arco.domain import plazos
from features.derechos_arco.domain.models import TipoSolicitud

RAIZ = Path(__file__).resolve().parents[1]
NUEVOS = ("SUSPENSION", "DECISIONES_AUTOMATIZADAS", "QUEJA")
DATOS = {"cedula_solicitante": "1700000001", "nombre_solicitante": "Titular Simulado"}


async def _tenant(session) -> str:
    tid = f"t-der06b-{uuid.uuid4().hex[:10]}"
    await session.execute(
        text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:t, :t, :t, :ruc)"),
        {"t": tid, "ruc": f"RUC{uuid.uuid4().hex[:12]}"},
    )
    return tid


def test_los_ocho_tipos_estan_activos_con_plazo():
    assert plazos.TIPOS_ACTIVOS == frozenset(TipoSolicitud)
    assert len(plazos.TIPOS_ACTIVOS) == 8
    for nombre in NUEVOS:
        assert plazos.plazo_dias(TipoSolicitud(nombre)) == 10


@pytest.mark.parametrize("nombre", NUEVOS)
@pytest.mark.asyncio
async def test_crear_cada_tipo_nuevo_da_fila_y_plazo_de_diez_dias(db_session, nombre):
    tenant = await _tenant(db_session)
    creada = await compuerta.crear_solicitud_arco(db_session, {**DATOS, "tipo_solicitud": nombre}, tenant_id=tenant)
    assert creada.tipo_solicitud == TipoSolicitud(nombre)
    dias = (creada.fecha_vencimiento - creada.fecha_recepcion).days
    assert dias == 10
    total = (await db_session.execute(
        text("SELECT count(*) FROM derechos_arco_solicitudes WHERE tenant_id_texto = :t"), {"t": tenant}
    )).scalar()
    assert total == 1
    await db_session.rollback()


@pytest.mark.parametrize("nombre", NUEVOS)
@pytest.mark.asyncio
async def test_mutacion_tipo_fuera_de_tipos_activos_se_rechaza(db_session, monkeypatch, nombre):
    """Mutación: dejar un tipo fuera de TIPOS_ACTIVOS rompe la creación."""
    tenant = await _tenant(db_session)
    monkeypatch.setattr(compuerta, "TIPOS_ACTIVOS", plazos.TIPOS_ACTIVOS - {TipoSolicitud(nombre)})
    with pytest.raises(compuerta.TipoNoDisponible):
        await compuerta.crear_solicitud_arco(db_session, {**DATOS, "tipo_solicitud": nombre}, tenant_id=tenant)
    await db_session.rollback()
