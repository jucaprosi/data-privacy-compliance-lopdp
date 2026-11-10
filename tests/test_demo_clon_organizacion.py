# -*- coding: utf-8 -*-
# ¤demo ¤seguridad-tenant ¤adpa
"""DEMO-03a: siembra y clonado de la sala `organizacion` desde la plantilla «Cooperativa Demo».

Corren contra PostgreSQL real (`TEST_DATABASE_URL`: el PG16 del arnés o evydentia-pruebas, nunca producción).
Solo valores simulados y correos `.invalid`. Los clones no hacen commit: cada prueba los descarta con rollback.

Mutaciones documentadas (cada una hace fallar la prueba que se nombra):
  - si el clon reutiliza los usuarios de la plantilla (`_id_usuario_clon` devuelve el id de origen):
    test_las_personas_del_clon_son_propias y test_personas_ficticias_con_rol_solo_por_user_tenant_roles;
  - si `_correo_clon` deja de conservar el dominio `.invalid`: test_personas_ficticias_con_rol_solo_por_user_tenant_roles;
  - si el clon omite `es_demo = TRUE`: test_el_destino_es_demo_y_copia_las_filas;
  - si el clon reutiliza ids de origen (usuarios o `parent_area_id`): test_ninguna_fila_apunta_a_ids_de_la_plantilla;
  - si se quita la comprobación de existencia en `_rol`/`_area`: test_clonar_dos_veces_no_duplica;
  - si el clon hace commit: test_el_clon_no_hace_commit.
"""
from __future__ import annotations

import ast
import hashlib
import uuid
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app_core.pasillo import organizacion as pasillo
from features.demo.demo_service import PLANTILLA_TENANT_ID

TID = PLANTILLA_TENANT_ID
RAIZ = Path(__file__).resolve().parents[1]
ROLES_OPERATIVOS = {"coordinador", "implementador", "responsable_area", "admin_organizacion"}

@pytest.fixture
def fabrica(db_engine):
    return async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)


async def _sembrar(fabrica) -> None:
    async with fabrica() as s:
        await pasillo.sembrar_en_plantilla(s, TID, {})
        await s.commit()


async def _estado(session, tenant: str) -> dict:
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant})
    consultas = {
        "tenant": "SELECT id, es_demo FROM tenants WHERE id = :t",
        "areas": "SELECT codigo, nivel, nombre FROM areas WHERE tenant_id = :t AND deleted_at IS NULL ORDER BY codigo",
        "roles": "SELECT split_part(u.email, '@', 1), r.role, a.codigo FROM user_tenant_roles r "
                 "JOIN users u ON u.id = r.user_id LEFT JOIN areas a ON a.id = r.area_id "
                 "WHERE r.tenant_id = :t AND (r.valid_to IS NULL OR r.valid_to > now()) ORDER BY 2, 1",
    }
    return {k: [tuple(f) for f in (await session.execute(text(q), {"t": tenant})).all()]
            for k, q in consultas.items()}


async def _filas_de_ids(session, tenant: str) -> set[str]:
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant})
    ids: set[str] = set()
    for sql in ("SELECT id FROM areas WHERE tenant_id = :t",
                "SELECT parent_area_id FROM areas WHERE tenant_id = :t AND parent_area_id IS NOT NULL",
                "SELECT user_id FROM user_tenant_roles WHERE tenant_id = :t",
                "SELECT area_id FROM user_tenant_roles WHERE tenant_id = :t AND area_id IS NOT NULL",
                "SELECT id FROM user_tenant_roles WHERE tenant_id = :t"):
        ids |= {f[0] for f in (await session.execute(text(sql), {"t": tenant})).all()}
    return ids


def _huella(estado: dict) -> str:
    return hashlib.sha256(repr(estado).encode()).hexdigest()


# --- Siembra -----------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dos_siembras_dejan_el_mismo_estado(fabrica):
    await _sembrar(fabrica)
    async with fabrica() as s:
        antes = await _estado(s, TID)
    await _sembrar(fabrica)
    async with fabrica() as s:
        despues = await _estado(s, TID)
    assert _huella(antes) == _huella(despues)
    assert antes["tenant"] == [(TID, True)]
    assert len(antes["areas"]) == 3 and len(antes["roles"]) == 5


