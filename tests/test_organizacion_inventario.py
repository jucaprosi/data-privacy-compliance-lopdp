# ¤rbac-tenant
# ¤arbitro
"""Árbitro de ORG-17: inventario de activos, soportes y personas mínimas.

Valida (contrato: governance/tareas/ORG-17.md):
1. Validación pura: tipos cerrados, cuerpos sin organización ni campos ajenos.
2. Lo creado por un rol se lee desde otra sesión; el `dpo` lee pero no escribe (403).
3. Una organización nunca ve ni toca el inventario de otra (HTTP y RLS como lopdp_app).
4. La cédula se guarda cifrada, nunca se devuelve y no se acepta si es inválida o sin clave.
5. Los vínculos con tratamientos solo admiten tratamientos del RAT de la propia organización.
6. lopdp_app no puede borrar activos ni personas (se archivan).

Las pruebas de integración necesitan TEST_DATABASE_URL (PostgreSQL 16 local, 127.0.0.1) y se omiten sin
ella. Datos ficticios: correos con el dominio reservado .invalid.
"""
from __future__ import annotations

import base64
import os
import re
import uuid

import pytest
import pytest_asyncio
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app_core.db.session import get_session
from features.organizacion.organizacion_service import (
    ActivoCrear,
    ActivoEditar,
    PersonaCrear,
    VinculosTratamientos,
)
from main import app

RUTA = "/api/v1/organizacion/inventario"
CEDULA_VALIDA = "1710034065"


# ---------------------------------------------------------------- validación pura (sin BD)

def test_tipos_de_activo_cerrados():
    for tipo in ("sistema", "soporte_fisico", "soporte_digital"):
        ActivoCrear.model_validate({"tipo": tipo, "nombre": "Elemento ficticio"})
    with pytest.raises(ValidationError):
        ActivoCrear.model_validate({"tipo": "otro", "nombre": "Elemento ficticio"})


def test_cuerpos_no_admiten_organizacion_ni_campos_ajenos():
    for cuerpo in ({"tipo": "sistema", "nombre": "X", "tenant_id": "t"}, {"tipo": "sistema", "nombre": "X", "created_by": "u"}):
        with pytest.raises(ValidationError):
            ActivoCrear.model_validate(cuerpo)
    with pytest.raises(ValidationError):
        ActivoEditar.model_validate({"tipo": "soporte_fisico"})
    with pytest.raises(ValidationError):
        VinculosTratamientos.model_validate({"tratamiento_ids": [], "tenant_id": "t"})


def test_persona_exige_correo_y_no_admite_identificaciones_distintas_de_cedula():
    base = {"nombre": "Persona Ficticia", "cargo": "Gerente", "email": "p@organizacion.invalid"}
    PersonaCrear.model_validate(base)
    for email in ("sin-arroba", "a@b", ""):
        with pytest.raises(ValidationError):
            PersonaCrear.model_validate({**base, "email": email})
    for campo in ("ruc", "identificacion", "tenant_id"):
        with pytest.raises(ValidationError):
            PersonaCrear.model_validate({**base, campo: "x"})


# ------------------------------------------------------------------------------- integración

def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Sin TEST_DATABASE_URL: la parte de BD de ORG-17 queda no verificada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def factory():
    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    yield async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    await engine.dispose()


@pytest.fixture
def clave_cifrado(monkeypatch):
    monkeypatch.setenv("INVENTARIO_CLAVE_CIFRADO", Fernet.generate_key().decode("ascii"))


