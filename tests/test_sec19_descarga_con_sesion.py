# ¤seguridad ¤arbitro
# ¤¤qa-engineer
"""Árbitro SEC-19: la descarga con token exige sesión, y el token es de quien la usa.

Orden: sesión → firma verificada → `pid`, `sub`/`tid` y `ver`. Contrato:
- Sin sesión: 401 (lo decide `get_context`; la prueba 2 corre con AUTH_MODE=oidc).
- Firma inválida, caducada, `pid` o `ver` distintos: 403 BIB_TOKEN_DESCARGA_INVALIDO.
- `sub` o `tid` distintos de la sesión: 403 BIB_TOKEN_DE_OTRA_PERSONA.
En los errores no salen bytes ni se escribe auditoría.

La persistencia corre como `lopdp_app` contra PostgreSQL local (ARNES_BASE=postgresql_local), en una
transacción que se revierte, con datos sintéticos y correos `.invalid`. La sesión válida se simula
sustituyendo `get_context` (la verificación OIDC tiene sus propias pruebas); la clave se genera aquí.

Mutaciones (governance/apoyo/DISENO_SEC-19_DESCARGA_CON_SESION.md §6):
- M1: el router vuelve a tomar `tid` y `sub` del token: fallan la 3 y la 4.
- M2: se quita la comparación de `sub` con la sesión: falla la 3.
- M3: se omite `get_context` cuando hay token: falla la 2.
"""
import os
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import httpx
import jwt
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from api.rbac import get_context
from app_core.db.session import get_session
from features.biblioteca.services import archivos
from main import app

PRODUCCION = "ep-late-hall-b50bpbk5"
CONTENIDO = b"PK\x03\x04 contenido sintetico SEC-19"


def _ruta(pid: str, token: str | None) -> str:
    base = f"/api/v1/biblioteca/descargas/{pid}/archivo"
    return f"{base}?token={token}" if token else base


# ¤arbitro
def _url() -> str:
    url = os.environ.get("TEST_DATABASE_URL", "")
    if PRODUCCION in url.lower():
        pytest.fail("Host de producción prohibido; no se abrió conexión", pytrace=False)
    if not url or os.environ.get("ARNES_BASE") != "postgresql_local":
        pytest.skip("Persistencia SEC-19 no acreditada: falta PostgreSQL local (ARNES_BASE=postgresql_local)")
    return url.replace("postgresql://", "postgresql+psycopg://", 1) if url.startswith("postgresql://") else url


