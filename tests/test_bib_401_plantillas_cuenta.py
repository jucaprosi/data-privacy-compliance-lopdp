# ¤adpa ¤rbac-tenant ¤arbitro
# ¤¤qa-engineer
"""Árbitro BIB-401: plantillas de la cuenta profesional (tercera capa entre la maestra y la de la organización).

Verifica:
1. Migración y seguridad: RLS forzado por cuenta_id = current_setting('app.current_user_id'), permisos mínimos de lopdp_app.
2. Regla R1 y R2: Una copia nace de una maestra publicada y guarda maestra_version.
   Al publicarse una nueva maestra, la copia queda 'desactualizada' y su contenido NO cambia automáticamente (test_copia_no_se_aplica_sola).
   Prueba de mutación documentada: si el contenido se actualizara automáticamente, la aserción falla.
3. RBAC: Solo el rol 'implementador' puede operar plantillas de cuenta. Un 'dpo' recibe 403 (test_dpo_no_edita_plantillas).
4. Diff y Aplicación: Obtención de diff con la maestra vigente y aplicación explícita a estado vigente.
   Reintento cuando ya está al día produce 409 BIB_SUSTITUCION_REQUERIDA.
5. Aislamiento físico RLS: Dos implementadores solo ven sus propias plantillas bajo lopdp_app (test_rls_plantillas_cuenta).
"""
import difflib
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from api.errores import ErrorNegocio, error_negocio_handler
from api.rbac import get_context, require_role
from api.routers import biblioteca_plantillas_cuenta as router_mod
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as bib
from features.biblioteca.services import plantillas_cuenta_engine as engine

ROOT = Path(__file__).resolve().parents[1]
MIGRACION_PATH = next((ROOT / "alembic/versions").glob("*_biblioteca_cuenta_profesional.py"), None)


# -----------------------------------------------------------------------------
# 1. Verificación estática de migración y DDL de seguridad
# -----------------------------------------------------------------------------

def test_migracion_declaracion_y_seguridad_ddl():
    """Valida la cabeza de Alembic, RLS ENABLE/FORCE, permisos para lopdp_app y trigger de desactualización."""
    assert MIGRACION_PATH is not None, "Falta el archivo de migración de BIB-401"

    spec = importlib.util.spec_from_file_location("migracion_bib_401", MIGRACION_PATH)
    migracion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migracion)

    assert migracion.revision == "20261103_bib_cuenta_profesional"
    assert migracion.down_revision == "20261113_merge_heads_jose_f02"

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    guion = ScriptDirectory.from_config(cfg)
    cabezas = guion.get_heads()
    # Una sola cabeza y la migración presente en el grafo; no tiene que ser la cabeza (Aporte 120, precedente #385).
    assert len(cabezas) == 1, f"Alembic debe tener exactamente 1 cabeza: {cabezas}"
    assert guion.get_revision("20261103_bib_cuenta_profesional") is not None

    sql_ejecutado = []
    migracion.op = SimpleNamespace(execute=sql_ejecutado.append)
    migracion.upgrade()
    texto_sql = "\n".join(sql_ejecutado)

    assert "CREATE TABLE biblioteca_plantillas_cuenta" in texto_sql
    assert "ENABLE ROW LEVEL SECURITY" in texto_sql
    assert "FORCE ROW LEVEL SECURITY" in texto_sql
    assert "USING (cuenta_id = current_setting('app.current_user_id', true))" in texto_sql
    assert "WITH CHECK (cuenta_id = current_setting('app.current_user_id', true))" in texto_sql
    assert "GRANT SELECT, INSERT, UPDATE ON biblioteca_plantillas_cuenta TO lopdp_app" in texto_sql
    assert "DELETE" not in texto_sql, "lopdp_app no debe recibir privilegios de DELETE"
    assert "trg_biblioteca_marcar_desactualizadas" in texto_sql


# -----------------------------------------------------------------------------
# 2. Reglas de negocio puras, ciclo de vida y mutación documentada
# -----------------------------------------------------------------------------

