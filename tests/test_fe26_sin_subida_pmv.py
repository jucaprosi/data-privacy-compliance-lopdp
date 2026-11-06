# ¤roadmap ¤evidencias ¤arbitro
"""FE-26: el PMV no sube archivos de evidencia a la hoja de ruta; el servidor rechaza esas subidas.

Contrato: governance/tareas/FE-26.md, INV_LOPDP_PMV_DECLARED_EVIDENCE y la decisión del propietario
del 2026-11-05. El interruptor `EVIDENCIA_FISICA` se lee solo en
`features/roadmap/domain/evidencia_fisica.py`: apagado por omisión (PMV), «true» en EVYDENTIA.

Con el interruptor apagado, `upload-url` y el registro de evidencia responden 409
`RM_EVIDENCIA_NO_DISPONIBLE`; la lista y la validación siguen respondiendo para no romper datos ya
registrados. Con él encendido se conserva el comportamiento de antes, incluidos los permisos de
`responsable_area` y `coordinador`.

Las pruebas de la API recorren PostgreSQL real (rama Neon de revisión propia, nunca producción);
sin TEST_DATABASE_URL se omiten.

Prueba de mutación documentada (FE-26): ver la cabecera de frontend/tests/pmv/sin-subida.spec.ts
(invertir el valor por omisión del interruptor de la pantalla). En el servidor se invirtió también
el valor por omisión de `evidencia_fisica_activa` (`or _ENCENDIDA`): fallaron
test_apagado_por_omision y test_apagado_upload_url_y_registro_responden_409; se restauró y pasan.
"""
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
if _TEST_URL:
    os.environ["DATABASE_URL"] = _TEST_URL
else:
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://sin-base:sin-base@localhost:1/sin-base")

from features.roadmap.roadmap_service import (  # noqa: E402
    RM_EVIDENCIA_NO_DISPONIBLE,
    EvidenciaFisicaDesconocida,
    evidencia_fisica_activa,
)

RAIZ = Path(__file__).resolve().parents[1]
SUBIDA = "/api/v1/roadmaps/tasks/{tarea}/evidence/upload-url"
REGISTRO = "/api/v1/roadmaps/tasks/{tarea}/evidence"
CUERPO = {"filename": "evidencia.pdf", "mime_type": "application/pdf", "file_size": 1024}
REGISTRO_PARAMS = {"r2_key": "evidencia.pdf", "mime_type": "application/pdf", "file_size": 1024}


# --- Interruptor (sin base) -------------------------------------------------------------------


def test_apagado_por_omision(monkeypatch):
    monkeypatch.delenv("EVIDENCIA_FISICA", raising=False)
    assert evidencia_fisica_activa() is False
    monkeypatch.setenv("EVIDENCIA_FISICA", "")
    assert evidencia_fisica_activa() is False


@pytest.mark.parametrize("valor, esperado", [("true", True), ("TRUE", True), ("false", False)])
def test_valores_admitidos(monkeypatch, valor, esperado):
    monkeypatch.setenv("EVIDENCIA_FISICA", valor)
    assert evidencia_fisica_activa() is esperado


def test_el_codigo_es_409_y_esta_en_el_catalogo():
    from app_core.errors import CATALOGO_ERRORES

    assert RM_EVIDENCIA_NO_DISPONIBLE.status_code == 409
    assert CATALOGO_ERRORES["RM_EVIDENCIA_NO_DISPONIBLE"] is RM_EVIDENCIA_NO_DISPONIBLE