@pytest.fixture(autouse=True)
def _clave(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", secrets.token_urlsafe(32))


# ¤arbitro
@pytest_asyncio.fixture
async def mundo():
    engine = create_async_engine(_url(), echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            sufijo = uuid4().hex[:8]
            u = {"a": f"sec19-a-{sufijo}", "b": f"sec19-b-{sufijo}"}
            t = {"t1": f"sec19-t1-{sufijo}", "t2": f"sec19-t2-{sufijo}"}
            pid, otra = str(uuid4()), str(uuid4())
            await conexion.execute(text("INSERT INTO users(id,email,nombre) VALUES (:id,:e,'Sintético')"),
                                   [{"id": v, "e": f"{v}@correo.invalid"} for v in u.values()])
            await conexion.execute(text("INSERT INTO tenants(id,nombre_comercial,razon_social,ruc_identificacion) "
                                        "VALUES (:id,'Org','Org SA',:ruc)"),
                                   [{"id": v, "ruc": f"179{uuid4().int % 10**10:010d}"} for v in t.values()])
            await conexion.execute(text("INSERT INTO user_tenant_roles(id,user_id,tenant_id,role) "
                                        "VALUES (:id,:u,:t,'implementador')"),
                                   [{"id": str(uuid4()), "u": us, "t": te}
                                    for us in u.values() for te in t.values()])
            await conexion.execute(text("SELECT set_config('app.current_user_id', :u, true)"), {"u": u["a"]})
            await conexion.execute(text(  # BIB-117: nadie se autoconcede; otorgante sintético distinto
                "WITH o AS (INSERT INTO users(id,email,nombre) SELECT 'otorgante-'||g, 'otorgante-'||g||'@correo.invalid', "
                "'Otorgante sintético' FROM md5(random()::text) g RETURNING id) "
                "INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo) "
                "SELECT :u,'editor',o.id,'prueba' FROM o"), {"u": u["a"]})
            for version_id in (pid, otra):
                codigo = f"SEC19-{uuid4().hex[:8].upper()}"
                await conexion.execute(text("INSERT INTO biblioteca_catalogo(codigo) VALUES (:c)"), {"c": codigo})
                await conexion.execute(text(
                    "INSERT INTO biblioteca_versiones(id,codigo,version,formato,responsable_id,autores) "
                    "VALUES (:id,:c,'1.0.0','DOCX',:u,CAST(:a AS jsonb))"),
                    {"id": version_id, "c": codigo, "u": u["a"], "a": f'["{u["a"]}"]'})
            # Publicación sintética directa: el flujo editorial tiene sus propias pruebas.
            await conexion.execute(text("SET LOCAL session_replication_role = replica"))
            await conexion.execute(text(
                "UPDATE biblioteca_versiones SET estado='publicada', archivo=:b, nombre_archivo='sec19.docx', sha256=repeat('a',64) "
                "WHERE id IN (:p,:o)"), {"b": CONTENIDO, "p": pid, "o": otra})
            await conexion.execute(text("SET LOCAL session_replication_role = origin"))
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False,
                                    join_transaction_mode="create_savepoint") as sesion:
                yield conexion, sesion, u, t, pid, otra
        finally:
            await transaccion.rollback()
    await engine.dispose()


def _token(usuario: str, tenant: str, pid: str, ver: str = "1.0.0", segundos: int = 300, clave: str | None = None):
    ahora = datetime.now(timezone.utc)
    datos = {"sub": usuario, "tid": tenant, "pid": pid, "ver": ver, "iat": ahora,
             "exp": ahora + timedelta(seconds=segundos), "aud": archivos.AUDIENCIA_TOKEN}
    return jwt.encode(datos, clave or archivos.secreto_firma_descargas(), algorithm=archivos.ALGORITMO_TOKEN)


async def _pedir(sesion: AsyncSession, ruta: str, usuario: str | None, tenant: str | None) -> httpx.Response:
    async def sesion_de_prueba():
        yield sesion
    app.dependency_overrides[get_session] = sesion_de_prueba
    if usuario:
        app.dependency_overrides[get_context] = lambda: {"user_id": usuario, "tenant_id": tenant, "role": "implementador"}
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://prueba") as api:
            return await api.get(ruta)
    finally:
        app.dependency_overrides.pop(get_session, None)
        app.dependency_overrides.pop(get_context, None)


async def _auditorias(conexion, tenant: str) -> list:
    await conexion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant})
    return (await conexion.execute(text("SELECT usuario_id FROM biblioteca_descargas"))).scalars().all()


def _codigo(respuesta: httpx.Response) -> str:
    cuerpo = respuesta.json()
    return cuerpo.get("code") or cuerpo.get("codigo") or str(cuerpo)


def _sin_bytes_ni_auditoria(respuesta: httpx.Response, auditorias: list) -> None:
    assert CONTENIDO not in respuesta.content
    assert auditorias == []


# ¤arbitro
@pytest.mark.asyncio
async def test_1_token_y_sesion_del_mismo_usuario_descarga_y_audita_a_la_sesion(mundo):
    conexion, sesion, u, t, pid, _ = mundo
    respuesta = await _pedir(sesion, _ruta(pid, _token(u["a"], t["t1"], pid)), u["a"], t["t1"])
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.content == CONTENIDO
    assert await _auditorias(conexion, t["t1"]) == [u["a"]]