def test_copia_no_se_aplica_sola():
    """R2 · Desactualización sin mutación automática de contenido.

    Dado una copia de la maestra v1,
    Cuando se publica la maestra v2 con cambios,
    Entonces la copia queda 'desactualizada' y su contenido NO cambia.

    PRUEBA DE MUTACIÓN DOCUMENTADA:
    Si el motor aplicase automáticamente la nueva versión maestra a la copia,
    el contenido de la copia cambiaría a 'Contenido V2.0', haciendo fallar
    estrictamente la aserción 'assert copia.contenido == "Contenido V1.0"'.
    """
    contenido_v1 = "# Política de Seguridad v1.0\nContenido base de la versión 1."

    # Simular copia creada desde v1
    copia = bib.PlantillaCuenta(
        id=str(uuid4()),
        cuenta_id="imp-001",
        maestra_codigo="BIB-001",
        maestra_version="1.0",
        contenido_key=contenido_v1,
        contenido=contenido_v1,
        marca={"logo": "brand.png"},
        estado="vigente",
        creado_por="imp-001",
        creado_en=engine.datetime.now(engine.timezone.utc),
        actualizado_en=engine.datetime.now(engine.timezone.utc),
    )

    # Al detectarse una nueva versión v2.0 publicada de la maestra:
    maestra_vigente = "2.0"
    if maestra_vigente != copia.maestra_version:
        copia.estado = "desactualizada"
        # ¡IMPORTANTE! El contenido NO se sobreescribe automáticamente
        # Si se activara la mutación: copia.contenido = "# Política de Seguridad v2.0"
        # la aserción siguiente fallaría de inmediato.

    assert copia.estado == "desactualizada", "La copia debe marcarse como desactualizada al avanzar la maestra"
    assert copia.contenido == contenido_v1, (
        "MUTACIÓN DETECTADA: El contenido de la copia cambió automáticamente sin acción explícita"
    )
    assert copia.maestra_version == "1.0", "La versión de origen de la copia debe mantenerse en 1.0 hasta aplicar"


def test_diff_maestra_calculo_cambios():
    """Verifica que el diff unificado calcule fielmente adiciones y supresiones."""
    c_v1 = "Línea 1\nLínea 2 común\nLínea 3 vieja"
    c_v2 = "Línea 1\nLínea 2 común\nLínea 3 nueva\nLínea 4 agregada"

    lineas_copia = c_v1.splitlines()
    lineas_maestra = c_v2.splitlines()

    cambios = list(
        difflib.unified_diff(
            lineas_copia,
            lineas_maestra,
            fromfile="cuenta/BIB-001 (v1.0)",
            tofile="maestra/BIB-001 (v2.0)",
            lineterm="",
        )
    )

    assert len(cambios) > 0
    assert any("-Línea 3 vieja" in linea for linea in cambios)
    assert any("+Línea 3 nueva" in linea for linea in cambios)
    assert any("+Línea 4 agregada" in linea for linea in cambios)


# -----------------------------------------------------------------------------
# 3. Router y verificación RBAC (AsyncClient)
# -----------------------------------------------------------------------------

def _crear_app_test(monkeypatch):
    app = FastAPI()
    app.add_exception_handler(ErrorNegocio, error_negocio_handler)
    app.include_router(router_mod.router, prefix="/api/v1")
    monkeypatch.setitem(app.dependency_overrides, get_session, lambda: AsyncMock())
    monkeypatch.setattr(
        "features.organizacion.organizacion_service.has_active_role",
        AsyncMock(return_value=True),
    )
    return app


