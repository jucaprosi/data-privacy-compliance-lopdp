"""GCP-01 · RLS en 1 RTT, PgBouncer sin sentencias preparadas y chasis Cloud Run.

`¤cloud-run-perf` `¤seguridad-tenant` — INV_LOPDP_SINGLE_RTT_RLS_PGBOUNCER
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import text

RAIZ = Path(__file__).resolve().parents[1]


class _SesionEspia:
    def __init__(self):
        self.sentencias = []

    async def execute(self, sentencia, parametros=None):
        self.sentencias.append((str(sentencia), parametros))


def test_rls_set_config_un_solo_viaje_sql():
    from app_core.db.session import fijar_contexto_rls

    espia = _SesionEspia()
    asyncio.run(fijar_contexto_rls(espia, "t-1", "u-1"))
    assert len(espia.sentencias) == 1
    sql, params = espia.sentencias[0]
    assert "app.current_tenant_id" in sql and "app.current_user_id" in sql
    assert params == {"tid": "t-1", "uid": "u-1"}

    solo_tenant = _SesionEspia()
    asyncio.run(fijar_contexto_rls(solo_tenant, "t-1"))
    assert len(solo_tenant.sentencias) == 1
    assert "app.current_user_id" not in solo_tenant.sentencias[0][0]


@pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="sin TEST_DATABASE_URL")
def test_rls_set_config_valores_activos_en_transaccion():
    """Contra la rama Neon de prueba: ambos valores quedan fijados tras una sola sentencia."""
    from sqlalchemy.ext.asyncio import create_async_engine

    from app_core.cloud.gcp_runtime import argumentos_motor
    from app_core.db.session import fijar_contexto_rls

    url = os.environ["TEST_DATABASE_URL"].replace("postgresql://", "postgresql+psycopg://", 1)

    async def _probar():
        motor = create_async_engine(url, connect_args=argumentos_motor(url))
        try:
            async with motor.connect() as conn:
                async with conn.begin():
                    from sqlalchemy.ext.asyncio import AsyncSession

                    sesion = AsyncSession(bind=conn)
                    await fijar_contexto_rls(sesion, "11111111-1111-1111-1111-111111111111", "u-gcp01")
                    fila = (await sesion.execute(text(
                        "SELECT current_setting('app.current_tenant_id'), current_setting('app.current_user_id')"
                    ))).one()
                    return tuple(fila)
        finally:
            await motor.dispose()

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    assert asyncio.run(_probar()) == ("11111111-1111-1111-1111-111111111111", "u-gcp01")


def test_pgbouncer_prepare_threshold_y_manifiesto_cloudrun(monkeypatch):
    from app_core.cloud import gcp_runtime as rt

    monkeypatch.delenv("DB_POOLER_TRANSACCIONAL", raising=False)
    pooler = "postgresql+psycopg://u:p@ep-x-pooler.c-7.us-east-2.aws.neon.tech/db?sslmode=require"
    directa = "postgresql+psycopg://u:p@ep-x.c-7.us-east-2.aws.neon.tech/db?sslmode=require"
    proxy = "postgresql+psycopg://u:p@/db?host=/cloudsql/proy:region:inst"
    assert rt.argumentos_motor(pooler) == {"prepare_threshold": None}
    assert rt.argumentos_motor(proxy) == {"prepare_threshold": None}
    assert rt.argumentos_motor(directa) == {}
    monkeypatch.setenv("DB_POOLER_TRANSACCIONAL", "1")
    assert rt.argumentos_motor(directa) == {"prepare_threshold": None}

    docker = (RAIZ / "governance/operaciones/Dockerfile.cloudrun").read_text(encoding="utf-8")
    assert "uvicorn main:app" in docker and "--loop uvloop" in docker and "--http httptools" in docker
    assert "--workers 1" in docker and "USER app" in docker and "uv pip install" in docker
    servicio = (RAIZ / "governance/operaciones/cloudrun_service.yaml").read_text(encoding="utf-8")
    assert "containerConcurrency: 80" in servicio
    assert 'run.googleapis.com/startup-cpu-boost: "true"' in servicio


def test_clientes_gcp_perezosos_y_secretos_por_entorno(monkeypatch):
    from app_core.cloud import gcp_runtime as rt

    rt._reiniciar_clientes()
    assert rt.clientes_iniciados() == ()
    creados = []
    cliente = rt.cliente_gcp("storage", fabrica=lambda: creados.append(1) or object())
    assert rt.cliente_gcp("storage") is cliente and creados == [1]
    rt._reiniciar_clientes()

    monkeypatch.setenv("SECRETO_GCP01", "valor")
    assert rt.leer_secreto("SECRETO_GCP01") == "valor"
    monkeypatch.delenv("SECRETO_GCP01")
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    assert rt.leer_secreto("SECRETO_GCP01") is None
    assert rt.clientes_iniciados() == ()
    assert set(rt.telemetria_cloudrun()) >= {"uvloop", "pooler_transaccional", "adc_proyecto"}
