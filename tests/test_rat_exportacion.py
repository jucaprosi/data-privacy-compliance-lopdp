"""Árbitro de RAT-06 contra PostgreSQL. ¤rat ¤arbitro

Contrato: governance/especificaciones/RAT-06.md §5.

Mutación documentada, corrida el 2026-11-01: quitar `a.c.deleted_at.is_(None)` de `fichas_vigentes` hace fallar
`test_exportar_solo_vigentes`, porque aparece `RAT-BAJA` como cuarta fila.
"""
import hashlib
import os
import re
from io import BytesIO
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from api.errores import ErrorNegocio
from app_core.db.session import fijar_contexto_rls
from features.rat.services import exportacion_engine as motor

pytestmark = pytest.mark.asyncio

RUTA = "/api/v1/rat/exportar"
ROLES = ("dpo", "coordinador", "implementador", "admin_organizacion", "responsable_area")


@pytest_asyncio.fixture
async def env(db_engine):
    assert os.environ.get("TEST_DATABASE_URL")
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    ta, tb = f"ratx-{uuid4().hex}", f"ratx-{uuid4().hex}"
    usuarios = {r: f"ratx-u-{uuid4().hex}" for r in ROLES}
    usuario_b = f"ratx-u-{uuid4().hex}"
    try:
        async with factory() as s:
            for tenant in (ta, tb):
                await s.execute(text("INSERT INTO tenants (id,nombre_comercial,razon_social,ruc_identificacion) VALUES (:t,:t,:t,:t)"), {"t": tenant})
            for tenant, rol, usuario in [*((ta, r, u) for r, u in usuarios.items()), (tb, "coordinador", usuario_b)]:
                await s.execute(text("INSERT INTO users (id,email,nombre) VALUES (:u,:e,'RAT-06')"),
                                {"u": usuario, "e": f"{usuario}@example.test"})
                await fijar_contexto_rls(s, tenant, usuario)
                await s.execute(text("INSERT INTO user_tenant_roles (id,user_id,tenant_id,role) VALUES (:i,:u,:t,:r)"),
                                {"i": str(uuid4()), "u": usuario, "t": tenant, "r": rol})
            await s.commit()
        yield {"factory": factory, "a": ta, "b": tb, "usuarios": usuarios, "usuario_b": usuario_b}
    finally:
        async with factory() as s:
            for tenant in (ta, tb):
                await fijar_contexto_rls(s, tenant)
                for sql in ("DELETE FROM audit_events WHERE tenant_id=:t", "DELETE FROM rat_versiones WHERE tenant_id=:t",
                            "DELETE FROM hallazgos WHERE tenant_id=:t", "DELETE FROM rat_actividades WHERE tenant_id=:t",
                            "DELETE FROM user_tenant_roles WHERE tenant_id=:t", "DELETE FROM tenants WHERE id=:t"):
                    await s.execute(text(sql), {"t": tenant})
            for usuario in [*usuarios.values(), usuario_b]:
                await s.execute(text("DELETE FROM users WHERE id=:u"), {"u": usuario})
            await s.commit()


@pytest_asyncio.fixture
async def cliente(env):
    from api.routers.rat import get_rat_session, router as rat
    from api.routers.rat_exportacion import router as exportacion

    app = FastAPI()
    app.include_router(rat, prefix="/api/v1")
    app.include_router(exportacion, prefix="/api/v1")

    @app.exception_handler(ErrorNegocio)
    async def _negocio(_, exc: ErrorNegocio):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "code": exc.code})

    async def sesion(tenant: str = Header(..., alias="X-Tenant-ID"), usuario: str = Header(..., alias="X-User-ID")):
        async with env["factory"]() as s:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
            await fijar_contexto_rls(s, tenant, usuario)
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    app.dependency_overrides[get_rat_session] = sesion
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://rat.test") as c:
        yield c


def _h(env, rol="coordinador"):
    return {"X-Tenant-ID": env["a"], "X-User-ID": env["usuarios"][rol], "X-Role": rol}


