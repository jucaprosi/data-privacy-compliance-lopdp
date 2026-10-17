# ¤seguridad ¤rbac-tenant ¤arbitro
"""Autenticación verificable con Google (SEC-03).

Antes: la identidad llegaba en cabeceras que el propio cliente enviaba (X-User-ID, X-Tenant-ID, X-Role),
un valor por defecto concedía acceso sin cabeceras y `Bearer jwt_mock_tenant_<id>` valía como token.
Ahora, en modo `oidc` (el de por defecto) el usuario sale solo del token de Google verificado.

Los tokens de estas pruebas se firman con una clave RSA generada aquí (nunca una clave de Google ni
credenciales reales). Las pruebas de vinculación con la base de datos requieren la migración
`20261017_users_google_sub` aplicada a la base de pruebas y se omiten, con el motivo, si falta.
"""
import os
import time
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import jwt
import pytest
import pytest_asyncio
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app_core import security
from app_core.db.session import get_session
from features.organizacion import organizacion_service
from features.roadmap import roadmap_service
from main import app

pytestmark = pytest.mark.asyncio

CLIENT_ID = "cliente-de-prueba.apps.googleusercontent.com"
EMISOR = "https://accounts.google.com"
CLAVE = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTRA_CLAVE = rsa.generate_private_key(public_exponent=65537, key_size=2048)

RUTA_CON_ROL = "/api/v1/roadmaps/tasks/task-1/evidence"  # get_context (api/rbac.py)
RUTA_CON_TENANT = "/api/v1/dpo/bitacora"  # obtener_tenant_id_actual (api/dependencies.py)
RUTA_CON_SESION_DE_TENANT = "/api/v1/ai/mitigaciones"  # get_current_tenant (app_core/security.py)


def token(*, clave=CLAVE, algoritmo="RS256", **cambios) -> str:
    ahora = int(time.time())
    claims = {
        "iss": EMISOR, "aud": CLIENT_ID, "sub": "sub-ana", "email": "ana@empresa.test",
        "email_verified": True, "iat": ahora, "exp": ahora + 3600,
    }
    claims.update(cambios)
    for clave_claim in [k for k, v in claims.items() if v is None]:
        del claims[clave_claim]
    return jwt.encode(claims, clave, algorithm=algoritmo)


def bearer(**kw) -> dict:
    return {"Authorization": f"Bearer {token(**kw)}"}


@pytest.fixture
def oidc(monkeypatch):
    """Modo oidc con la clave pública de la prueba en lugar de la de Google (sin red)."""
    monkeypatch.setenv("AUTH_MODE", "oidc")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", CLIENT_ID)
    monkeypatch.setattr(security, "_clave_de_firma", lambda _token: CLAVE.public_key())


@pytest.fixture
def api(oidc, monkeypatch):
    """Cliente HTTP. El usuario de la plataforma y la membresía se simulan: aquí se prueba la identidad."""
    monkeypatch.setattr(security, "usuario_de_identidad", AsyncMock(return_value="usuario-ana"))
    monkeypatch.setattr(security, "roles_activos", AsyncMock(return_value={"implementador"}))
    pertenece = AsyncMock(return_value=True)
    monkeypatch.setattr(organizacion_service, "has_active_role", pertenece)
    monkeypatch.setattr(roadmap_service, "list_evidence", AsyncMock(return_value=[]))
    app.dependency_overrides[get_session] = lambda: None
    yield SimpleNamespace(pertenece=pertenece)
    app.dependency_overrides.clear()


async def get(ruta, headers):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        return await c.get(ruta, headers=headers)


def con_rol(**extra) -> dict:
    return {"X-Tenant-ID": "t-1", "X-Role": "implementador", **extra}


# ---------------------------------------------------------------- modo de autenticación

@pytest.mark.parametrize("valor", [None, "", "oidc", "OIDC", "otra-cosa", "header", "headers ", "true", "0"])
async def test_solo_headers_exacto_activa_las_cabeceras(monkeypatch, valor):
    if valor is None:
        monkeypatch.delenv("AUTH_MODE", raising=False)
    else:
        monkeypatch.setenv("AUTH_MODE", valor)
    esperado = "headers" if (valor or "").strip().lower() == "headers" else "oidc"
    assert security.modo_autenticacion() == esperado


