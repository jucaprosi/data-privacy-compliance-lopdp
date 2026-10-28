# ¤rbac-tenant
# ¤arbitro
"""Árbitro de ORG-14: datos de la organización para documentos.

Valida:
1. Una organización existente sin estos datos sigue funcionando: todos salen como faltantes.
2. Prueba cruzada: un usuario de otra organización no lee ni edita estos datos, ni siquiera
   nombrando la organización ajena en el cuerpo de la petición.
3. Un rol sin administración lee, pero no edita.
4. Los valores inválidos se rechazan en el servidor con ErrorNegocio (DATOS_DOCUMENTALES_INVALIDOS).
5. La edición parcial conserva los demás campos, null borra y la auditoría guarda solo los nombres
   de los campos cambiados, nunca sus valores.

Las pruebas de validación pura no tocan la BD; las de integración necesitan TEST_DATABASE_URL
(rama Neon propia) y se omiten sin ella. Todos los datos son ficticios: la cédula usa el código 30
(no corresponde a una provincia) y los correos el dominio reservado .test.
"""
from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.errores import ErrorNegocio
from features.organizacion.organizacion_service import (
    CAMPOS_DOCUMENTALES,
    VARIABLES_DOCUMENTALES,
    es_cedula_valida,
    es_identificacion_valida,
    normalizar_dato_documental,
)
from main import app

client = TestClient(app)
RUTA = "/api/v1/organizacion/datos-documentales"
CEDULA_FICTICIA = "3000000004"

DATOS_VALIDOS = {
    "direccion": "Av. Ficticia N10-20 y Calle Prueba",
    "ciudad": "Quito",
    "telefono": "+593 2 000 0000",
    "correo_contacto": "contacto@organizacion.test",
    "correo_privacidad": "privacidad@organizacion.test",
    "sitio_web": "https://organizacion.test",
    "representante_legal_nombre": "Persona Ficticia de Prueba",
    "representante_legal_identificacion": CEDULA_FICTICIA,
    "representante_legal_cargo": "Gerente General",
}


# ---------------------------------------------------------------- validación pura (sin BD)

def test_cedula_ficticia_es_valida_y_las_alteradas_no():
    assert es_cedula_valida(CEDULA_FICTICIA)
    assert not es_cedula_valida("3000000005"), "dígito verificador alterado"
    assert not es_cedula_valida("9900000004"), "provincia inexistente"
    assert not es_cedula_valida("300000000"), "nueve dígitos"
    assert es_identificacion_valida(CEDULA_FICTICIA + "001"), "RUC de persona natural"
    assert not es_identificacion_valida(CEDULA_FICTICIA + "000")


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("correo_contacto", "sin-arroba.test"),
        ("correo_privacidad", "dos@@organizacion.test"),
        ("sitio_web", "organizacion.test"),
        ("sitio_web", "ftp://organizacion.test"),
        ("sitio_web", "https://sin-dominio"),
        ("telefono", "llamar al 099"),
        ("representante_legal_identificacion", "1234567890"),
        ("ciudad", "x" * 121),
    ],
)
def test_valores_invalidos_lanzan_error_negocio(campo, valor):
    with pytest.raises(ErrorNegocio) as exc:
        normalizar_dato_documental(campo, valor)
    assert exc.value.code == "DATOS_DOCUMENTALES_INVALIDOS"
    assert exc.value.status_code == 422
    assert campo in exc.value.detail


def test_vacio_se_normaliza_a_none_y_correo_a_minusculas():
    assert normalizar_dato_documental("direccion", "   ") is None
    assert normalizar_dato_documental("correo_contacto", " Contacto@Organizacion.TEST ") == "contacto@organizacion.test"


def test_variables_cubren_las_de_la_biblioteca():
    """Cada columna nueva tiene su variable de plantilla (docs/biblioteca-pmv.md, apartado a)."""
    assert set(CAMPOS_DOCUMENTALES) <= set(VARIABLES_DOCUMENTALES.values())
    assert {"representante.nombre", "representante.identificacion", "representante.cargo"} <= set(VARIABLES_DOCUMENTALES)


# ---------------------------------------------------------------- integración (rama Neon propia)

def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Sin TEST_DATABASE_URL: la parte de BD de ORG-14 queda no verificada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def factory():
    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    yield async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    await engine.dispose()


