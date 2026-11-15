# ¤conservacion ¤seguridad-tenant ¤arbitro
"""CON-01: políticas de conservación, acta de ejecución con SHA-256 y aislamiento RLS entre inquilinos.

Las pruebas de base de datos corren contra la PostgreSQL 16 local del arnés (TEST_DATABASE_URL) con el rol
`lopdp_app` y se omiten sin ella. Cada prueba lleva en su docstring la mutación que la pone en rojo.
"""
import os
import re
import uuid
from datetime import date, timedelta

import httpx
import pytest
from fastapi import FastAPI

if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or "postgresql+psycopg://u:c@localhost/pruebas"

from app_core.bucle_eventos import configurar_bucle_eventos  # noqa: E402

configurar_bucle_eventos()
from api.errores import ErrorNegocio, error_negocio_handler  # noqa: E402
from app_core.db.session import fijar_contexto_rls, get_session  # noqa: E402
from features.conservacion import conservacion_service as svc  # noqa: E402
from features.conservacion.routes import conservacion_routes as rutas  # noqa: E402

app = FastAPI()
app.add_exception_handler(ErrorNegocio, error_negocio_handler)
app.include_router(svc.router, prefix="/api/v1")
RUTA = "/api/v1/conservacion/politicas"
TODOS_LOS_ROLES = {"admin_organizacion", "dpo", "coordinador", "auditor", "implementador", "responsable_area"}


# Sin base de datos ------------------------------------------------------------------------------
async def _peticion(metodo, ruta, rol, monkeypatch, **kw):
    monkeypatch.setattr(rutas, "modo_autenticacion", lambda: rutas.MODO_HEADERS)

    async def _todos(session, tenant_id, usuario):
        return TODOS_LOS_ROLES

    monkeypatch.setattr(rutas, "roles_activos", _todos)
    app.dependency_overrides[get_session] = lambda: None
    cabeceras = {"X-User-ID": "u", "X-Tenant-ID": "t", "X-Role": rol}
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://p") as api:
            return await api.request(metodo, ruta, headers=cabeceras, **kw)
    finally:
        app.dependency_overrides.clear()


def test_rutas_expuestas():
    """Mutación: añadir un DELETE o quitar /ejecutar → rojo."""
    rutas_http = {(r.path, tuple(sorted(r.methods))) for r in svc.router.routes}
    assert rutas_http == {
        ("/conservacion/politicas", ("GET",)),
        ("/conservacion/politicas", ("POST",)),
        ("/conservacion/politicas/{politica_id}/ejecutar", ("POST",)),
    }


@pytest.mark.asyncio
async def test_roles_por_operacion(monkeypatch):
    """Mutación: abrir el alta o /ejecutar al DPO, o cerrar la consulta a un rol de lectura → rojo."""
    assert svc.ROLES_CONSULTA == ("admin_organizacion", "implementador", "dpo", "coordinador", "auditor")
    assert svc.ROLES_EJECUCION == ("admin_organizacion", "implementador")
    assert (await _peticion("GET", RUTA, "responsable_area", monkeypatch)).status_code == 403
    ruta = f"{RUTA}/{uuid.uuid4()}/ejecutar"
    for rol in ("dpo", "coordinador", "auditor", "responsable_area"):
        assert (await _peticion("POST", ruta, rol, monkeypatch)).status_code == 403, rol
        assert (await _peticion("POST", RUTA, rol, monkeypatch, json={})).status_code == 403, rol


def test_codigos_de_error_registrados():
    """Mutación: cambiar el estado HTTP de CONSERVACION_YA_EJECUTADA (409) o quitar un código → rojo."""
    from app_core.errors import CATALOGO_ERRORES

    esperado = {
        "CONSERVACION_POLITICA_NO_ENCONTRADA": 404,
        "CONSERVACION_PLAZO_INVALIDO": 422,
        "CONSERVACION_YA_EJECUTADA": 409,
    }
    for codigo, estado in esperado.items():
        assert CATALOGO_ERRORES[codigo].status_code == estado, codigo


