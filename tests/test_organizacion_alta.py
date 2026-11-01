# ¤rbac-tenant
# ¤arbitro
"""Árbitro de ORG-16: alta de la organización en siete pasos.

Valida (contrato: governance/especificaciones/ORG-16.md §5):
1. Los pasos 1 y 3 guardados en el servidor se leen desde otra sesión (cliente nuevo).
2. El `dpo` no escribe (403) pero sí lee el estado.
3. Repetir el paso 3 no duplica áreas.
4. Una persona `dpo` que ya es `coordinador` se rechaza con DPO_INDEPENDENCE_VIOLATED.
5. Las sugerencias son solo estructura del catálogo.
6. Personas clave: ningún campo de identificación; la tabla aísla por organización con lopdp_app.

Las pruebas de validación pura no tocan la BD; las de integración necesitan TEST_DATABASE_URL (rama
Neon propia) y se omiten sin ella. Las que dependen de la migración 20261101_org16_perfil_alta se
omiten, con motivo explícito, mientras esa migración no esté aplicada en la rama. Datos ficticios:
correos con el dominio reservado .test.
"""
from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from features.organizacion.services.alta_engine import (
    PASOS,
    SUGERENCIAS_POR_SECTOR,
    PasoPersonas,
    PasoPerfil,
    _clave_sector,
)
from main import app

RUTA = "/api/v1/organizacion/alta"
PERFIL = {
    "razon_social": "Organización Ficticia de Prueba S.A.",
    "ruc": "1790000000001",  # solo para validación pura; las pruebas con base usan _perfil()
    "sector": "salud",
    "tamano": "pequena",
    "naturaleza": "privada",
    "rol_datos": "responsable",
    "actividades_riesgo": ["Datos de salud"],
}


def _perfil() -> dict:
    """Perfil con un RUC de 13 dígitos único por ejecución (la columna es única en toda la base)."""
    return {**PERFIL, "ruc": f"{uuid.uuid4().int % 10**13:013d}"}


AREAS = {"areas": [{"nombre": "Administración", "codigo": "ADM"}, {"nombre": "Atención"}]}


# ---------------------------------------------------------------- validación pura (sin BD)

def test_siete_pasos_en_orden():
    assert PASOS == ("perfil", "sedes", "areas", "tratamientos", "terceros", "personas", "resumen")


def test_personas_no_admite_campos_de_identificacion():
    persona = {"nombre": "Persona Ficticia", "cargo": "Gerente", "email": "p@organizacion.test", "rol": "coordinador"}
    PasoPersonas.model_validate({"personas": [persona]})
    for campo in ("cedula", "identificacion", "ruc"):
        with pytest.raises(ValidationError):
            PasoPersonas.model_validate({"personas": [{**persona, campo: "3000000004"}]})


@pytest.mark.parametrize("ruc", ["123", "17900000000012", "17900000000a1", ""])
def test_ruc_debe_tener_trece_digitos(ruc):
    with pytest.raises(ValidationError):
        PasoPerfil.model_validate({**PERFIL, "ruc": ruc})


def test_enumerados_cerrados():
    for campo, valor in (("tamano", "gigante"), ("naturaleza", "otra"), ("rol_datos", "nadie")):
        with pytest.raises(ValidationError):
            PasoPerfil.model_validate({**PERFIL, campo: valor})


def test_sin_sector_no_hay_catalogo_y_sector_desconocido_usa_general():
    assert _clave_sector(None) is None and _clave_sector("  ") is None
    assert _clave_sector("Servicios de Salud") == "salud"
    assert _clave_sector("Minería") == "general"


def test_catalogo_solo_estructura():
    permitidas_trat = {"nombre", "finalidad", "base_legal"}
    permitidas_terc = {"tipo", "descripcion"}
    for catalogo in SUGERENCIAS_POR_SECTOR.values():
        assert all(set(t) == permitidas_trat for t in catalogo["tratamientos"])
        assert all(set(t) == permitidas_terc for t in catalogo["terceros"])


# ------------------------------------------------------------------------------- integración

def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Sin TEST_DATABASE_URL: la parte de BD de ORG-16 queda no verificada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def factory():
    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    yield async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    await engine.dispose()


async def _migracion_aplicada(factory) -> bool:
    async with factory() as s:
        return (await s.execute(text(
            "SELECT count(*) FROM information_schema.columns "
            "WHERE table_name = 'tenants' AND column_name = 'naturaleza'"
        ))).scalar_one() == 1