async def test_la_suite_corre_en_modo_headers_por_conftest():
    assert os.environ["AUTH_MODE"] == "headers"


# ---------------------------------------------------------------- token ausente o mal formado

@pytest.mark.parametrize("cabeceras", [
    {},
    {"Authorization": ""},
    {"Authorization": "Bearer "},
    {"Authorization": "Basic YWRtaW46YWRtaW4="},
    {"Authorization": "Bearer jwt_mock_tenant_t-1"},  # el antiguo token simulado ya no vale
    {"Authorization": "Bearer no.es.un.jwt"},
])
async def test_sin_token_valido_es_401_en_los_tres_mecanismos(api, cabeceras):
    for ruta in (RUTA_CON_ROL, RUTA_CON_TENANT, RUTA_CON_SESION_DE_TENANT):
        r = await get(ruta, {**con_rol(), **cabeceras})
        assert r.status_code == 401, f"{ruta}: {r.status_code} {r.text}"


async def test_las_cabeceras_de_identidad_no_sustituyen_al_token_en_oidc(api):
    """Con X-User-ID, X-Tenant-ID y X-Role correctos pero sin token, oidc no cae en el modo de cabeceras."""
    r = await get(RUTA_CON_ROL, con_rol(**{"X-User-ID": "usuario-ana"}))
    assert r.status_code == 401
    assert api.pertenece.await_count == 0


async def test_sin_cabecera_de_tenant_no_hay_tenant_por_defecto_en_oidc(api):
    """Antes api/dependencies.py concedía «tenant-default» y GESTOR_PROCESO a quien no enviaba nada."""
    r = await get(RUTA_CON_TENANT, bearer())
    assert r.status_code == 400
    sin_nada = await get(RUTA_CON_TENANT, {})
    assert sin_nada.status_code in (400, 401)


# ---------------------------------------------------------------- token inválido

@pytest.mark.parametrize("cambios", [
    {"iss": "https://accounts.otro.test"},
    {"iss": None},
    {"aud": "otro-cliente.apps.googleusercontent.com"},
    {"aud": None},
    {"exp": int(time.time()) - 60},
    {"exp": None},
    {"sub": None},
], ids=["emisor-ajeno", "sin-emisor", "audiencia-ajena", "sin-audiencia", "caducado", "sin-exp", "sin-sub"])
async def test_token_con_claims_invalidos_es_401(api, cambios):
    r = await get(RUTA_CON_ROL, {**con_rol(), **bearer(**cambios)})
    assert r.status_code == 401


async def test_firma_de_otra_clave_es_401(api):
    r = await get(RUTA_CON_ROL, {**con_rol(), **bearer(clave=OTRA_CLAVE)})
    assert r.status_code == 401


async def test_algoritmo_distinto_de_rs256_es_401(api):
    """Un token HS256 firmado con la clave pública como secreto (ataque de confusión de algoritmo)."""
    from cryptography.hazmat.primitives import serialization

    publica = CLAVE.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    ahora = int(time.time())
    # PyJWT recientes se niegan a firmar así a propósito; el token se arma a mano.
    import base64, hashlib, hmac, json

    def b64(b):
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

    cabecera = b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    cuerpo = b64(json.dumps(
        {"iss": EMISOR, "aud": CLIENT_ID, "sub": "sub-ana", "email": "ana@empresa.test",
         "email_verified": True, "exp": ahora + 3600}
    ).encode())
    firma = b64(hmac.new(publica, f"{cabecera}.{cuerpo}".encode(), hashlib.sha256).digest())
    r = await get(RUTA_CON_ROL, {**con_rol(), "Authorization": f"Bearer {cabecera}.{cuerpo}.{firma}"})
    assert r.status_code == 401