@pytest_asyncio.fixture
async def dos_organizaciones(factory):
    """Organización A (admin y dpo) y organización B (su propio admin), sin datos documentales."""
    sufijo = uuid.uuid4().hex[:8]
    ta, tb = f"t14a-{sufijo}", f"t14b-{sufijo}"
    ua_admin, ua_dpo, ub_admin = f"u14aa-{sufijo}", f"u14ad-{sufijo}", f"u14ba-{sufijo}"
    usuarios = (ua_admin, ua_dpo, ub_admin)

    async with factory() as s:
        for tid in (ta, tb):
            await s.execute(
                text(
                    "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                    "VALUES (:id, :nom, :razon, :ruc)"
                ),
                {"id": tid, "nom": f"Org {tid}", "razon": f"Org Ficticia {tid} S.A.", "ruc": f"RUC{tid[:10]}"},
            )
        for uid in usuarios:
            await s.execute(
                text("INSERT INTO users (id, email, nombre) VALUES (:id, :email, :nombre)"),
                {"id": uid, "email": f"{uid}@organizacion.test", "nombre": f"Usuario ficticio {uid}"},
            )
        for uid, tid, rol in ((ua_admin, ta, "admin_organizacion"), (ua_dpo, ta, "dpo"), (ub_admin, tb, "admin_organizacion")):
            await s.execute(
                text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, :r)"),
                {"id": f"r14-{uuid.uuid4().hex[:8]}", "u": uid, "t": tid, "r": rol},
            )
        await s.commit()

    yield {"ta": ta, "tb": tb, "ua_admin": ua_admin, "ua_dpo": ua_dpo, "ub_admin": ub_admin}

    async with factory() as s:
        await s.execute(text("DELETE FROM audit_events WHERE tenant_id IN (:a, :b)"), {"a": ta, "b": tb})
        await s.execute(text("DELETE FROM user_tenant_roles WHERE tenant_id IN (:a, :b)"), {"a": ta, "b": tb})
        await s.execute(text("DELETE FROM users WHERE id IN (:u1, :u2, :u3)"), dict(zip(("u1", "u2", "u3"), usuarios)))
        await s.execute(text("DELETE FROM tenants WHERE id IN (:a, :b)"), {"a": ta, "b": tb})
        await s.commit()


def _cab(tenant: str, usuario: str, rol: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant, "X-User-ID": usuario, "X-Role": rol}


async def _fila(factory, tenant: str) -> dict:
    async with factory() as s:
        fila = (await s.execute(
            text(
                "SELECT direccion, ciudad, telefono, correo_contacto, correo_privacidad, sitio_web, "
                "representante_legal_nombre, representante_legal_identificacion, representante_legal_cargo "
                "FROM tenants WHERE id = :t"
            ),
            {"t": tenant},
        )).mappings().one()
    return dict(fila)


@pytest.mark.asyncio
async def test_columnas_nuevas_son_opcionales(factory):
    async with factory() as s:
        filas = (await s.execute(
            text(
                "SELECT column_name, is_nullable FROM information_schema.columns "
                "WHERE table_name = 'tenants' AND column_name = ANY(:cols)"
            ),
            {"cols": list(CAMPOS_DOCUMENTALES)},
        )).all()
    assert {nombre: nulo for nombre, nulo in filas} == {campo: "YES" for campo in CAMPOS_DOCUMENTALES}


@pytest.mark.asyncio
async def test_organizacion_sin_datos_sigue_funcionando_y_los_muestra_faltantes(dos_organizaciones, factory):
    o = dos_organizaciones
    r = client.get(RUTA, headers=_cab(o["ta"], o["ua_dpo"], "dpo"))
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["tenant_id"] == o["ta"]
    assert all(cuerpo[campo] is None for campo in CAMPOS_DOCUMENTALES)
    assert set(cuerpo["faltantes"]) == set(CAMPOS_DOCUMENTALES)

    # La compuerta de solo lectura que usará Biblioteca (BIB-201).
    from features.organizacion import organizacion_service

    async with factory() as s:
        variables = await organizacion_service.obtener_variables_documentales(s, o["ta"])
    assert variables["valores"]["organizacion.razon_social"] == f"Org Ficticia {o['ta']} S.A."
    assert "organizacion.direccion" in variables["faltantes"]
    assert "representante.nombre" in variables["faltantes"]
    assert "organizacion.razon_social" not in variables["faltantes"]

    # La configuración existente de la organización no se ve afectada.
    assert client.get("/api/v1/organizacion/configuracion", headers=_cab(o["ta"], o["ua_dpo"], "dpo")).status_code == 200


