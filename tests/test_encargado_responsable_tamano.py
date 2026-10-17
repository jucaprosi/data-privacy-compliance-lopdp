# ¤rbac-tenant
# ¤seguridad
# ¤arbitro
"""RM-16: INV_LOPDP_ENCARGADO_RESPONSABLE_SIZE (encargado + responsable_area según tamaño).

Las pruebas contra la BD corren dentro de una transacción que siempre se revierte: no dejan
datos y no dependen de que la migración ya esté aplicada (instalan el trigger de la propia
migración dentro de la transacción). Usan el servicio directamente, sin cabeceras ni modo de
autenticación.
"""
from __future__ import annotations

import importlib.util
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from features.organizacion import organizacion_service as svc
from features.organizacion.domain.models import RoleGrant
from features.organizacion.services import regla_tamano_engine as regla

pytestmark = pytest.mark.asyncio

MIGRACION = Path(__file__).resolve().parent.parent / "alembic" / "versions" / "20261017_encargado_responsable_trigger.py"
PASADO = datetime(2020, 1, 1, tzinfo=timezone.utc)


def _sentencias_migracion() -> list[str]:
    spec = importlib.util.spec_from_file_location("mig_rm16", MIGRACION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    capturadas: list[str] = []

    class _Op:
        @staticmethod
        def execute(sql):
            capturadas.append(str(sql))

    mod.op = _Op
    mod.upgrade()
    return capturadas


@pytest_asyncio.fixture
async def conn(db_engine):
    async with db_engine.connect() as c:
        tx = await c.begin()
        try:
            yield c
        finally:
            await tx.rollback()


@pytest_asyncio.fixture
async def session(conn):
    return AsyncSession(bind=conn, expire_on_commit=False)


@pytest_asyncio.fixture
async def trigger(conn):
    await conn.execute(text("DROP TRIGGER IF EXISTS trg_utr_encargado_responsable ON user_tenant_roles"))
    for sql in _sentencias_migracion():
        await conn.execute(text(sql))


async def _tenant(conn, tamano):
    tid = f"rm16-t-{uuid.uuid4().hex[:10]}"
    await conn.execute(
        text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
             "VALUES (:i, :n, :r, :ruc, :tam)"),
        {"i": tid, "n": tid, "r": tid, "ruc": f"RUC{uuid.uuid4().hex[:12]}", "tam": tamano},
    )
    return tid


async def _usuario(conn):
    uid = f"rm16-u-{uuid.uuid4().hex[:10]}"
    await conn.execute(
        text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, :n)"),
        {"i": uid, "e": f"{uid}@test.local", "n": uid},
    )
    return uid


async def _rol(conn, uid, tid, role, also=False, valid_to=None):
    await conn.execute(
        text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role, also_responsable, valid_to) "
             "VALUES (:i, :u, :t, :r, :a, :v)"),
        {"i": f"rm16-r-{uuid.uuid4().hex[:10]}", "u": uid, "t": tid, "r": role, "a": also, "v": valid_to},
    )


# ---- Regla pura: las cuatro tallas y el fallo cerrado ----

@pytest.mark.parametrize("tamano", ["micro", "pequena"])
async def test_micro_y_pequena_permiten(tamano):
    regla.evaluar_tamano(tamano)


@pytest.mark.parametrize("tamano", ["mediana", "corporativo"])
async def test_mediana_y_corporativo_son_sod_violation(tamano):
    with pytest.raises(ErrorNegocio) as e:
        regla.evaluar_tamano(tamano)
    assert e.value.code == "SOD_VIOLATION" and e.value.status_code == 409


@pytest.mark.parametrize("tamano", [None, "", "gigante", "MICRO"])
async def test_tamano_nulo_o_invalido_falla_cerrado(tamano):
    with pytest.raises(ErrorNegocio) as e:
        regla.evaluar_tamano(tamano)
    assert e.value.code == "TENANT_SIZE_NOT_CONFIGURED"
    assert e.value.action_required == "configure_tenant_size"


# ---- Validación del servicio (sin trigger instalado) ----

@pytest.mark.parametrize("par", [("encargado", "responsable_area"), ("responsable_area", "encargado")])
@pytest.mark.parametrize("tamano,codigo", [
    ("micro", None), ("pequena", None), ("mediana", "SOD_VIOLATION"),
    ("corporativo", "SOD_VIOLATION"), (None, "TENANT_SIZE_NOT_CONFIGURED"),
])
async def test_servicio_valida_ambas_direcciones(conn, session, par, tamano, codigo):
    tid = await _tenant(conn, tamano)
    uid = await _usuario(conn)
    await _rol(conn, uid, tid, par[0])
    if codigo is None:
        await regla.verificar_encargado_responsable(session, tid, uid, par[1])
    else:
        with pytest.raises(ErrorNegocio) as e:
            await regla.verificar_encargado_responsable(session, tid, uid, par[1])
        assert e.value.code == codigo