async def test_token_sin_firma_alg_none_es_401(api):
    import base64, json

    def b64(b):
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

    ahora = int(time.time())
    sin_firma = (
        b64(json.dumps({"alg": "none", "typ": "JWT"}).encode()) + "."
        + b64(json.dumps({"iss": EMISOR, "aud": CLIENT_ID, "sub": "x", "email": "a@b.test",
                          "email_verified": True, "exp": ahora + 3600}).encode()) + "."
    )
    r = await get(RUTA_CON_ROL, {**con_rol(), "Authorization": f"Bearer {sin_firma}"})
    assert r.status_code == 401


@pytest.mark.parametrize("email_verified", [False, "false", None, 0])
async def test_correo_no_verificado_es_401(api, email_verified):
    r = await get(RUTA_CON_ROL, {**con_rol(), **bearer(email_verified=email_verified)})
    assert r.status_code == 401


async def test_token_sin_correo_es_401(api):
    r = await get(RUTA_CON_ROL, {**con_rol(), **bearer(email=None)})
    assert r.status_code == 401


async def test_emisor_sin_https_tambien_es_valido(api):
    """Google documenta dos formas del emisor; ambas se aceptan."""
    r = await get(RUTA_CON_ROL, {**con_rol(), **bearer(iss="accounts.google.com")})
    assert r.status_code == 200


async def test_el_mensaje_de_error_no_orienta_a_quien_prueba(api):
    detalles = set()
    for cambios in ({"aud": "x"}, {"iss": "x"}, {"exp": int(time.time()) - 60}):
        r = await get(RUTA_CON_ROL, {**con_rol(), **bearer(**cambios)})
        detalles.add(r.json()["detail"])
    assert len(detalles) == 1


# ---------------------------------------------------------------- cierre ante falta de configuración