@pytest_asyncio.fixture
async def dos_organizaciones(factory):
    """Organización A (admin, coordinador, dpo, responsable_area) y B (su admin)."""
    async def _sesion_de_prueba():
        async with factory() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    guardado = dict(app.dependency_overrides)
    app.dependency_overrides[get_session] = _sesion_de_prueba

    sufijo = uuid.uuid4().hex[:8]
    ta, tb = f"t17a-{sufijo}", f"t17b-{sufijo}"
    u = {n: f"u17{n}-{sufijo}" for n in ("admin", "coord", "dpo", "resp", "badmin")}
    roles = (
        (u["admin"], ta, "admin_organizacion"), (u["coord"], ta, "coordinador"), (u["dpo"], ta, "dpo"),
        (u["resp"], ta, "responsable_area"), (u["badmin"], tb, "admin_organizacion"),
    )
    area_a, area_b = f"ar17a-{sufijo}", f"ar17b-{sufijo}"
    async with factory() as s:
        for tid in (ta, tb):
            await s.execute(
                text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                     "VALUES (:id, :nom, :razon, :ruc)"),
                {"id": tid, "nom": f"Org {tid}", "razon": f"Org Ficticia {tid} S.A.", "ruc": f"RUC{tid[:10]}"},
            )
        for tid, aid in ((ta, area_a), (tb, area_b)):
            await s.execute(
                text("INSERT INTO areas (id, tenant_id, nombre) VALUES (:id, :t, :n)"),
                {"id": aid, "t": tid, "n": f"Área {aid}"},
            )
        for uid in u.values():
            await s.execute(
                text("INSERT INTO users (id, email, nombre) VALUES (:id, :email, :nombre)"),
                {"id": uid, "email": f"{uid}@organizacion.invalid", "nombre": f"Usuario ficticio {uid}"},
            )
        for uid, tid, rol in roles:
            await s.execute(
                text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, :r)"),
                {"id": f"r17-{uuid.uuid4().hex[:8]}", "u": uid, "t": tid, "r": rol},
            )
        await s.commit()

    yield {"ta": ta, "tb": tb, "area_a": area_a, "area_b": area_b, **u}

    ids = {"a": ta, "b": tb}
    async with factory() as s:
        await s.execute(text("DELETE FROM inventario_activos_tratamientos WHERE tenant_id IN (:a, :b)"), ids)
        await s.execute(text("DELETE FROM inventario_activos WHERE tenant_id IN (:a, :b)"), ids)
        await s.execute(text("DELETE FROM inventario_personas WHERE tenant_id IN (:a, :b)"), ids)
        await s.execute(text("DELETE FROM rat_actividades WHERE tenant_id IN (:a, :b)"), ids)
        await s.execute(text("DELETE FROM audit_events WHERE tenant_id IN (:a, :b)"), ids)
        await s.execute(text("DELETE FROM user_tenant_roles WHERE tenant_id IN (:a, :b)"), ids)
        await s.execute(text("DELETE FROM areas WHERE tenant_id IN (:a, :b)"), ids)
        await s.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": list(u.values())})
        await s.execute(text("DELETE FROM tenants WHERE id IN (:a, :b)"), ids)
        await s.commit()

    app.dependency_overrides.clear()
    app.dependency_overrides.update(guardado)


def _cab(tenant: str, usuario: str, rol: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant, "X-User-ID": usuario, "X-Role": rol}


def _cli() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _sembrar_tratamiento(factory, tenant: str, codigo: str) -> str:
    rat_id = str(uuid.uuid4())
    async with factory() as s:
        await s.execute(
            text(
                "INSERT INTO rat_actividades (id, tenant_id, codigo, nombre, area_responsable, finalidad, "
                "base_legal, medio_soporte, pais_transferencia, plazo_conservacion, nivel_riesgo, "
                "observaciones_dpo, origen, categorias_titulares, categorias_datos, encargados, "
                "destinatarios, medidas_seguridad, datos_sensibles, transferencia_internacional, "
                "requiere_eipd, es_gran_escala, decisiones_automatizadas, volumen_titulares_estimado, "
                "volumen_titulares_12_meses, version) "
                "VALUES (:id, :t, :codigo, 'Tratamiento ficticio', 'Área', 'Finalidad', 'CUMPLIMIENTO_CONTRATO', 'Digital', "
                "'Ecuador', '1 año', 'BAJO', '', 'manual', '[]', '[]', '[]', '[]', '[]', false, false, false, "
                "false, false, 0, 0, 1)"
            ),
            {"id": rat_id, "t": tenant, "codigo": codigo},
        )
        await s.commit()
    return rat_id


@pytest.mark.asyncio
async def test_activo_creado_se_lee_desde_otra_sesion_y_el_dpo_no_escribe(dos_organizaciones):
    o = dos_organizaciones
    cab = _cab(o["ta"], o["admin"], "admin_organizacion")
    async with _cli() as c:
        r = await c.post(f"{RUTA}/activos", json={"tipo": "sistema", "nombre": "Sistema ficticio", "area_id": o["area_a"]}, headers=cab)
        assert r.status_code == 201
        activo_id = r.json()["id"]
    async with _cli() as otra:
        lista = (await otra.get(f"{RUTA}/activos", headers=_cab(o["ta"], o["dpo"], "dpo"))).json()
        assert [a["id"] for a in lista] == [activo_id]
        assert (await otra.get(f"{RUTA}/activos?tipo=soporte_fisico", headers=_cab(o["ta"], o["dpo"], "dpo"))).json() == []
        for rol, uid in (("dpo", o["dpo"]), ("responsable_area", o["resp"])):
            r = await otra.post(f"{RUTA}/activos", json={"tipo": "sistema", "nombre": "Otro"}, headers=_cab(o["ta"], uid, rol))
            assert r.status_code == 403
        assert (await otra.post(f"{RUTA}/activos", json={"tipo": "soporte_digital", "nombre": "Copia"}, headers=_cab(o["ta"], o["coord"], "coordinador"))).status_code == 201