@pytest.mark.asyncio
async def test_prueba_cruzada_otra_organizacion_no_lee_ni_edita(dos_organizaciones, factory):
    o = dos_organizaciones
    assert client.patch(RUTA, headers=_cab(o["ta"], o["ua_admin"], "admin_organizacion"), json=DATOS_VALIDOS).status_code == 200
    antes_a, antes_b = await _fila(factory, o["ta"]), await _fila(factory, o["tb"])

    # El admin de B declara la organización A en la cabecera: no tiene membresía allí.
    ajena = _cab(o["ta"], o["ub_admin"], "admin_organizacion")
    assert client.get(RUTA, headers=ajena).status_code == 403
    assert client.patch(RUTA, headers=ajena, json={"ciudad": "Cuenca"}).status_code == 403

    # El admin de B, en su propia sesión, nombra la organización A en el cuerpo: no cuenta.
    propia_b = _cab(o["tb"], o["ub_admin"], "admin_organizacion")
    r = client.patch(RUTA, headers=propia_b, json={"tenant_id": o["ta"], "ciudad": "Cuenca"})
    assert r.status_code != 200, "la organización se toma de la sesión, nunca del cuerpo"
    assert await _fila(factory, o["ta"]) == antes_a
    assert await _fila(factory, o["tb"]) == antes_b

    # Y lo que B lee es lo suyo, no lo de A.
    lectura_b = client.get(RUTA, headers=propia_b).json()
    assert lectura_b["tenant_id"] == o["tb"]
    assert lectura_b["direccion"] is None


@pytest.mark.asyncio
async def test_rol_sin_administracion_lee_pero_no_edita(dos_organizaciones, factory):
    o = dos_organizaciones
    dpo = _cab(o["ta"], o["ua_dpo"], "dpo")
    assert client.get(RUTA, headers=dpo).status_code == 200
    assert client.patch(RUTA, headers=dpo, json={"ciudad": "Cuenca"}).status_code == 403
    assert (await _fila(factory, o["ta"]))["ciudad"] is None


@pytest.mark.asyncio
async def test_valores_invalidos_se_rechazan_en_el_servidor(dos_organizaciones, factory):
    o = dos_organizaciones
    admin = _cab(o["ta"], o["ua_admin"], "admin_organizacion")
    for cuerpo in (
        {"correo_privacidad": "no-es-correo"},
        {"sitio_web": "organizacion.test"},
        {"representante_legal_identificacion": "1234567890"},
        {"ciudad": "Quito", "correo_contacto": "mal@"},
    ):
        r = client.patch(RUTA, headers=admin, json=cuerpo)
        assert r.status_code == 422, cuerpo
        assert r.json()["code"] == "DATOS_DOCUMENTALES_INVALIDOS", cuerpo
    # Un cuerpo con un campo inválido no deja escrito ningún campo, ni los válidos.
    assert (await _fila(factory, o["ta"]))["ciudad"] is None


@pytest.mark.asyncio
async def test_admin_edita_parcial_borra_con_null_y_audita_sin_valores(dos_organizaciones, factory):
    o = dos_organizaciones
    admin = _cab(o["ta"], o["ua_admin"], "admin_organizacion")

    r = client.patch(RUTA, headers=admin, json=DATOS_VALIDOS)
    assert r.status_code == 200
    assert r.json()["faltantes"] == []
    assert r.json()["representante_legal_identificacion"] == CEDULA_FICTICIA

    r = client.patch(RUTA, headers=admin, json={"ciudad": "Guayaquil", "sitio_web": None})
    assert r.status_code == 200
    fila = await _fila(factory, o["ta"])
    assert fila["ciudad"] == "Guayaquil"
    assert fila["sitio_web"] is None
    assert fila["direccion"] == DATOS_VALIDOS["direccion"], "el campo no enviado se conserva"
    assert r.json()["faltantes"] == ["sitio_web"]

    async with factory() as s:
        eventos = (await s.execute(
            text(
                "SELECT user_id, payload FROM audit_events "
                "WHERE tenant_id = :t AND action = 'datos_documentales_updated' ORDER BY timestamp"
            ),
            {"t": o["ta"]},
        )).mappings().all()
    assert [e["payload"] for e in eventos] == [
        {"campos": sorted(CAMPOS_DOCUMENTALES)},
        {"campos": ["ciudad", "sitio_web"]},
    ]
    assert {e["user_id"] for e in eventos} == {o["ua_admin"]}
    texto = str([e["payload"] for e in eventos])
    assert DATOS_VALIDOS["representante_legal_nombre"] not in texto and CEDULA_FICTICIA not in texto