async def test_sin_client_id_configurado_cierra_con_503_aunque_el_token_sea_valido(api, monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    r = await get(RUTA_CON_ROL, {**con_rol(), **bearer()})
    assert r.status_code == 503


async def test_servicio_de_claves_caido_es_503_y_no_concede(api, monkeypatch):
    def caido(_token):
        raise jwt.PyJWKClientConnectionError("sin red")

    monkeypatch.setattr(security, "_clave_de_firma", caido)
    r = await get(RUTA_CON_ROL, {**con_rol(), **bearer()})
    assert r.status_code == 503


# ---------------------------------------------------------------- identidad y autorización

async def test_token_valido_entra_y_el_usuario_es_el_del_token(api):
    r = await get(RUTA_CON_ROL, {**con_rol(), **bearer()})
    assert r.status_code == 200, r.text
    assert api.pertenece.await_args.args[2] == "usuario-ana"


async def test_x_user_id_suplantado_se_ignora(api):
    r = await get(RUTA_CON_ROL, {**con_rol(**{"X-User-ID": "usuario-victima"}), **bearer()})
    assert r.status_code == 200
    usados = {c.args[2] for c in api.pertenece.await_args_list}
    assert usados == {"usuario-ana"}


async def test_tenant_sin_membresia_es_403(api):
    api.pertenece.return_value = False
    r = await get(RUTA_CON_ROL, {**con_rol(), **bearer()})
    assert r.status_code == 403


async def test_tenant_sin_ningun_rol_es_403_en_los_otros_dos_mecanismos(api, monkeypatch):
    monkeypatch.setattr(security, "roles_activos", AsyncMock(return_value=set()))
    for ruta in (RUTA_CON_TENANT, RUTA_CON_SESION_DE_TENANT):
        r = await get(ruta, {"X-Tenant-ID": "t-ajeno", **bearer()})
        assert r.status_code == 403, f"{ruta}: {r.status_code}"


async def test_usuario_no_registrado_es_403(api, monkeypatch):
    monkeypatch.setattr(
        security, "usuario_de_identidad",
        AsyncMock(side_effect=HTTPException(403, "Usuario no registrado en la plataforma.")),
    )
    r = await get(RUTA_CON_ROL, {**con_rol(), **bearer()})
    assert r.status_code == 403


# ---------------------------------------------------------------- vinculación con la base de datos

def _url():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    return url.replace("postgresql://", "postgresql+psycopg://", 1) if url.startswith("postgresql://") else url


@pytest_asyncio.fixture
async def bd():
    engine = create_async_engine(_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as s:
        hay = (await s.execute(text(
            "SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='google_sub'"
        ))).first()
    if not hay:
        await engine.dispose()
        pytest.skip("falta aplicar la migración 20261017_users_google_sub a la base de pruebas")
    creados: list[str] = []

    async def usuario(correo=None, google_sub=None, activo=True) -> str:
        uid = f"sec03-{uuid.uuid4().hex[:10]}"
        creados.append(uid)
        async with factory() as s:
            await s.execute(text(
                "INSERT INTO users (id, email, nombre, google_sub, activo) VALUES (:i, :e, :n, :g, :a)"
            ), {"i": uid, "e": correo or f"{uid}@sec03.test", "n": uid, "g": google_sub, "a": activo})
            await s.commit()
        return uid

    yield factory, usuario
    async with factory() as s:
        await s.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": creados})
        await s.commit()
    await engine.dispose()


def _identidad(sub, email):
    return security.IdentidadVerificada(sub=sub, email=email)


async def test_primer_acceso_vincula_la_cuenta_por_correo_verificado(bd):
    factory, usuario = bd
    sub = f"sub-{uuid.uuid4().hex[:8]}"
    uid = await usuario(correo=f"{sub}@sec03.test")
    async with factory() as s:
        assert await security.usuario_de_identidad(s, _identidad(sub, f"{sub}@sec03.test")) == uid
        await s.commit()
        guardado = (await s.execute(text("SELECT google_sub FROM users WHERE id=:i"), {"i": uid})).scalar()
    assert guardado == sub


async def test_acceso_posterior_se_resuelve_por_sub_aunque_cambie_el_correo(bd):
    factory, usuario = bd
    sub = f"sub-{uuid.uuid4().hex[:8]}"
    uid = await usuario(google_sub=sub)
    async with factory() as s:
        assert await security.usuario_de_identidad(s, _identidad(sub, "otro-correo@sec03.test")) == uid


async def test_cuenta_vinculada_a_otro_sub_no_se_reasigna(bd):
    factory, usuario = bd
    correo = f"{uuid.uuid4().hex[:8]}@sec03.test"
    await usuario(correo=correo, google_sub=f"sub-dueno-{uuid.uuid4().hex[:6]}")
    async with factory() as s:
        with pytest.raises(HTTPException) as e:
            await security.usuario_de_identidad(s, _identidad(f"sub-intruso-{uuid.uuid4().hex[:6]}", correo))
    assert e.value.status_code == 403


async def test_correo_desconocido_no_crea_usuario(bd):
    factory, _ = bd
    async with factory() as s:
        with pytest.raises(HTTPException) as e:
            await security.usuario_de_identidad(s, _identidad(f"sub-{uuid.uuid4().hex[:6]}", "nadie@sec03.test"))
        assert e.value.status_code == 403
        cuantos = (await s.execute(text("SELECT count(*) FROM users WHERE email='nadie@sec03.test'"))).scalar()
    assert cuantos == 0


async def test_usuario_inactivo_no_entra(bd):
    factory, usuario = bd
    correo = f"{uuid.uuid4().hex[:8]}@sec03.test"
    await usuario(correo=correo, activo=False)
    async with factory() as s:
        with pytest.raises(HTTPException) as e:
            await security.usuario_de_identidad(s, _identidad(f"sub-{uuid.uuid4().hex[:6]}", correo))
    assert e.value.status_code == 403


async def test_el_correo_se_compara_sin_distinguir_mayusculas(bd):
    factory, usuario = bd
    sub = f"sub-{uuid.uuid4().hex[:8]}"
    uid = await usuario(correo=f"Mixto.{sub}@sec03.test")
    async with factory() as s:
        assert await security.usuario_de_identidad(s, _identidad(sub, f"mixto.{sub}@sec03.test")) == uid


async def test_google_sub_es_unico(bd):
    factory, usuario = bd
    sub = f"sub-{uuid.uuid4().hex[:8]}"
    await usuario(google_sub=sub)
    with pytest.raises(Exception):
        await usuario(google_sub=sub)
