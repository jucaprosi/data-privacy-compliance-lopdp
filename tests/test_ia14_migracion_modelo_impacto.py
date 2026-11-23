# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""IA-14 · la migración quita el CHECK de literal de `normativa_analisis_impacto.modelo`.

`¤arbitro` `¤gemini-vertex`

Contra la PostgreSQL 16 local del arnés (TEST_DATABASE_URL); nunca producción. La migración corre sobre una réplica
de la tabla en un esquema temporal, con el CHECK que declara NORM-03. Datos simulados.

Mutación m3: dejar el CHECK de literal en `upgrade()` hace fallar `test_upgrade_acepta_el_modelo_del_pasillo`.
"""
import importlib.util
import os
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from conftest import exigir_base_de_pruebas
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from app_core.pasillo import inferencia as pasillo_inferencia

RAIZ = Path(__file__).resolve().parents[1]
RUTA = RAIZ / "alembic/versions/20261123_ia14_modelo_impacto_sin_literal.py"
_spec = importlib.util.spec_from_file_location("ia14_migracion", RUTA)
migracion = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(migracion)

ESQUEMA = "ia14_replica"
INSERTAR = "INSERT INTO normativa_analisis_impacto (modelo) VALUES (:m)"


def _motor():
    exigir_base_de_pruebas()
    url = os.environ.get("TEST_DATABASE_URL", "")
    if not url:
        pytest.skip("TEST_DATABASE_URL no definida (PostgreSQL 16 local del arnés)")
    url = url.replace("postgresql+asyncpg://", "postgresql://").replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(url)


@pytest.fixture
def replica():
    motor = _motor()
    with motor.begin() as c:
        c.execute(text(f"DROP SCHEMA IF EXISTS {ESQUEMA} CASCADE"))
        c.execute(text(f"CREATE SCHEMA {ESQUEMA}"))
        c.execute(text(f"SET LOCAL search_path = {ESQUEMA}"))
        c.execute(text("CREATE TABLE normativa_analisis_impacto (modelo VARCHAR(40) NOT NULL CHECK (modelo = 'gemini-2.5-pro'))"))
    try:
        yield motor
    finally:
        with motor.begin() as c:
            c.execute(text(f"DROP SCHEMA IF EXISTS {ESQUEMA} CASCADE"))
        motor.dispose()


def _correr(motor, funcion):
    with motor.begin() as c:
        c.execute(text(f"SET LOCAL search_path = {ESQUEMA}"))
        with Operations.context(MigrationContext.configure(c)):
            funcion()


def _insertar(motor, modelo):
    with motor.begin() as c:
        c.execute(text(f"SET LOCAL search_path = {ESQUEMA}"))
        c.execute(text(INSERTAR), {"m": modelo})


def test_revision_cuelga_de_norm03():
    assert migracion.down_revision == "norm03_analisis_impacto"
    assert migracion.branch_labels is None


def test_antes_del_upgrade_el_modelo_nuevo_falla(replica):
    with pytest.raises(DBAPIError):
        _insertar(replica, pasillo_inferencia.MODELO_GENERACION)


def test_upgrade_acepta_el_modelo_del_pasillo(replica):
    _correr(replica, migracion.upgrade)
    _insertar(replica, pasillo_inferencia.MODELO_GENERACION)


def test_upgrade_rechaza_modelo_vacio(replica):
    _correr(replica, migracion.upgrade)
    with pytest.raises(DBAPIError):
        _insertar(replica, "")


def test_downgrade_y_otro_upgrade_terminan_sin_error(replica):
    _correr(replica, migracion.upgrade)
    _insertar(replica, pasillo_inferencia.MODELO_GENERACION)
    _correr(replica, migracion.downgrade)  # NOT VALID: la fila ya escrita no lo hace fallar
    with pytest.raises(DBAPIError):
        _insertar(replica, pasillo_inferencia.MODELO_GENERACION)
    _correr(replica, migracion.upgrade)
    _insertar(replica, pasillo_inferencia.MODELO_GENERACION)