# ¤arbitro
@pytest.mark.asyncio
async def test_2_token_valido_sin_sesion_en_oidc_es_401(mundo, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "oidc")
    conexion, sesion, u, t, pid, _ = mundo
    respuesta = await _pedir(sesion, _ruta(pid, _token(u["a"], t["t1"], pid)), None, None)
    assert respuesta.status_code == 401, respuesta.text
    _sin_bytes_ni_auditoria(respuesta, await _auditorias(conexion, t["t1"]))


# ¤arbitro
@pytest.mark.asyncio
async def test_3_token_de_a_con_sesion_de_b_del_mismo_tenant_es_403_otra_persona(mundo):
    conexion, sesion, u, t, pid, _ = mundo
    respuesta = await _pedir(sesion, _ruta(pid, _token(u["a"], t["t1"], pid)), u["b"], t["t1"])
    assert respuesta.status_code == 403 and _codigo(respuesta) == "BIB_TOKEN_DE_OTRA_PERSONA", respuesta.text
    _sin_bytes_ni_auditoria(respuesta, await _auditorias(conexion, t["t1"]))


# ¤arbitro
@pytest.mark.asyncio
async def test_4_token_de_t1_con_sesion_en_t2_es_403_otra_persona(mundo):
    conexion, sesion, u, t, pid, _ = mundo
    respuesta = await _pedir(sesion, _ruta(pid, _token(u["a"], t["t1"], pid)), u["a"], t["t2"])
    assert respuesta.status_code == 403 and _codigo(respuesta) == "BIB_TOKEN_DE_OTRA_PERSONA", respuesta.text
    _sin_bytes_ni_auditoria(respuesta, await _auditorias(conexion, t["t1"]) + await _auditorias(conexion, t["t2"]))


# ¤arbitro
@pytest.mark.asyncio
async def test_5_token_firmado_con_la_clave_publica_de_desarrollo_es_403_invalido(mundo):
    conexion, sesion, u, t, pid, _ = mundo
    falso = _token(u["a"], t["t1"], pid, clave=archivos.CLAVE_FIRMA_DESARROLLO)
    respuesta = await _pedir(sesion, _ruta(pid, falso), u["a"], t["t1"])
    assert respuesta.status_code == 403 and _codigo(respuesta) == "BIB_TOKEN_DESCARGA_INVALIDO", respuesta.text
    _sin_bytes_ni_auditoria(respuesta, await _auditorias(conexion, t["t1"]))


# ¤arbitro
@pytest.mark.asyncio
async def test_6_token_caducado_o_de_otra_plantilla_es_403_invalido(mundo):
    conexion, sesion, u, t, pid, otra = mundo
    for token in (_token(u["a"], t["t1"], pid, segundos=-10), _token(u["a"], t["t1"], otra)):
        respuesta = await _pedir(sesion, _ruta(pid, token), u["a"], t["t1"])
        assert respuesta.status_code == 403 and _codigo(respuesta) == "BIB_TOKEN_DESCARGA_INVALIDO", respuesta.text
    _sin_bytes_ni_auditoria(respuesta, await _auditorias(conexion, t["t1"]))


# ¤arbitro
@pytest.mark.asyncio
async def test_7_sin_token_y_con_sesion_sigue_descargando(mundo):
    _, sesion, u, t, pid, _ = mundo
    respuesta = await _pedir(sesion, _ruta(pid, None), u["a"], t["t1"])
    assert respuesta.status_code == 200 and respuesta.content == CONTENIDO, respuesta.text


# ¤arbitro
@pytest.mark.asyncio
async def test_8_token_con_otra_version_es_403_invalido(mundo):
    conexion, sesion, u, t, pid, _ = mundo
    respuesta = await _pedir(sesion, _ruta(pid, _token(u["a"], t["t1"], pid, ver="9.9.9")), u["a"], t["t1"])
    assert respuesta.status_code == 403 and _codigo(respuesta) == "BIB_TOKEN_DESCARGA_INVALIDO", respuesta.text
    _sin_bytes_ni_auditoria(respuesta, await _auditorias(conexion, t["t1"]))