@pytest.mark.asyncio
async def test_aislamiento_entre_organizaciones_por_http(dos_organizaciones):
    o = dos_organizaciones
    async with _cli() as c:
        activo = (await c.post(f"{RUTA}/activos", json={"tipo": "sistema", "nombre": "Solo de A"}, headers=_cab(o["ta"], o["admin"], "admin_organizacion"))).json()["id"]
        cab_b = _cab(o["tb"], o["badmin"], "admin_organizacion")
        assert (await c.get(f"{RUTA}/activos", headers=cab_b)).json() == []
        assert (await c.patch(f"{RUTA}/activos/{activo}", json={"nombre": "Robado"}, headers=cab_b)).status_code == 404
        # Un área de otra organización no es referencia válida.
        r = await c.post(f"{RUTA}/activos", json={"tipo": "sistema", "nombre": "X", "area_id": o["area_a"]}, headers=cab_b)
        assert r.status_code == 422


@pytest.mark.asyncio
async def test_duplicado_y_archivado(dos_organizaciones):
    o = dos_organizaciones
    cab = _cab(o["ta"], o["admin"], "admin_organizacion")
    async with _cli() as c:
        cuerpo = {"tipo": "soporte_fisico", "nombre": "Archivo central"}
        activo = (await c.post(f"{RUTA}/activos", json=cuerpo, headers=cab)).json()["id"]
        assert (await c.post(f"{RUTA}/activos", json={**cuerpo, "nombre": "ARCHIVO CENTRAL"}, headers=cab)).status_code == 409
        assert (await c.patch(f"{RUTA}/activos/{activo}", json={"archivado": True}, headers=cab)).status_code == 200
        lista = (await c.get(f"{RUTA}/activos", headers=cab)).json()
        assert lista[0]["archivado"] is True and lista[0]["nombre"] == "Archivo central"


@pytest.mark.asyncio
async def test_cedula_cifrada_nunca_devuelta(dos_organizaciones, factory, clave_cifrado):
    o = dos_organizaciones
    cab = _cab(o["ta"], o["admin"], "admin_organizacion")
    persona = {"nombre": "Persona Ficticia", "cargo": "Gerente", "email": "p@organizacion.invalid", "area_id": o["area_a"]}
    async with _cli() as c:
        assert (await c.post(f"{RUTA}/personas", json={**persona, "cedula": "1234567890"}, headers=cab)).status_code == 422
        r = await c.post(f"{RUTA}/personas", json={**persona, "cedula": CEDULA_VALIDA}, headers=cab)
        assert r.status_code == 201
        assert (await c.post(f"{RUTA}/personas", json={**persona, "email": "P@ORGANIZACION.INVALID"}, headers=cab)).status_code == 409
        lista = (await c.get(f"{RUTA}/personas", headers=cab)).json()
        assert lista[0]["tiene_cedula"] is True
        assert CEDULA_VALIDA not in str(lista) and "cedula" not in {k for k in lista[0] if k != "tiene_cedula"}
    async with factory() as s:
        guardado = (await s.execute(
            text("SELECT cedula_cifrada FROM inventario_personas WHERE tenant_id = :t"), {"t": o["ta"]},
        )).scalar_one()
    assert guardado and CEDULA_VALIDA not in guardado


@pytest.mark.asyncio
async def test_cedula_sin_clave_configurada_no_se_guarda(dos_organizaciones, monkeypatch):
    monkeypatch.delenv("INVENTARIO_CLAVE_CIFRADO", raising=False)
    o = dos_organizaciones
    cab = _cab(o["ta"], o["admin"], "admin_organizacion")
    persona = {"nombre": "Persona Ficticia", "cargo": "Gerente", "email": "q@organizacion.invalid", "cedula": CEDULA_VALIDA}
    async with _cli() as c:
        assert (await c.post(f"{RUTA}/personas", json=persona, headers=cab)).status_code == 503
        sin_cedula = {k: v for k, v in persona.items() if k != "cedula"}
        assert (await c.post(f"{RUTA}/personas", json=sin_cedula, headers=cab)).status_code == 201