async def _crear(cliente, env, codigo: str, **cambios) -> str:
    ficha = {"codigo": codigo, "nombre": f"Tratamiento {codigo}", "area_responsable": "Talento humano",
             "finalidad": "Nómina", "plazo_conservacion": "5 años", "categorias_datos": ["Identificación"], **cambios}
    r = await cliente.post("/api/v1/rat/actividades", json=ficha, headers=_h(env))
    assert r.status_code == 200, r.text
    return r.json()["actividad"]["id"]


def _filas(contenido: bytes) -> list[tuple]:
    return list(load_workbook(BytesIO(contenido)).active.iter_rows(values_only=True))


async def test_exportar_solo_vigentes(cliente, env):
    for codigo in ("RAT-1", "RAT-2", "RAT-3"):
        await _crear(cliente, env, codigo)
    baja = await _crear(cliente, env, "RAT-BAJA")
    assert (await cliente.delete(f"/api/v1/rat/actividades/{baja}", headers=_h(env))).status_code == 200

    r = await cliente.get(RUTA, params={"formato": "xlsx"}, headers=_h(env))
    assert r.status_code == 200, r.text
    filas = _filas(r.content)
    assert filas[0] == tuple(titulo for _, titulo in motor.COLUMNAS)
    assert [f[0] for f in filas[1:]] == ["RAT-1", "RAT-2", "RAT-3"]
    assert r.headers["content-type"] == motor.MEDIA_XLSX


async def test_exportar_huella(cliente, env):
    await _crear(cliente, env, "RAT-1")
    capturado = {}
    original = motor.generar_xlsx

    def espia(fichas):
        capturado["xlsx"] = original(fichas)
        return capturado["xlsx"]

    motor.generar_xlsx = espia
    try:
        r = await cliente.get(RUTA, params={"formato": "pdf"}, headers=_h(env))
    finally:
        motor.generar_xlsx = original
    assert r.status_code == 200, r.text
    huella = hashlib.sha256(capturado["xlsx"]).hexdigest()
    pdf = PdfReader(BytesIO(r.content))
    assert all(huella in pagina.extract_text() for pagina in pdf.pages)
    assert huella in pdf.metadata.subject and pdf.metadata["/Keywords"] == huella
    assert r.headers["x-huella-sha256"] == huella
    assert "Tratamiento RAT-1" in pdf.pages[0].extract_text()


async def test_exportar_huella_del_xlsx_descargado(cliente, env):
    await _crear(cliente, env, "RAT-1")
    r = await cliente.get(RUTA, params={"formato": "xlsx"}, headers=_h(env))
    assert r.headers["x-huella-sha256"] == hashlib.sha256(r.content).hexdigest()


async def test_exportar_vacio(cliente, env):
    r = await cliente.get(RUTA, params={"formato": "xlsx"}, headers=_h(env))
    assert r.status_code == 409 and r.json()["code"] == "RAT_VACIO"


async def test_exportar_version_es_la_ultima_de_rat_versiones(cliente, env):
    rid = await _crear(cliente, env, "RAT-1")
    await cliente.patch(f"/api/v1/rat/actividades/{rid}", json={"nombre": "Otro"}, headers=_h(env))
    # La columna `version` de la ficha se aleja a propósito: manda rat_versiones.
    async with env["factory"]() as s:
        await fijar_contexto_rls(s, env["a"])
        await s.execute(text("UPDATE rat_actividades SET version=9 WHERE id=:i"), {"i": rid})
        await s.commit()
    filas = _filas((await cliente.get(RUTA, params={"formato": "xlsx"}, headers=_h(env))).content)
    fila = dict(zip(filas[0], filas[1]))
    assert fila["Versión"] == 2 and fila["Fecha de la versión"]


async def test_ficha_sin_versiones_se_exporta_sin_numero(cliente, env):
    rid = await _crear(cliente, env, "RAT-ANTIGUA")
    async with env["factory"]() as s:
        await fijar_contexto_rls(s, env["a"])
        await s.execute(text("DELETE FROM rat_versiones WHERE tratamiento_id=:i"), {"i": rid})
        await s.commit()
    filas = _filas((await cliente.get(RUTA, params={"formato": "xlsx"}, headers=_h(env))).content)
    assert dict(zip(filas[0], filas[1]))["Versión"] == motor.SIN_VERSION


