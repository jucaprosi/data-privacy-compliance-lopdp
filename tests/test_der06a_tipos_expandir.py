"""DER-06a · Tipos nuevos de solicitud: expandir el enum sin activarlos.

`¤regulation-code` `¤arbitro`

Contra la PostgreSQL 16 de pruebas migrada (TEST_DATABASE_URL). Valores simulados.
"""
import enum
import importlib.util
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import Column, Enum, MetaData, String, Table, create_engine, select, text
from alembic.migration import MigrationContext
from alembic.operations import Operations

from features.derechos_arco import derechos_arco_service as compuerta
from features.derechos_arco.domain import plazos
from features.derechos_arco.domain.models import TipoSolicitud

pytestmark = pytest.mark.asyncio

RAIZ = Path(__file__).resolve().parents[1]
NUEVOS = ("SUSPENSION", "DECISIONES_AUTOMATIZADAS", "QUEJA")
DATOS = {"cedula_solicitante": "1700000001", "nombre_solicitante": "Titular Simulado"}

# Lector congelado: la revisión anterior de Cloud Run solo conoce los cinco valores originales.
Antiguo = enum.Enum("Antiguo", {n: n for n in ("ACCESO", "RECTIFICACION", "CANCELACION", "OPOSICION", "PORTABILIDAD")})
_tabla_antigua = Table(
    "derechos_arco_solicitudes", MetaData(),
    Column("id", String),
    Column("tenant_id_texto", String),
    Column("tipo_solicitud", Enum(Antiguo, name="tiposolicitud", create_type=False)),
)


async def _tenant(session) -> str:
    tid = f"t-der06a-{uuid.uuid4().hex[:10]}"
    await session.execute(
        text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:t, :t, :t, :ruc)"),
        {"t": tid, "ruc": f"RUC{uuid.uuid4().hex[:12]}"},
    )
    return tid


async def _lector_antiguo(session, tenant: str):
    res = await session.execute(select(_tabla_antigua.c.tipo_solicitud).where(_tabla_antigua.c.tenant_id_texto == tenant))
    return list(res.scalars().all())


async def _insertar_sql(session, tenant: str, tipo: str) -> None:
    await session.execute(
        text(
            "INSERT INTO derechos_arco_solicitudes (id, tenant_id_texto, tipo_solicitud, estado, cedula_solicitante, "
            "nombre_solicitante, fecha_vencimiento) VALUES (:id, :t, CAST(:tipo AS tiposolicitud), 'RECIBIDA', "
            "'1700000001', 'Titular Simulado', :v)"
        ),
        {"id": str(uuid.uuid4()), "t": tenant, "tipo": tipo, "v": datetime.now(timezone.utc) + timedelta(days=10)},
    )


def test_modelo_y_plazos_leen_los_tres_valores_pero_no_los_activan():
    for nombre in NUEVOS:
        tipo = TipoSolicitud(nombre)
        assert plazos.plazo_dias(tipo) == 10
        assert tipo not in plazos.TIPOS_ACTIVOS
    assert {t.value for t in plazos.PLAZO_POR_TIPO} == {t.value for t in TipoSolicitud}
    assert len(plazos.TIPOS_ACTIVOS) == 5


async def test_a_lector_antiguo_lista_las_filas_con_los_tipos_nuevos_inactivos(db_session):
    tenant = await _tenant(db_session)
    creada = await compuerta.crear_solicitud_arco(db_session, {**DATOS, "tipo_solicitud": "PORTABILIDAD"}, tenant_id=tenant)
    assert creada.id is not None
    # Un tipo nuevo inactivo no crea fila: el lector antiguo sigue leyendo todo lo que hay.
    with pytest.raises(compuerta.TipoNoDisponible):
        await compuerta.crear_solicitud_arco(db_session, {**DATOS, "tipo_solicitud": "QUEJA"}, tenant_id=tenant)
    assert [t.value for t in await _lector_antiguo(db_session, tenant)] == ["PORTABILIDAD"]
    await db_session.rollback()


@pytest.mark.parametrize("nombre", NUEVOS)
async def test_b_tipo_nuevo_inactivo_se_rechaza_en_la_compuerta_sin_crear_fila(db_session, nombre):
    tenant = await _tenant(db_session)
    with pytest.raises(compuerta.TipoNoDisponible, match="tipo no disponible"):
        await compuerta.crear_solicitud_arco(db_session, {**DATOS, "tipo_solicitud": nombre}, tenant_id=tenant)
    total = (await db_session.execute(
        text("SELECT count(*) FROM derechos_arco_solicitudes WHERE tenant_id_texto = :t"), {"t": tenant}
    )).scalar()
    assert total == 0
    await db_session.rollback()


@pytest.mark.parametrize("nombre", NUEVOS)
async def test_la_base_acepta_los_tres_valores_nuevos(db_session, nombre):
    tenant = await _tenant(db_session)
    await _insertar_sql(db_session, tenant, nombre)
    await db_session.rollback()


async def test_mutacion_activar_un_tipo_rompe_al_lector_antiguo(db_session, monkeypatch):
    """Demuestra el porqué: con el tipo activo y una fila creada, el lector de cinco valores falla."""
    tenant = await _tenant(db_session)
    monkeypatch.setattr(compuerta, "TIPOS_ACTIVOS", plazos.TIPOS_ACTIVOS | {TipoSolicitud.QUEJA})
    creada = await compuerta.crear_solicitud_arco(db_session, {**DATOS, "tipo_solicitud": "QUEJA"}, tenant_id=tenant)
    assert creada.tipo_solicitud == TipoSolicitud.QUEJA
    with pytest.raises(LookupError):
        await _lector_antiguo(db_session, tenant)
    await db_session.rollback()


def test_c_la_migracion_es_idempotente():
    url = os.environ.get("TEST_DATABASE_URL", "")
    assert url, "TEST_DATABASE_URL es obligatoria"
    spec = importlib.util.spec_from_file_location("der06a_mig", RAIZ / "alembic/versions/20261123_der06a_tipos_solicitud.py")
    mig = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mig)
    motor = create_engine(url.replace("postgresql+asyncpg://", "postgresql://").replace("postgresql://", "postgresql+psycopg://", 1))
    try:
        for _ in range(2):
            with motor.connect() as conexion:
                contexto = MigrationContext.configure(conexion)
                with Operations.context(contexto):
                    mig.upgrade()
        with motor.connect() as conexion:
            etiquetas = {r[0] for r in conexion.execute(text("SELECT unnest(enum_range(NULL::tiposolicitud))::text"))}
    finally:
        motor.dispose()
    assert set(NUEVOS) <= etiquetas