@pytest.mark.asyncio
async def test_vinculos_solo_con_tratamientos_propios(dos_organizaciones, factory):
    o = dos_organizaciones
    rat_a = await _sembrar_tratamiento(factory, o["ta"], "T17-A")
    rat_b = await _sembrar_tratamiento(factory, o["tb"], "T17-B")
    cab = _cab(o["ta"], o["admin"], "admin_organizacion")
    async with _cli() as c:
        activo = (await c.post(f"{RUTA}/activos", json={"tipo": "sistema", "nombre": "Con vínculos"}, headers=cab)).json()["id"]
        disponibles = (await c.get(f"{RUTA}/tratamientos", headers=cab)).json()
        assert [t["id"] for t in disponibles] == [rat_a]
        assert (await c.put(f"{RUTA}/activos/{activo}/tratamientos", json={"tratamiento_ids": [rat_a, rat_b]}, headers=cab)).status_code == 422
        assert (await c.put(f"{RUTA}/activos/{activo}/tratamientos", json={"tratamiento_ids": [rat_a, rat_a]}, headers=cab)).status_code == 200
        assert (await c.get(f"{RUTA}/activos", headers=cab)).json()[0]["tratamiento_ids"] == [rat_a]
        assert (await c.put(f"{RUTA}/activos/{activo}/tratamientos", json={"tratamiento_ids": []}, headers=cab)).status_code == 200
        assert (await c.get(f"{RUTA}/activos", headers=cab)).json()[0]["tratamiento_ids"] == []


@pytest.mark.asyncio
async def test_rls_y_permisos_como_lopdp_app(dos_organizaciones, factory):
    o = dos_organizaciones
    async with factory() as s:
        for tabla, permiso, esperado in (
            ("inventario_activos", "DELETE", False), ("inventario_personas", "DELETE", False),
            ("inventario_activos", "UPDATE", True), ("inventario_personas", "INSERT", True),
            ("inventario_activos_tratamientos", "DELETE", True), ("inventario_activos_tratamientos", "UPDATE", False),
        ):
            r = (await s.execute(text("SELECT has_table_privilege('lopdp_app', :t, :p)"), {"t": tabla, "p": permiso})).scalar()
            assert r is esperado, (tabla, permiso)
        forzadas = (await s.execute(text(
            "SELECT count(*) FROM pg_class WHERE relname IN "
            "('inventario_activos', 'inventario_personas', 'inventario_activos_tratamientos') "
            "AND relrowsecurity AND relforcerowsecurity"
        ))).scalar()
        assert forzadas == 3
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": o["ta"]})
        await s.execute(
            text("INSERT INTO inventario_activos (id, tenant_id, tipo, nombre, created_by) VALUES (:id, :t, 'sistema', 'De A', 'u')"),
            {"id": str(uuid.uuid4()), "t": o["ta"]},
        )
        with pytest.raises(Exception):  # WITH CHECK: no se escribe en otra organización
            async with s.begin_nested():
                await s.execute(
                    text("INSERT INTO inventario_activos (id, tenant_id, tipo, nombre, created_by) VALUES (:id, :t, 'sistema', 'Ajeno', 'u')"),
                    {"id": str(uuid.uuid4()), "t": o["tb"]},
                )
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": o["tb"]})
        assert (await s.execute(text("SELECT count(*) FROM inventario_activos"))).scalar() == 0
        await s.rollback()


# ---------------------------------------------------------------- condiciones del CTO sobre la cédula

@pytest.mark.asyncio
async def test_cedula_no_aparece_en_logs_auditoria_ni_respuestas(dos_organizaciones, factory, clave_cifrado, caplog):
    o = dos_organizaciones
    cab = _cab(o["ta"], o["admin"], "admin_organizacion")
    persona = {"nombre": "Persona Ficticia", "cargo": "Gerente", "email": "c@organizacion.invalid", "cedula": CEDULA_VALIDA}
    with caplog.at_level("DEBUG"):
        async with _cli() as c:
            creada = await c.post(f"{RUTA}/personas", json=persona, headers=cab)
            lista = await c.get(f"{RUTA}/personas", headers=cab)
    assert CEDULA_VALIDA not in creada.text and CEDULA_VALIDA not in lista.text
    assert CEDULA_VALIDA not in caplog.text
    async with factory() as s:
        eventos = (await s.execute(
            text("SELECT CAST(payload AS text) FROM audit_events WHERE tenant_id = :t"), {"t": o["ta"]},
        )).scalars().all()
    assert all(CEDULA_VALIDA not in (e or "") for e in eventos)