def test_sumar_meses_ajusta_fin_de_mes():
    """Mutación: sumar días en vez de meses calendario → rojo."""
    assert svc._sumar_meses(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert svc._sumar_meses(date(2026, 11, 15), 24) == date(2028, 11, 15)


def test_semaforo_umbral_por_vencer():
    """Mutación: escribir 30 fuera de DIAS_POR_VENCER o comparar con < en vez de <= → rojo."""
    hoy = date(2026, 11, 15)
    for dias, esperado in ((31, "vigente"), (30, "por_vencer"), (1, "por_vencer"), (0, "vencida"), (-5, "vencida")):
        assert svc.semaforo_de(hoy + timedelta(days=dias), hoy) == esperado, dias
    assert svc.DIAS_POR_VENCER == 30


# Base de datos ----------------------------------------------------------------------------------
_URL = os.environ.get("TEST_DATABASE_URL", "")
_con_bd = pytest.mark.skipif(not _URL, reason="TEST_DATABASE_URL no configurada")


def _url_async() -> str:
    return _URL.replace("postgresql://", "postgresql+psycopg://", 1) if _URL.startswith("postgresql://") else _URL


async def _con_lopdp_app(cuerpo):
    """Dos organizaciones nuevas y una sesión con lopdp_app dentro de una transacción que se deshace."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

    from tests.conftest import exigir_base_de_pruebas

    exigir_base_de_pruebas()
    engine = create_async_engine(_url_async(), hide_parameters=True)
    sufijo = uuid.uuid4().hex[:10]
    a, b = f"con01-a-{sufijo}", f"con01-b-{sufijo}"
    try:
        async with engine.connect() as conexion:
            transaccion = await conexion.begin()
            try:
                for t in (a, b):
                    await conexion.execute(
                        text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                             "VALUES (:t, :t, :t, :t)"), {"t": t},
                    )
                await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
                async with AsyncSession(bind=conexion, expire_on_commit=False,
                                        join_transaction_mode="create_savepoint") as s:
                    await cuerpo(s, a, b)
            finally:
                await transaccion.rollback()
    finally:
        await engine.dispose()


async def _actividad(s, tenant) -> str:
    """Actividad real del RAT del inquilino, creada por la compuerta del RAT."""
    from features.rat import rat_service
    from features.rat.domain.models import ActividadRAT

    await fijar_contexto_rls(s, tenant, None)
    actividad = ActividadRAT(tenant_id=tenant, codigo="RAT-CON01", nombre="Nómina", area_responsable="RRHH",
                             finalidad="Pago de nómina", medio_soporte="digital", plazo_conservacion="24 meses",
                             nivel_riesgo="bajo")
    return (await rat_service.registrar_actividad_rat(s, actividad)).id


def _codigo(exc_info):
    return exc_info.value.code, exc_info.value.status_code


@_con_bd
@pytest.mark.asyncio
async def test_ciclo_politica_conservacion_y_bloqueo():
    """Mutación: no calcular el hash, no pasar a BLOQUEADA o permitir una segunda ejecución → rojo."""

    async def cuerpo(s, a, b):
        rat_id = await _actividad(s, a)
        entrada = svc.PoliticaEntrada(actividad_rat_id=rat_id, plazo_meses=24, accion_vencimiento="BLOQUEO")
        creada = await svc.crear_politica(s, a, entrada, None)
        assert creada.estado == "ACTIVA" and creada.acta_ejecucion_hash is None and creada.semaforo == "vigente"
        assert creada.fecha_proxima_revision > date.today() + timedelta(days=700)
        ejecutada = await svc.ejecutar_politica(s, a, creada.id, None)
        assert ejecutada.estado == "BLOQUEADA"
        assert re.fullmatch(r"[0-9a-f]{64}", ejecutada.acta_ejecucion_hash)
        with pytest.raises(ErrorNegocio) as exc:
            await svc.ejecutar_politica(s, a, creada.id, None)
        assert _codigo(exc) == ("CONSERVACION_YA_EJECUTADA", 409)
        listada = (await svc.listar_politicas(s, a))[0]
        assert listada.acta_ejecucion_hash == ejecutada.acta_ejecucion_hash  # el acta no cambia

    await _con_lopdp_app(cuerpo)


@_con_bd
@pytest.mark.asyncio
async def test_anonimizacion_queda_ejecutada_y_plazo_invalido():
    """Mutación: aceptar plazo_meses <= 0 o dejar la anonimización en BLOQUEADA → rojo."""

    async def cuerpo(s, a, b):
        rat_id = await _actividad(s, a)
        for plazo in (0, -3):
            with pytest.raises(ErrorNegocio) as exc:
                await svc.crear_politica(
                    s, a, svc.PoliticaEntrada(actividad_rat_id=rat_id, plazo_meses=plazo,
                                              accion_vencimiento="SUPRESION"), None)
            assert _codigo(exc) == ("CONSERVACION_PLAZO_INVALIDO", 422)
        creada = await svc.crear_politica(
            s, a, svc.PoliticaEntrada(actividad_rat_id=rat_id, plazo_meses=12,
                                      accion_vencimiento="ANONIMIZACION"), None)
        assert (await svc.ejecutar_politica(s, a, creada.id, None)).estado == "EJECUTADA"
        with pytest.raises(ErrorNegocio) as exc:
            await svc.ejecutar_politica(s, a, str(uuid.uuid4()), None)
        assert _codigo(exc) == ("CONSERVACION_POLITICA_NO_ENCONTRADA", 404)

    await _con_lopdp_app(cuerpo)


@_con_bd
@pytest.mark.asyncio
async def test_actividad_debe_existir_en_el_rat_del_tenant():
    """Mutación: no verificar la actividad por el pasillo del RAT, o verificarla sin el inquilino → rojo."""

    async def cuerpo(s, a, b):
        rat_a = await _actividad(s, a)
        await fijar_contexto_rls(s, b, None)
        with pytest.raises(ErrorNegocio) as exc:  # la actividad existe, pero es de A
            await svc.crear_politica(
                s, b, svc.PoliticaEntrada(actividad_rat_id=rat_a, plazo_meses=6, accion_vencimiento="BLOQUEO"), None)
        assert _codigo(exc) == ("CONSERVACION_ACTIVIDAD_NO_ENCONTRADA", 404)

    await _con_lopdp_app(cuerpo)


@_con_bd
@pytest.mark.asyncio
async def test_vencimiento_se_expone_al_cockpit_por_los_pasillos():
    """Mutación: incluir políticas ya ejecutadas o futuras en las vencidas → rojo."""
    from app_core.pasillo import conservacion as pasillo

    async def cuerpo(s, a, b):
        rat_id = await _actividad(s, a)
        ayer, manana = date.today() - timedelta(days=1), date.today() + timedelta(days=1)
        vencida = await svc.crear_politica(s, a, svc.PoliticaEntrada(
            actividad_rat_id=rat_id, plazo_meses=1, accion_vencimiento="BLOQUEO", fecha_proxima_revision=ayer), None)
        await svc.crear_politica(s, a, svc.PoliticaEntrada(
            actividad_rat_id=rat_id, plazo_meses=1, accion_vencimiento="BLOQUEO", fecha_proxima_revision=manana), None)
        ya = await svc.crear_politica(s, a, svc.PoliticaEntrada(
            actividad_rat_id=rat_id, plazo_meses=1, accion_vencimiento="BLOQUEO", fecha_proxima_revision=ayer), None)
        await svc.ejecutar_politica(s, a, ya.id, None)
        assert [p.id for p in await pasillo.listar_politicas_vencidas(s, a)] == [vencida.id]
        alertas = await svc.alertas_vencimiento(s, a)
        assert [x.politica_id for x in alertas] == [vencida.id]

    await _con_lopdp_app(cuerpo)


@_con_bd
@pytest.mark.asyncio
async def test_conservacion_rls_aislamiento_tenant():
    """Mutación: política RLS con USING (true), o conceder DELETE a lopdp_app → rojo."""
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    async def cuerpo(s, a, b):
        rat_id = await _actividad(s, a)
        await svc.crear_politica(
            s, a, svc.PoliticaEntrada(actividad_rat_id=rat_id, plazo_meses=24, accion_vencimiento="BLOQUEO"), None)
        assert len(await svc.listar_politicas(s, a)) == 1
        await fijar_contexto_rls(s, b, None)
        assert await svc.listar_politicas(s, b) == []
        assert (await s.execute(text("SELECT count(*) FROM politicas_conservacion"))).scalar() == 0
        with pytest.raises(DBAPIError):  # B no inserta filas de A
            async with s.begin_nested():
                await s.execute(text(
                    "INSERT INTO politicas_conservacion (tenant_id, actividad_rat_id, plazo_meses, "
                    "accion_vencimiento, fecha_proxima_revision) VALUES (:t, 'x', 1, 'BLOQUEO', now())"), {"t": a})
        with pytest.raises(DBAPIError):  # lopdp_app no borra
            async with s.begin_nested():
                await s.execute(text("DELETE FROM politicas_conservacion"))

    await _con_lopdp_app(cuerpo)


@_con_bd
@pytest.mark.asyncio
async def test_acta_recalculable_desde_auditoria():
    """Mutación: dejar `ejecutada_en` fuera del payload del evento, o hashear otra forma del acta → rojo."""
    import json

    from sqlalchemy import text

    async def cuerpo(s, a, b):
        rat_id = await _actividad(s, a)
        creada = await svc.crear_politica(
            s, a, svc.PoliticaEntrada(actividad_rat_id=rat_id, plazo_meses=24, accion_vencimiento="BLOQUEO"), None)
        ejecutada = await svc.ejecutar_politica(s, a, creada.id, None)
        payload = (await s.execute(text(
            "SELECT payload FROM audit_events WHERE entity_type = 'politica_conservacion' "
            "AND entity_id = :i AND action = 'politica_ejecutada'"), {"i": creada.id})).scalar()
        payload = json.loads(payload) if isinstance(payload, str) else payload
        assert payload["acta"]["ejecutada_en"]
        assert svc.hash_acta(payload["acta"]) == payload["acta_ejecucion_hash"] == ejecutada.acta_ejecucion_hash

    await _con_lopdp_app(cuerpo)