# --- Clonado -----------------------------------------------------------------------------------------

async def _clonar(session, destino: str, mapa: dict | None = None) -> dict:
    return await pasillo.clonar_desde_plantilla(session, TID, destino, mapa or {})


@pytest.mark.asyncio
async def test_el_destino_es_demo_y_copia_las_filas(fabrica):
    await _sembrar(fabrica)
    destino = f"demo-{uuid.uuid4().hex[:10]}"
    async with fabrica() as s:
        origen = await _estado(s, TID)
        await _clonar(s, destino)
        clon = await _estado(s, destino)
        await s.rollback()
    assert clon["tenant"] == [(destino, True)]
    assert clon["areas"] == origen["areas"]
    assert sorted((rol, area) for _, rol, area in clon["roles"]) == sorted(
        (rol, area) for _, rol, area in origen["roles"])


@pytest.mark.asyncio
async def test_la_plantilla_queda_intacta(fabrica):
    await _sembrar(fabrica)
    destino = f"demo-{uuid.uuid4().hex[:10]}"
    async with fabrica() as s:
        antes = _huella(await _estado(s, TID))
        usuarios_antes = (await s.execute(text("SELECT count(*) FROM users WHERE id LIKE 'usr-ep-%'"))).scalar_one()
        ids_antes = await _filas_de_ids(s, TID)
        await _clonar(s, destino)
        assert _huella(await _estado(s, TID)) == antes
        assert await _filas_de_ids(s, TID) == ids_antes
        assert (await s.execute(text("SELECT count(*) FROM users WHERE id LIKE 'usr-ep-%'"))).scalar_one()             == usuarios_antes
        await s.rollback()


@pytest.mark.asyncio
async def test_ninguna_fila_apunta_a_ids_de_la_plantilla(fabrica):
    await _sembrar(fabrica)
    destino = f"demo-{uuid.uuid4().hex[:10]}"
    async with fabrica() as s:
        ids_plantilla = await _filas_de_ids(s, TID)
        mapa = await _clonar(s, destino)
        ids_destino = await _filas_de_ids(s, destino)
        await s.rollback()
    assert ids_plantilla and ids_destino
    assert not ids_plantilla & ids_destino
    claves = {k for k in mapa if k != TID}
    assert claves and all(mapa[k] != k for k in claves) and mapa[TID] == destino


@pytest.mark.asyncio
async def test_el_mapa_amplia_el_que_recibe(fabrica):
    await _sembrar(fabrica)
    destino = f"demo-{uuid.uuid4().hex[:10]}"
    async with fabrica() as s:
        mapa = await _clonar(s, destino, {"previo": "x"})
        await s.rollback()
    assert mapa["previo"] == "x"
    # 3 unidades + 5 personas + el tenant + el previo
    assert len(mapa) == 10


@pytest.mark.asyncio
async def test_las_personas_del_clon_son_propias(fabrica):
    await _sembrar(fabrica)
    d1, d2 = (f"demo-{uuid.uuid4().hex[:10]}" for _ in range(2))
    async with fabrica() as s:
        m1 = await _clonar(s, d1)
        m2 = await _clonar(s, d2)
        await s.rollback()
    usuarios = lambda m: {v for k, v in m.items() if v.startswith("usr-")}  # noqa: E731
    assert usuarios(m1) and not usuarios(m1) & usuarios(m2)
    assert not usuarios(m1) & {k for k in m1 if k.startswith("usr-")}