async def test_sin_datos_de_personas_ni_identificadores(cliente, env):
    await _crear(cliente, env, "RAT-1", observaciones_dpo="Ana Pérez, cédula 1712345678")
    r = await cliente.get(RUTA, params={"formato": "xlsx"}, headers=_h(env))
    filas = _filas(r.content)
    campos = {campo for campo, _ in motor.COLUMNAS}
    assert not campos & {"observaciones_dpo", "tenant_id", "id", "creado_por", "origen"}
    assert "Ana Pérez" not in str(filas) and env["a"] not in str(filas)
    assert env["usuarios"]["coordinador"] not in str(filas)


async def test_formulas_no_se_ejecutan(cliente, env):
    await _crear(cliente, env, "RAT-1", nombre='=HYPERLINK("http://malo.test")', finalidad="+1+1",
                 area_responsable="-2", plazo_conservacion="@SUMA(A1)", categorias_datos=["=1+1"])
    r = await cliente.get(RUTA, params={"formato": "xlsx"}, headers=_h(env))
    hoja = load_workbook(BytesIO(r.content)).active
    celdas = [c for c in hoja[2] if isinstance(c.value, str) and c.value[1:2] in ("=", "+", "-", "@")]
    assert len(celdas) == 5
    assert all(c.data_type == "s" and c.value.startswith("'") for c in celdas)
    assert not any(c.data_type == "f" for c in hoja[2])


async def test_saneado_de_celda_y_marcado_del_pdf(cliente, env):
    assert motor.celda_segura("  =1+1") == "'  =1+1"
    assert motor.celda_segura("texto\x01 limpio") == "texto limpio"
    await _crear(cliente, env, "RAT-1", nombre="<b>A & B</para>\x01")
    r = await cliente.get(RUTA, params={"formato": "pdf"}, headers=_h(env))
    assert r.status_code == 200, r.text
    assert "<b>A & B</para>" in PdfReader(BytesIO(r.content)).pages[0].extract_text()


@pytest.mark.parametrize("tenant", ['a"; filename="x.exe', "a\r\nSet-Cookie: x=1", "../../etc", "ñandú 1", '"""'])
async def test_nombre_de_archivo_saneado(tenant):
    nombre = motor.nombre_archivo(tenant, "2026-11-01", "xlsx")
    assert re.fullmatch(r"rat-[A-Za-z0-9_-]+-2026-11-01\.xlsx", nombre)


async def test_cabeceras_y_formato(cliente, env):
    await _crear(cliente, env, "RAT-1")
    r = await cliente.get(RUTA, params={"formato": "xlsx"}, headers=_h(env))
    assert r.headers["content-disposition"].startswith(f'attachment; filename="rat-{env["a"]}-')
    assert (await cliente.get(RUTA, params={"formato": "csv"}, headers=_h(env))).status_code == 422


async def test_otra_organizacion_no_ve_las_fichas(cliente, env):
    await _crear(cliente, env, "RAT-1")
    ajeno = {"X-Tenant-ID": env["b"], "X-User-ID": env["usuario_b"], "X-Role": "coordinador"}
    r = await cliente.get(RUTA, params={"formato": "xlsx"}, headers=ajeno)
    assert r.status_code == 409 and r.json()["code"] == "RAT_VACIO"


async def test_roles(cliente, env):
    await _crear(cliente, env, "RAT-1")
    for rol in ("implementador", "coordinador", "dpo", "admin_organizacion"):
        assert (await cliente.get(RUTA, params={"formato": "xlsx"}, headers=_h(env, rol))).status_code == 200
    assert (await cliente.get(RUTA, params={"formato": "xlsx"}, headers=_h(env, "responsable_area"))).status_code == 403


async def test_exportacion_queda_auditada(cliente, env):
    await _crear(cliente, env, "RAT-1")
    r = await cliente.get(RUTA, params={"formato": "pdf"}, headers=_h(env))
    async with env["factory"]() as s:
        await fijar_contexto_rls(s, env["a"])
        total = await s.execute(
            text("SELECT count(*) FROM audit_events WHERE tenant_id=:t AND entity_type='rat_exportacion' AND entity_id=:h"),
            {"t": env["a"], "h": r.headers["x-huella-sha256"]},
        )
        assert total.scalar_one() == 1