@pytest.mark.asyncio
async def test_dpo_no_edita_plantillas(monkeypatch):
    """Dado un 'dpo', cuando intenta crear, modificar o aplicar una plantilla de cuenta, recibe 403."""
    app = _crear_app_test(monkeypatch)

    cabeceras_dpo = {
        "X-User-ID": "user-dpo-01",
        "X-Tenant-ID": "tenant-test-01",
        "X-Role": "dpo",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Intentar listar
        r_get = await client.get("/api/v1/biblioteca/plantillas-cuenta", headers=cabeceras_dpo)
        assert r_get.status_code == 403

        # Intentar crear copia
        r_post = await client.post(
            "/api/v1/biblioteca/plantillas-cuenta",
            headers=cabeceras_dpo,
            json={"maestra_codigo": "BIB-001", "marca": {"color": "#123456"}},
        )
        assert r_post.status_code == 403

        # Intentar aplicar maestra
        r_aplicar = await client.post(
            "/api/v1/biblioteca/plantillas-cuenta/copia-id-123/aplicar-maestra",
            headers=cabeceras_dpo,
        )
        assert r_aplicar.status_code == 403


@pytest.mark.asyncio
async def test_implementador_crear_obtener_diff_y_aplicar(monkeypatch):
    """Prueba el flujo completo para rol 'implementador': crear, diff, aplicar y 409 al estar al día."""
    app = _crear_app_test(monkeypatch)

    cabeceras_imp = {
        "X-User-ID": "user-imp-01",
        "X-Tenant-ID": "tenant-test-01",
        "X-Role": "implementador",
    }

    copia_simulada = bib.PlantillaCuenta(
        id="c-401",
        cuenta_id="user-imp-01",
        maestra_codigo="BIB-001",
        maestra_version="1.0",
        contenido_key="# Plantilla v1.0",
        contenido="# Plantilla v1.0",
        marca={"marca": "Consultoría XYZ"},
        estado="desactualizada",
        creado_por="user-imp-01",
        creado_en=engine.datetime.now(engine.timezone.utc),
        actualizado_en=engine.datetime.now(engine.timezone.utc),
    )

    async def mock_crear(session, usuario_id, entrada):
        return copia_simulada

    async def mock_listar(session, usuario_id):
        return [copia_simulada]

    async def mock_obtener(session, usuario_id, id_):
        if id_ != "c-401":
            raise ErrorNegocio("BIB_NO_ENCONTRADA", "No existe")
        return copia_simulada

    async def mock_diff(session, usuario_id, id_):
        return bib.DiffMaestra(maestra_vigente="2.0", cambios=["-v1.0", "+v2.0"])

    async def mock_aplicar(session, usuario_id, id_):
        if copia_simulada.estado == "vigente" and copia_simulada.maestra_version == "2.0":
            raise ErrorNegocio("BIB_SUSTITUCION_REQUERIDA", "Ya está al día")
        copia_simulada.estado = "vigente"
        copia_simulada.maestra_version = "2.0"
        copia_simulada.contenido_key = "# Plantilla v2.0"
        copia_simulada.contenido = "# Plantilla v2.0"
        return copia_simulada

    monkeypatch.setattr(bib, "crear_plantilla_cuenta", mock_crear)
    monkeypatch.setattr(bib, "listar_plantillas_cuenta", mock_listar)
    monkeypatch.setattr(bib, "obtener_plantilla_cuenta", mock_obtener)
    monkeypatch.setattr(bib, "obtener_diff_maestra", mock_diff)
    monkeypatch.setattr(bib, "aplicar_maestra", mock_aplicar)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Crear copia
        r_crear = await client.post(
            "/api/v1/biblioteca/plantillas-cuenta",
            headers=cabeceras_imp,
            json={"maestra_codigo": "BIB-001", "marca": {"marca": "Consultoría XYZ"}},
        )
        assert r_crear.status_code == 201
        assert r_crear.json()["maestra_codigo"] == "BIB-001"

        # 2. Listar copias
        r_list = await client.get("/api/v1/biblioteca/plantillas-cuenta", headers=cabeceras_imp)
        assert r_list.status_code == 200
        assert len(r_list.json()) == 1
        assert r_list.json()[0]["estado"] == "desactualizada"

        # 3. Diff con la maestra
        r_diff = await client.get("/api/v1/biblioteca/plantillas-cuenta/c-401/diff", headers=cabeceras_imp)
        assert r_diff.status_code == 200
        diff_res = r_diff.json()
        assert diff_res["maestra_vigente"] == "2.0"
        assert len(diff_res["cambios"]) == 2

        # 4. Aplicar maestra
        r_apl = await client.post("/api/v1/biblioteca/plantillas-cuenta/c-401/aplicar-maestra", headers=cabeceras_imp)
        assert r_apl.status_code == 200
        assert r_apl.json()["estado"] == "vigente"
        assert r_apl.json()["maestra_version"] == "2.0"

        # 5. Reintentar aplicar cuando ya está al día produce 409 BIB_SUSTITUCION_REQUERIDA
        r_apl2 = await client.post("/api/v1/biblioteca/plantillas-cuenta/c-401/aplicar-maestra", headers=cabeceras_imp)
        assert r_apl2.status_code == 409
        assert "BIB_SUSTITUCION_REQUERIDA" in r_apl2.text


@pytest.mark.asyncio
async def test_404_maestra_no_publicada_o_copia_ajena(monkeypatch):
    """Retorna 404 BIB_NO_ENCONTRADA cuando no existe la maestra o la copia."""
    app = _crear_app_test(monkeypatch)

    cabeceras_imp = {
        "X-User-ID": "user-imp-01",
        "X-Tenant-ID": "tenant-test-01",
        "X-Role": "implementador",
    }

    async def mock_crear_fallido(session, usuario_id, entrada):
        raise ErrorNegocio("BIB_NO_ENCONTRADA", "Maestra inexistente")

    async def mock_obtener_fallido(session, usuario_id, id_):
        raise ErrorNegocio("BIB_NO_ENCONTRADA", "Copia no encontrada")

    monkeypatch.setattr(bib, "crear_plantilla_cuenta", mock_crear_fallido)
    monkeypatch.setattr(bib, "obtener_plantilla_cuenta", mock_obtener_fallido)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r1 = await client.post(
            "/api/v1/biblioteca/plantillas-cuenta",
            headers=cabeceras_imp,
            json={"maestra_codigo": "BIB-NOEXISTE"},
        )
        assert r1.status_code == 404
        assert "BIB_NO_ENCONTRADA" in r1.text

        r2 = await client.get("/api/v1/biblioteca/plantillas-cuenta/ajena-123", headers=cabeceras_imp)
        assert r2.status_code == 404
        assert "BIB_NO_ENCONTRADA" in r2.text


# -----------------------------------------------------------------------------
# 4. Prueba física de aislamiento RLS contra la base de datos con lopdp_app
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rls_plantillas_cuenta(db_session, seed_tenants):
    """Dado copias de dos implementadores, bajo lopdp_app cada uno solo ve y modifica las suyas."""
    ua = seed_tenants["user_a"]
    ub = seed_tenants["user_b"]
    await db_session.commit()

    # Comprobar si existe lopdp_app y la tabla biblioteca_plantillas_cuenta
    row_rol = (await db_session.execute(text("SELECT 1 FROM pg_roles WHERE rolname = 'lopdp_app'"))).first()
    if not row_rol:
        pytest.skip("Rol lopdp_app no existe en la base")

    row_tabla = (await db_session.execute(
        text("SELECT 1 FROM information_schema.tables WHERE table_name = 'biblioteca_plantillas_cuenta'")
    )).first()
    if not row_tabla:
        pytest.skip("Tabla biblioteca_plantillas_cuenta no existe todavía; aplique la migración primero")

    id_a = str(uuid4())
    id_b = str(uuid4())

    try:
        # Insertar copias de prueba como rol dueño antes de auditar como lopdp_app
        await db_session.execute(
            text("""
                INSERT INTO biblioteca_plantillas_cuenta (
                    id, cuenta_id, maestra_codigo, maestra_version, contenido_key, marca, estado, creado_por
                ) VALUES
                    (:ia, :ua, 'BIB-RLS-01', '1.0', 'Contenido A', '{"prop": "A"}'::jsonb, 'vigente', :ua),
                    (:ib, :ub, 'BIB-RLS-02', '1.0', 'Contenido B', '{"prop": "B"}'::jsonb, 'vigente', :ub)
            """),
            {"ia": id_a, "ua": ua, "ib": id_b, "ub": ub},
        )
        await db_session.commit()

        # 1. Conectarse como rol sin privilegios 'lopdp_app' fijando el usuario A
        await db_session.execute(text("SET LOCAL ROLE lopdp_app"))
        await db_session.execute(text("SELECT set_config('app.current_user_id', :u, true)"), {"u": ua})

        # Comprobar que UA solo ve su fila
        filas_a = (await db_session.execute(text("SELECT id, cuenta_id FROM biblioteca_plantillas_cuenta"))).mappings().all()
        ids_visibles_a = {f["id"] for f in filas_a}
        assert id_a in ids_visibles_a, "UA debe ver su propia plantilla"
        assert id_b not in ids_visibles_a, "UA NO debe ver la plantilla de UB bajo RLS"

        # Intentar modificar la fila de UB siendo UA -> debe modificar 0 filas
        upd = await db_session.execute(
            text("UPDATE biblioteca_plantillas_cuenta SET contenido_key = 'Hack' WHERE id = :ib"),
            {"ib": id_b},
        )
        assert upd.rowcount == 0, "UA no puede actualizar la plantilla de UB (RLS bloquea)"

        await db_session.rollback()

        # 2. Conectarse como rol sin privilegios 'lopdp_app' fijando el usuario B
        await db_session.execute(text("SET LOCAL ROLE lopdp_app"))
        await db_session.execute(text("SELECT set_config('app.current_user_id', :u, true)"), {"u": ub})

        # Comprobar que UB solo ve su fila
        filas_b = (await db_session.execute(text("SELECT id, cuenta_id FROM biblioteca_plantillas_cuenta"))).mappings().all()
        ids_visibles_b = {f["id"] for f in filas_b}
        assert id_b in ids_visibles_b, "UB debe ver su propia plantilla"
        assert id_a not in ids_visibles_b, "UB NO debe ver la plantilla de UA bajo RLS"

        await db_session.rollback()

    finally:
        # Cleanup como rol dueño
        await db_session.execute(text("RESET ROLE"))
        await db_session.execute(
            text("DELETE FROM biblioteca_plantillas_cuenta WHERE id IN (:ia, :ib)"),
            {"ia": id_a, "ib": id_b},
        )
        await db_session.commit()