# ORG-17b: acepta la referencia a Secret Manager (`NOMBRE=INVENTARIO_CLAVE_CIFRADO:latest` o `:<versión>`) y sigue
# detectando cualquier valor de 20 caracteres o más. El lookahead final impide que `:latestAAAA…` pase por referencia.
PATRON_CLAVE_ESCRITA = re.compile(
    r"INVENTARIO_CLAVE_CIFRADO\s*[:=]\s*[\"']?"
    r"(?!INVENTARIO_CLAVE_CIFRADO:(?:latest|\d+)(?![A-Za-z0-9_\-=]))"
    r"[A-Za-z0-9_\-=]{20,}"
)
REFERENCIA = "INVENTARIO_CLAVE_CIFRADO=INVENTARIO_CLAVE_CIFRADO:latest"


def _fernet_real() -> str:
    """Un valor con la forma de una clave Fernet, generado al ejecutar y nunca escrito en un archivo."""
    return base64.urlsafe_b64encode(os.urandom(32)).decode("ascii")


@pytest.mark.parametrize(
    ("texto", "debe_detectarse"),
    [
        pytest.param(lambda k: f'--set-secrets="{REFERENCIA}"', False, id="referencia-latest"),
        pytest.param(lambda k: "INVENTARIO_CLAVE_CIFRADO=INVENTARIO_CLAVE_CIFRADO:3,OTRA=x:latest", False, id="referencia-version-3"),
        pytest.param(lambda k: f"INVENTARIO_CLAVE_CIFRADO: {k}", True, id="fernet-en-yaml"),
        pytest.param(lambda k: f'INVENTARIO_CLAVE_CIFRADO="{k}"', True, id="fernet-entre-comillas"),
        pytest.param(lambda k: f"INVENTARIO_CLAVE_CIFRADO={k}", True, id="fernet-en-env"),
        pytest.param(lambda k: f"INVENTARIO_CLAVE_CIFRADO={k.rstrip('=')}", True, id="fernet-sin-relleno"),
        pytest.param(lambda k: f"INVENTARIO_CLAVE_CIFRADO=INVENTARIO_CLAVE_CIFRADO:latest{k[:4]}", True, id="latest-seguido-de-texto"),
        pytest.param(lambda k: f"INVENTARIO_CLAVE_CIFRADO={k},{REFERENCIA}", True, id="fernet-seguido-de-referencia"),
    ],
)
def test_el_patron_acepta_la_referencia_a_secret_manager_y_detecta_un_valor_real(texto, debe_detectarse):
    k = _fernet_real()
    assert len(k) == 44
    assert bool(PATRON_CLAVE_ESCRITA.search(texto(k))) is debe_detectarse


def test_la_clave_de_cifrado_no_esta_escrita_en_ningun_archivo():
    """La variable solo se lee del entorno: ningún archivo versionado le asigna un valor."""
    import pathlib

    raiz = pathlib.Path(__file__).resolve().parent.parent
    patron = PATRON_CLAVE_ESCRITA
    candidatos = [raiz / ".github" / "workflows" / "deploy-gcp.yml", raiz / ".env.example", raiz / "docker-compose.yml"]
    candidatos += list((raiz / "features" / "organizacion").rglob("*.py")) + list((raiz / "api").rglob("*.py"))
    for archivo in candidatos:
        if archivo.exists():
            assert not patron.search(archivo.read_text(encoding="utf-8", errors="ignore")), archivo.name


@pytest.mark.asyncio
async def test_sin_clave_la_funcion_falla_cerrada_y_no_guarda_nada(dos_organizaciones, factory, monkeypatch):
    monkeypatch.setenv("INVENTARIO_CLAVE_CIFRADO", "no-es-una-clave-valida")
    o = dos_organizaciones
    cab = _cab(o["ta"], o["admin"], "admin_organizacion")
    persona = {"nombre": "Persona Ficticia", "cargo": "Gerente", "email": "d@organizacion.invalid", "cedula": CEDULA_VALIDA}
    async with _cli() as c:
        assert (await c.post(f"{RUTA}/personas", json=persona, headers=cab)).status_code == 503
    async with factory() as s:
        n = (await s.execute(text("SELECT count(*) FROM inventario_personas WHERE tenant_id = :t"), {"t": o["ta"]})).scalar()
    assert n == 0