async def test_servicio_sin_rol_contrario_no_exige_tamano(conn, session):
    tid = await _tenant(conn, None)
    uid = await _usuario(conn)
    await regla.verificar_encargado_responsable(session, tid, uid, "encargado")


async def test_servicio_ignora_rol_contrario_revocado(conn, session):
    tid = await _tenant(conn, "mediana")
    uid = await _usuario(conn)
    await _rol(conn, uid, tid, "encargado", valid_to=PASADO)
    await regla.verificar_encargado_responsable(session, tid, uid, "responsable_area")


async def test_grant_role_publico_aplica_la_regla(conn, session):
    tid = await _tenant(conn, "mediana")
    uid, admin = await _usuario(conn), await _usuario(conn)
    await _rol(conn, uid, tid, "encargado")
    with pytest.raises(ErrorNegocio) as e:
        await svc.grant_role(session, tid, admin, RoleGrant(user_id=uid, role="responsable_area"))
    assert e.value.code == "SOD_VIOLATION"


async def test_grant_role_publico_permite_en_micro(conn, session):
    tid = await _tenant(conn, "micro")
    uid, admin = await _usuario(conn), await _usuario(conn)
    await _rol(conn, uid, tid, "encargado")
    fila = await svc.grant_role(session, tid, admin, RoleGrant(user_id=uid, role="responsable_area"))
    assert fila["role"] == "responsable_area"


# ---- Trigger de la BD ----

@pytest.mark.parametrize("par", [("encargado", "responsable_area"), ("responsable_area", "encargado")])
@pytest.mark.parametrize("also", [False, True])
@pytest.mark.parametrize("tamano,marca", [
    ("mediana", "SOD_VIOLATION"), ("corporativo", "SOD_VIOLATION"),
    (None, "TENANT_SIZE_NOT_CONFIGURED"),
])
async def test_trigger_bloquea_ambas_direcciones_aunque_also_responsable_se_falsee(
    conn, trigger, par, also, tamano, marca
):
    tid = await _tenant(conn, tamano)
    uid = await _usuario(conn)
    await _rol(conn, uid, tid, par[0], also=also)
    with pytest.raises(IntegrityError) as e:
        await _rol(conn, uid, tid, par[1], also=also)
    assert marca in str(e.value.orig)


@pytest.mark.parametrize("par", [("encargado", "responsable_area"), ("responsable_area", "encargado")])
@pytest.mark.parametrize("tamano", ["micro", "pequena"])
async def test_trigger_permite_en_micro_y_pequena(conn, trigger, par, tamano):
    tid = await _tenant(conn, tamano)
    uid = await _usuario(conn)
    await _rol(conn, uid, tid, par[0])
    await _rol(conn, uid, tid, par[1])


async def test_trigger_ignora_rol_contrario_revocado(conn, trigger):
    tid = await _tenant(conn, "corporativo")
    uid = await _usuario(conn)
    await _rol(conn, uid, tid, "encargado", valid_to=PASADO)
    await _rol(conn, uid, tid, "responsable_area")


async def test_servicio_traduce_la_excepcion_del_trigger(conn, trigger, session, monkeypatch):
    """Sin la validación previa del servicio, el 409 sale de traducir el error del trigger."""
    async def _nada(*a, **k):
        return None

    monkeypatch.setattr(svc, "verificar_encargado_responsable", _nada)
    tid = await _tenant(conn, "mediana")
    uid, admin = await _usuario(conn), await _usuario(conn)
    await _rol(conn, uid, tid, "encargado")
    with pytest.raises(ErrorNegocio) as e:
        await svc.grant_role(session, tid, admin, RoleGrant(user_id=uid, role="responsable_area"))
    assert e.value.code == "SOD_VIOLATION" and e.value.status_code == 409


async def test_traduccion_del_trigger_sin_tamano(conn, trigger):
    tid = await _tenant(conn, None)
    uid = await _usuario(conn)
    await _rol(conn, uid, tid, "encargado")
    with pytest.raises(IntegrityError) as e:
        await _rol(conn, uid, tid, "responsable_area")
    traducido = regla.traducir_error_trigger(e.value)
    assert traducido.code == "TENANT_SIZE_NOT_CONFIGURED"
    assert traducido.action_required == "configure_tenant_size"
    assert regla.traducir_error_trigger(ValueError("otra cosa")) is None