@pytest_asyncio.fixture
async def requiere_migracion(factory):
    if not await _migracion_aplicada(factory):
        pytest.skip("Migración 20261101_org16_perfil_alta no aplicada en la rama de pruebas")


@pytest_asyncio.fixture
async def dos_organizaciones(factory):
    """Organización A (admin, implementador, dpo, coordinador) y B (su admin)."""
    sufijo = uuid.uuid4().hex[:8]
    ta, tb = f"t16a-{sufijo}", f"t16b-{sufijo}"
    u = {n: f"u16{n}-{sufijo}" for n in ("admin", "impl", "dpo", "coord", "badmin")}
    roles = (
        (u["admin"], ta, "admin_organizacion"), (u["impl"], ta, "implementador"),
        (u["dpo"], ta, "dpo"), (u["coord"], ta, "coordinador"), (u["badmin"], tb, "admin_organizacion"),
    )
    async with factory() as s:
        for tid in (ta, tb):
            await s.execute(
                text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                     "VALUES (:id, :nom, :razon, :ruc)"),
                {"id": tid, "nom": f"Org {tid}", "razon": f"Org Ficticia {tid} S.A.", "ruc": f"RUC{tid[:10]}"},
            )
        for uid in u.values():
            await s.execute(
                text("INSERT INTO users (id, email, nombre) VALUES (:id, :email, :nombre)"),
                {"id": uid, "email": f"{uid}@organizacion.test", "nombre": f"Usuario ficticio {uid}"},
            )
        for uid, tid, rol in roles:
            await s.execute(
                text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, :r)"),
                {"id": f"r16-{uuid.uuid4().hex[:8]}", "u": uid, "t": tid, "r": rol},
            )
        await s.commit()

    yield {"ta": ta, "tb": tb, **u}

    async with factory() as s:
        ids = {"a": ta, "b": tb}
        for tabla in ("rat_actividades", "invitaciones_personas", "audit_events", "user_tenant_roles", "areas"):
            try:
                async with s.begin_nested():
                    await s.execute(text(f"DELETE FROM {tabla} WHERE tenant_id IN (:a, :b)"), ids)  # noqa: S608
            except Exception:  # la tabla puede no existir si la migración no se aplicó
                pass
        await s.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": list(u.values())})
        await s.execute(text("DELETE FROM tenants WHERE id IN (:a, :b)"), ids)
        await s.commit()


def _cab(tenant: str, usuario: str, rol: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant, "X-User-ID": usuario, "X-Role": rol}


async def _fijar_tamano_y_sector(factory, tenant: str, tamano="pequena", sector="salud"):
    async with factory() as s:
        await s.execute(text("UPDATE tenants SET tamano=:z, sector=:s WHERE id=:t"),
                        {"z": tamano, "s": sector, "t": tenant})
        await s.commit()


@pytest.mark.asyncio
async def test_alta_persiste_en_servidor(dos_organizaciones, requiere_migracion):
    o = dos_organizaciones
    cab = _cab(o["ta"], o["admin"], "admin_organizacion")
    assert TestClient(app).get(RUTA, headers=cab).json()["completo"] is False
    assert TestClient(app).post(f"{RUTA}/paso/perfil", json=_perfil(), headers=cab).status_code == 200
    assert TestClient(app).post(f"{RUTA}/paso/areas", json=AREAS, headers=cab).status_code == 200
    # «Otro navegador»: cliente nuevo, sin estado compartido, otro rol de lectura.
    otra_sesion = TestClient(app)
    r = otra_sesion.get(RUTA, headers=_cab(o["ta"], o["dpo"], "dpo"))
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["completo"] is True
    assert {p["id"]: p["completo"] for p in cuerpo["pasos"]}["perfil"] is True
    assert {p["id"]: p["completo"] for p in cuerpo["pasos"]}["areas"] is True
    # La otra organización sigue sin alta.
    assert otra_sesion.get(RUTA, headers=_cab(o["tb"], o["badmin"], "admin_organizacion")).json()["completo"] is False


@pytest.mark.asyncio
async def test_alta_dpo_no_escribe(dos_organizaciones, factory):
    o = dos_organizaciones
    for rol, uid in (("dpo", o["dpo"]), ("coordinador", o["coord"])):
        r = TestClient(app).post(f"{RUTA}/paso/perfil", json=_perfil(), headers=_cab(o["ta"], uid, rol))
        assert r.status_code == 403
    if not await _migracion_aplicada(factory):
        pytest.skip("Migración 20261101_org16_perfil_alta no aplicada: el estado del alta lee invitaciones_personas")
    assert TestClient(app).get(RUTA, headers=_cab(o["ta"], o["dpo"], "dpo")).status_code == 200


