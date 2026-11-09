# ¤arbitro
# ¤¤qa-engineer
"""Árbitro ADPA-08: terceros_encargados y transferencias_terceros existen con RLS forzada. ¤adpa ¤transferencias ¤seguridad-tenant

Las pruebas de esquema corren contra PostgreSQL 16 local (TEST_DATABASE_URL) con la base migrada;
sin esa variable se saltan. La de acoplamiento entre salas es estática y corre siempre.
Datos sintéticos y rollback.

Mutaciones documentadas (2026-11-09, contenedor postgres:16):
1. Sin `FORCE ROW LEVEL SECURITY`, test_ambas_tablas_con_rls_forzada_y_politica falla.
2. Sin el GRANT a lopdp_app, test_lopdp_app_lee_inserta_y_actualiza_sin_borrar falla.
3. Con `from features.terceros...` en features/transferencias/models.py, test_salas_desacopladas falla.
"""
import ast
import os
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

RAIZ = Path(__file__).resolve().parent.parent
TABLAS = ("terceros_encargados", "transferencias_terceros")


@pytest_asyncio.fixture
async def conexion():
    url = os.environ.get("TEST_DATABASE_URL", "")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_async_engine(url, hide_parameters=True)
    async with engine.connect() as con:
        transaccion = await con.begin()
        try:
            yield con
        finally:
            await transaccion.rollback()
    await engine.dispose()


@pytest.mark.asyncio
async def test_ambas_tablas_con_rls_forzada_y_politica(conexion):
    filas = (await conexion.execute(text(
        "SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity, "
        "(SELECT count(*) FROM pg_policies p WHERE p.tablename = c.relname "
        " AND p.policyname = 'tenant_isolation_' || c.relname AND p.with_check IS NOT NULL) "
        "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = 'public' AND c.relname = ANY(:t)"), {"t": list(TABLAS)})).all()
    assert {f[0] for f in filas} == set(TABLAS)
    for nombre, rls, forzada, politicas in filas:
        assert rls and forzada and politicas == 1, nombre


@pytest.mark.asyncio
async def test_lopdp_app_lee_inserta_y_actualiza_sin_borrar(conexion):
    for tabla in TABLAS:
        for permiso, esperado in (("SELECT", True), ("INSERT", True), ("UPDATE", True), ("DELETE", False)):
            r = (await conexion.execute(text("SELECT has_table_privilege('lopdp_app', :t, :p)"),
                                        {"t": tabla, "p": permiso})).scalar()
            assert r is esperado, (tabla, permiso)


@pytest.mark.asyncio
async def test_rls_aisla_por_tenant_como_lopdp_app(conexion):
    a, b = str(uuid4()), str(uuid4())
    for t in (a, b):
        await conexion.execute(text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                                    "VALUES (:t, 'Org sintética', 'Org sintética S.A.', :ruc)"),
                               {"t": t, "ruc": str(uuid4().int)[:13]})
    await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
    await conexion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": a})
    await conexion.execute(text("INSERT INTO terceros_encargados (tenant_id, nombre) VALUES (:t, 'Encargado A')"), {"t": a})
    await conexion.execute(text(
        "INSERT INTO transferencias_terceros (tenant_id, nombre, rol, pais_destino, nivel_proteccion) "
        "VALUES (:t, 'Destino A', 'DESTINATARIO', 'País sintético', 'ESTANDAR')"), {"t": a})
    with pytest.raises(Exception):  # WITH CHECK: no se escribe en otro tenant
        async with conexion.begin_nested():
            await conexion.execute(text("INSERT INTO terceros_encargados (tenant_id, nombre) VALUES (:t, 'Ajeno')"), {"t": b})
    await conexion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": b})
    for tabla in TABLAS:
        assert (await conexion.execute(text(f"SELECT count(*) FROM {tabla}"))).scalar() == 0


def test_salas_desacopladas():
    """transferencias no importa de terceros ni al revés; el modelo de transferencias vive en su sala."""
    def importados(ruta: Path) -> set[str]:
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        salida = set()
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.ImportFrom) and nodo.module:
                salida.add(nodo.module)
            elif isinstance(nodo, ast.Import):
                salida |= {a.name for a in nodo.names}
        return salida

    for sala, otra in (("transferencias", "terceros"), ("terceros", "transferencias")):
        for ruta in (RAIZ / "features" / sala).rglob("*.py"):
            assert not any(m == f"features.{otra}" or m.startswith(f"features.{otra}.") for m in importados(ruta)), ruta
    from features.transferencias import models, transferencias_service
    assert transferencias_service.TerceroEncargado is models.TerceroEncargado
    assert models.TerceroEncargado.__tablename__ == "transferencias_terceros"