@pytest.mark.asyncio
async def test_personas_ficticias_con_rol_solo_por_user_tenant_roles(fabrica):
    await _sembrar(fabrica)
    destino = f"demo-{uuid.uuid4().hex[:10]}"
    async with fabrica() as s:
        mapa = await _clonar(s, destino)
        uids = {v for k, v in mapa.items() if k.startswith("usr-ep-")}
        filas = (await s.execute(text(
            "SELECT u.id, u.email, r.role, r.tenant_id FROM users u LEFT JOIN user_tenant_roles r "
            "ON r.user_id = u.id WHERE u.id = ANY(:ids)"), {"ids": list(uids)})).all()
        await s.rollback()
    assert len(uids) == 5
    assert all(email.endswith(".invalid") for _, email, _, _ in filas)
    assert all(tid == destino for _, _, _, tid in filas), "cada persona se relaciona solo con su tenant"
    por_persona: dict[str, list[str]] = {}
    for uid, _, rol, _ in filas:
        por_persona.setdefault(uid, []).append(rol)
    assert all(len(r) == 1 for r in por_persona.values())
    dpo = [r for r in por_persona.values() if r == ["dpo"]]
    assert len(dpo) == 1 and not ROLES_OPERATIVOS & set(dpo[0])


@pytest.mark.asyncio
async def test_clonar_dos_veces_no_duplica(fabrica):
    await _sembrar(fabrica)
    destino = f"demo-{uuid.uuid4().hex[:10]}"
    async with fabrica() as s:
        m1 = await _clonar(s, destino)
        e1 = await _estado(s, destino)
        n1 = (await s.execute(text("SELECT count(*) FROM users"))).scalar_one()
        m2 = await _clonar(s, destino)
        e2 = await _estado(s, destino)
        n2 = (await s.execute(text("SELECT count(*) FROM users"))).scalar_one()
        await s.rollback()
    assert m1 == m2 and _huella(e1) == _huella(e2) and n1 == n2


@pytest.mark.asyncio
async def test_el_clon_no_hace_commit(fabrica):
    await _sembrar(fabrica)
    destino = f"demo-{uuid.uuid4().hex[:10]}"
    async with fabrica() as s:
        await _clonar(s, destino)
        await s.rollback()
    async with fabrica() as s:
        assert (await s.execute(text("SELECT count(*) FROM tenants WHERE id = :t"), {"t": destino})).scalar_one() == 0


@pytest.mark.asyncio
async def test_con_rls_el_rol_de_app_del_destino_no_ve_la_plantilla(fabrica):
    await _sembrar(fabrica)
    destino = f"demo-{uuid.uuid4().hex[:10]}"
    async with fabrica() as s:
        await _clonar(s, destino)
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": destino})
        vistas = {
            "areas": (await s.execute(text("SELECT count(*) FROM areas WHERE tenant_id = :p"), {"p": TID})).scalar_one(),
            "user_tenant_roles": (await s.execute(
                text("SELECT count(*) FROM user_tenant_roles WHERE tenant_id = :p"), {"p": TID})).scalar_one(),
        }
        propias = (await s.execute(text("SELECT count(*) FROM areas WHERE tenant_id = :d"), {"d": destino})).scalar_one()
        await s.rollback()
    assert vistas == {"areas": 0, "user_tenant_roles": 0}
    assert propias == 3


# --- Frontera ADPA -----------------------------------------------------------------------------------

def test_el_motor_no_importa_la_sala_demo():
    arbol = ast.parse((RAIZ / "features/organizacion/services/clon_plantilla_engine.py").read_text(encoding="utf-8"))
    modulos = {n.module for n in ast.walk(arbol) if isinstance(n, ast.ImportFrom) and n.module}
    assert not {m for m in modulos if m.startswith(("features.demo", "app_core.pasillo"))}, modulos


def test_el_pasillo_solo_reexporta():
    fuente = (RAIZ / "app_core/pasillo/organizacion.py").read_text(encoding="utf-8")
    seccion = fuente.split("# === DEMO-03a ===")[1].split("# === fin DEMO-03a ===")[0]
    arbol = ast.parse(seccion)
    for fn in (n for n in arbol.body if isinstance(n, ast.AsyncFunctionDef)):
        cuerpo = [n for n in fn.body if not isinstance(n, ast.ImportFrom)]
        assert len(cuerpo) == 1, fn.name