@pytest.mark.asyncio
async def test_alta_idempotente(dos_organizaciones, factory):
    o = dos_organizaciones
    cab = _cab(o["ta"], o["impl"], "implementador")
    for _ in range(2):
        assert TestClient(app).post(f"{RUTA}/paso/areas", json=AREAS, headers=cab).status_code == 200
    async with factory() as s:
        n = (await s.execute(
            text("SELECT count(*) FROM areas WHERE tenant_id=:t AND deleted_at IS NULL AND nombre='Administración'"),
            {"t": o["ta"]},
        )).scalar_one()
    assert n == 1


@pytest.mark.asyncio
async def test_alta_dpo_exclusivo(dos_organizaciones, factory, requiere_migracion):
    o = dos_organizaciones
    await _fijar_tamano_y_sector(factory, o["ta"])
    cab = _cab(o["ta"], o["admin"], "admin_organizacion")
    persona = {"nombre": "Persona Ficticia", "cargo": "Delegado", "email": f"{o['coord']}@organizacion.test", "rol": "dpo"}
    r = TestClient(app).post(f"{RUTA}/paso/personas", json={"personas": [persona]}, headers=cab)
    assert r.status_code == 409
    assert r.json()["code"] == "DPO_INDEPENDENCE_VIOLATED"
    # Mismo correo con dos roles incompatibles en el mismo envío.
    nuevo = "nuevo-16@organizacion.test"
    lote = [{**persona, "email": nuevo}, {**persona, "email": nuevo, "rol": "coordinador"}]
    r = TestClient(app).post(f"{RUTA}/paso/personas", json={"personas": lote}, headers=cab)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_alta_personas_antes_del_perfil(dos_organizaciones, requiere_migracion):
    o = dos_organizaciones
    persona = {"nombre": "Persona Ficticia", "cargo": "Jefa", "email": "a-16@organizacion.test", "rol": "coordinador"}
    r = TestClient(app).post(f"{RUTA}/paso/personas", json={"personas": [persona]},
                             headers=_cab(o["ta"], o["admin"], "admin_organizacion"))
    assert r.status_code == 409
    assert r.json()["code"] == "TENANT_SIZE_NOT_CONFIGURED"


@pytest.mark.asyncio
async def test_alta_personas_se_guardan_y_repetir_no_duplica(dos_organizaciones, factory, requiere_migracion):
    o = dos_organizaciones
    await _fijar_tamano_y_sector(factory, o["ta"])
    cab = _cab(o["ta"], o["admin"], "admin_organizacion")
    persona = {"nombre": "Persona Ficticia", "cargo": "Jefa", "email": "b-16@organizacion.test", "rol": "coordinador"}
    for cargo in ("Jefa", "Directora"):
        r = TestClient(app).post(f"{RUTA}/paso/personas", json={"personas": [{**persona, "cargo": cargo}]}, headers=cab)
        assert r.status_code == 200
    async with factory() as s:
        filas = (await s.execute(
            text("SELECT cargo FROM invitaciones_personas WHERE tenant_id=:t"), {"t": o["ta"]},
        )).scalars().all()
    assert filas == ["Directora"]


@pytest.mark.asyncio
async def test_alta_persona_rechaza_cedula(dos_organizaciones, factory):
    o = dos_organizaciones
    await _fijar_tamano_y_sector(factory, o["ta"])
    persona = {"nombre": "Persona Ficticia", "cargo": "Jefa", "email": "c-16@organizacion.test",
               "rol": "coordinador", "cedula": "3000000004"}
    r = TestClient(app).post(f"{RUTA}/paso/personas", json={"personas": [persona]},
                             headers=_cab(o["ta"], o["admin"], "admin_organizacion"))
    assert r.status_code == 422
    assert r.json()["code"] == "PASO_INVALIDO"


@pytest.mark.asyncio
async def test_alta_sugerencias_solo_estructura(dos_organizaciones, factory):
    o = dos_organizaciones
    cab = _cab(o["ta"], o["admin"], "admin_organizacion")
    vacio = TestClient(app).get(f"{RUTA}/sugerencias", headers=cab).json()
    assert vacio == {"tratamientos": [], "terceros": []}
    await _fijar_tamano_y_sector(factory, o["ta"], sector="salud")
    r = TestClient(app).get(f"{RUTA}/sugerencias", headers=cab).json()
    assert [t["nombre"] for t in r["tratamientos"]] == [t["nombre"] for t in SUGERENCIAS_POR_SECTOR["salud"]["tratamientos"]]
    assert all(set(t) == {"indice", "nombre", "finalidad", "base_legal"} for t in r["tratamientos"])
    assert all(set(t) == {"indice", "tipo", "descripcion"} for t in r["terceros"])
    assert TestClient(app).get(f"{RUTA}/sugerencias", headers=_cab(o["ta"], o["dpo"], "dpo")).status_code == 403