@pytest.mark.parametrize("valor", ["si", "1", "verdadero"])
def test_un_valor_desconocido_falla_al_leerse_y_al_arrancar(monkeypatch, valor):
    monkeypatch.setenv("EVIDENCIA_FISICA", valor)
    with pytest.raises(EvidenciaFisicaDesconocida):
        evidencia_fisica_activa()
    env = {**os.environ, "EVIDENCIA_FISICA": valor,
           "DATABASE_URL": "postgresql+psycopg://sin-base:sin-base@localhost:1/sin-base"}
    r = subprocess.run([sys.executable, "-c", "import features.roadmap.roadmap_service"],
                       cwd=RAIZ, env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode != 0 and "EvidenciaFisicaDesconocida" in r.stderr


# --- API contra PostgreSQL ----------------------------------------------------------------------


def _h(user: str, tenant: str, role: str) -> dict[str, str]:
    return {"X-User-ID": user, "X-Tenant-ID": tenant, "X-Role": role}


@pytest_asyncio.fixture
async def ctx(monkeypatch):
    if not _TEST_URL:
        pytest.skip("TEST_DATABASE_URL no configurada")
    assert "ep-late-hall" not in _TEST_URL, "Se requiere una rama de desarrollo o test (nunca producción)"
    monkeypatch.setenv("AUTH_MODE", "headers")
    monkeypatch.delenv("EVIDENCIA_FISICA", raising=False)
    from app_core.db.session import get_session
    from main import app

    engine = create_async_engine(_TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    tenant = f"fe26-t-{sufijo}"
    usuarios = {rol: f"fe26-{rol[:5]}-{sufijo}" for rol in ("responsable_area", "coordinador", "dpo")}
    async with factory() as s:
        await s.execute(text(
            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:t, :t, :t, :t)"
        ), {"t": tenant})
        for rol, uid in usuarios.items():
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"),
                            {"u": uid, "e": f"{uid}@example.test"})
            await s.execute(text(
                "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"
            ), {"i": str(uuid.uuid4()), "u": uid, "t": tenant, "r": rol})
        await s.commit()

    async def session_override():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = session_override
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield {"client": client, "tenant": tenant, "u": usuarios}
    finally:
        app.dependency_overrides.clear()
        async with factory() as s:
            await s.execute(text("DELETE FROM user_tenant_roles WHERE tenant_id = :t"), {"t": tenant})
            await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": tenant})
            await s.execute(text("DELETE FROM users WHERE id LIKE :p"), {"p": f"fe26-%-{sufijo}"})
            await s.commit()
        await engine.dispose()


def _como(ctx, rol):
    return _h(ctx["u"][rol], ctx["tenant"], rol)


@pytest.mark.parametrize("rol", ["responsable_area", "coordinador"])
@pytest.mark.asyncio
async def test_apagado_upload_url_y_registro_responden_409(ctx, rol):
    r = await ctx["client"].post(SUBIDA.format(tarea="any-task"), json=CUERPO, headers=_como(ctx, rol))
    assert r.status_code == 409, r.text
    assert r.json()["code"] == "RM_EVIDENCIA_NO_DISPONIBLE"
    r = await ctx["client"].post(REGISTRO.format(tarea="any-task"), params=REGISTRO_PARAMS, headers=_como(ctx, rol))
    assert r.status_code == 409, r.text
    assert r.json()["code"] == "RM_EVIDENCIA_NO_DISPONIBLE"


@pytest.mark.asyncio
async def test_apagado_un_rol_sin_permiso_sigue_en_403(ctx):
    r = await ctx["client"].post(SUBIDA.format(tarea="any-task"), json=CUERPO, headers=_como(ctx, "dpo"))
    assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_apagado_la_lista_de_evidencias_sigue_respondiendo(ctx):
    r = await ctx["client"].get(REGISTRO.format(tarea="any-task"), headers=_como(ctx, "coordinador"))
    assert r.status_code != 409 and "RM_EVIDENCIA_NO_DISPONIBLE" not in r.text


@pytest.mark.asyncio
async def test_encendido_se_conserva_la_subida_y_sus_permisos(ctx, monkeypatch):
    monkeypatch.setenv("EVIDENCIA_FISICA", "true")
    r = await ctx["client"].post(SUBIDA.format(tarea="any-task"), json=CUERPO, headers=_como(ctx, "responsable_area"))
    assert r.status_code == 200, r.text
    assert {"url", "key"} <= set(r.json())
    r = await ctx["client"].post(SUBIDA.format(tarea="any-task"), json=CUERPO, headers=_como(ctx, "dpo"))
    assert r.status_code == 403, r.text