@pytest.mark.asyncio
async def test_alta_tratamientos_se_guardan_como_plantilla_y_no_duplican(dos_organizaciones, factory):
    o = dos_organizaciones
    await _fijar_tamano_y_sector(factory, o["ta"], sector="salud")
    cab = _cab(o["ta"], o["admin"], "admin_organizacion")
    cuerpo = {"aceptados": [0, 1], "ajustes": [{"indice": 1, "nombre": "Historia clínica propia"}]}
    for _ in range(2):
        assert TestClient(app).post(f"{RUTA}/paso/tratamientos", json=cuerpo, headers=cab).status_code == 200
    async with factory() as s:
        filas = (await s.execute(
            text("SELECT nombre, origen FROM rat_actividades WHERE tenant_id=:t ORDER BY codigo"), {"t": o["ta"]},
        )).all()
    assert len(filas) == 2
    assert {origen for _, origen in filas} == {"plantilla:alta-salud"}
    assert "Historia clínica propia" in {nombre for nombre, _ in filas}
    if not await _migracion_aplicada(factory):
        pytest.skip("Migración 20261101_org16_perfil_alta no aplicada: el estado del alta lee invitaciones_personas")
    estado = TestClient(app).get(RUTA, headers=cab).json()
    assert {p["id"]: p["completo"] for p in estado["pasos"]}["tratamientos"] is True


@pytest.mark.asyncio
async def test_alta_errores_de_paso(dos_organizaciones, factory):
    o = dos_organizaciones
    cab = _cab(o["ta"], o["admin"], "admin_organizacion")
    r = TestClient(app).post(f"{RUTA}/paso/inexistente", json={}, headers=cab)
    assert (r.status_code, r.json()["code"]) == (422, "PASO_DESCONOCIDO")
    r = TestClient(app).post(f"{RUTA}/paso/terceros", json={"aceptados": [0]}, headers=cab)
    assert (r.status_code, r.json()["code"]) == (501, "PASO_NO_DISPONIBLE")
    if not await _migracion_aplicada(factory):
        pytest.skip("Migración 20261101_org16_perfil_alta no aplicada: el estado del alta lee invitaciones_personas")
    r = TestClient(app).post(f"{RUTA}/paso/resumen", json={}, headers=cab)
    assert (r.status_code, r.json()["code"]) == (409, "PASO_PREVIO_INCOMPLETO")


@pytest.mark.asyncio
async def test_invitaciones_personas_aisla_por_organizacion_con_lopdp_app(dos_organizaciones, factory, requiere_migracion):
    """RLS real con el rol de aplicación: una organización no ve las personas de la otra."""
    o = dos_organizaciones
    async with factory() as s:
        for tid, uid, mail in ((o["ta"], o["admin"], "x-a@organizacion.test"), (o["tb"], o["badmin"], "x-b@organizacion.test")):
            await s.execute(
                text("INSERT INTO invitaciones_personas (id, tenant_id, nombre, cargo, email, rol_propuesto, created_by) "
                     "VALUES (:id, :t, 'Persona Ficticia', 'Cargo', :m, 'coordinador', :u)"),
                {"id": f"ip-{uuid.uuid4().hex[:8]}", "t": tid, "m": mail, "u": uid},
            )
        await s.commit()
    async with factory() as s:
        if not (await s.execute(text("SELECT 1 FROM pg_roles WHERE rolname='lopdp_app'"))).first():
            pytest.skip("Rol lopdp_app no existe en la rama de pruebas")
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": o["ta"]})
        correos = (await s.execute(text("SELECT email FROM invitaciones_personas"))).scalars().all()
        assert correos == ["x-a@organizacion.test"]
        with pytest.raises(Exception):
            await s.execute(
                text("INSERT INTO invitaciones_personas (id, tenant_id, nombre, cargo, email, rol_propuesto, created_by) "
                     "VALUES ('ip-cruzada', :t, 'P', 'C', 'y@organizacion.test', 'dpo', 'u')"),
                {"t": o["tb"]},
            )
        await s.rollback()
