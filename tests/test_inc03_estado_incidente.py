# ¤incidentes ¤rbac-tenant ¤arbitro
"""INC-03: el estado del incidente son eventos que solo se agregan; contador de abiertos.

Contra la PostgreSQL 16 de pruebas migrada (TEST_DATABASE_URL), con el rol lopdp_app y RLS. Valores
simulados; correos .invalid. Cada prueba lleva en su docstring la mutación que la pone en rojo.
"""
import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

_URL = os.environ.get("TEST_DATABASE_URL", "")
if not _URL:
    pytest.skip("TEST_DATABASE_URL no configurada", allow_module_level=True)

from api.rbac import get_usuario_autenticado  # noqa: E402
from app_core.db.session import fijar_contexto_rls, get_session  # noqa: E402
from app_core.pasillo import incidentes as pasillo  # noqa: E402
from features.incidentes import incidentes_service as inc  # noqa: E402
from main import app  # noqa: E402

RUTA = "/api/v1/incidentes"
ROLES_QUE_CAMBIAN = ("admin_organizacion", "coordinador", "responsable_area", "implementador")
MOTIVO = "Contención verificada por el equipo"


def _url_async() -> str:
    return _URL.replace("postgresql://", "postgresql+psycopg://", 1) if _URL.startswith("postgresql://") else _URL


async def _preparar(conexion, sufijo: str) -> dict:
    """Dos organizaciones, un usuario por rol en A y un coordinador en B (como dueño; luego lopdp_app)."""
    a, b = f"inc03-a-{sufijo}", f"inc03-b-{sufijo}"
    usuarios = {rol: (f"inc03-{rol[:6]}-{sufijo}", a, rol) for rol in (*ROLES_QUE_CAMBIAN, "dpo")}
    usuarios["coord_b"] = (f"inc03-coordb-{sufijo}", b, "coordinador")
    for t in (a, b):
        await conexion.execute(
            text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:t, :t, :t, :t)"),
            {"t": t},
        )
    for uid, tenant, rol in usuarios.values():
        await conexion.execute(
            text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"), {"u": uid, "e": f"{uid}@correo.invalid"}
        )
        await conexion.execute(
            text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"),
            {"i": str(uuid.uuid4()), "u": uid, "t": tenant, "r": rol},
        )
    return {"a": a, "b": b, "u": usuarios}


@pytest_asyncio.fixture
async def mundo():
    """Todo dentro de una transacción que se revierte: nada queda en la base."""
    engine = create_async_engine(_url_async(), hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            datos = await _preparar(conexion, uuid.uuid4().hex[:10])
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False, join_transaction_mode="create_savepoint") as s:
                yield {"s": s, **datos}
        finally:
            await transaccion.rollback()
    await engine.dispose()


async def _registrar(mundo, tenant="a", rol="coordinador", **cambios):
    uid, t, _ = mundo["u"][rol] if tenant == "a" else mundo["u"]["coord_b"]
    base = dict(
        fecha_deteccion=datetime.now(timezone.utc) - timedelta(hours=2),
        titulo="Acceso no autorizado simulado",
        descripcion="Consultas masivas simuladas.",
        severidad="Alta",
        afecta_datos_personales=True,
        categorias_datos=["Contacto (Email / Teléfono)"],
        medidas_inmediatas="Credencial revocada.",
    )
    return await inc.registrar_incidente(mundo["s"], t, uid, **{**base, **cambios})


def _actor(mundo, clave):
    return mundo["u"][clave]


async def _post(mundo, clave, incidente_id, accion, cuerpo=None, tenant=None):
    uid, t, rol = _actor(mundo, clave)

    async def sesion():
        yield mundo["s"]

    app.dependency_overrides[get_session] = sesion
    app.dependency_overrides[get_usuario_autenticado] = lambda: uid
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://prueba") as api:
            return await api.post(
                f"{RUTA}/{incidente_id}/{accion}",
                headers={"X-Tenant-ID": tenant or t, "X-Role": rol},
                json={"motivo": MOTIVO} if cuerpo is None else cuerpo,
            )
    finally:
        app.dependency_overrides.pop(get_session, None)
        app.dependency_overrides.pop(get_usuario_autenticado, None)


@pytest.fixture(autouse=True)
def _oidc(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "oidc")


# m1 ---------------------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_m1_estado_es_el_del_ultimo_evento_y_el_contador_lo_sigue(mundo):
    """Mutación: calcular el estado con el primer evento en vez del último → rojo."""
    s = mundo["s"]
    uid, t, _ = _actor(mundo, "coordinador")
    i1, i2 = await _registrar(mundo), await _registrar(mundo, titulo="Otro incidente simulado")
    assert (await inc.estado_de(s, t, i1.id)).estado == "abierto"
    assert await pasillo.contar_abiertos(s, t) == 2

    await inc.cerrar_incidente(s, t, uid, i1.id, MOTIVO)
    assert (await inc.estado_de(s, t, i1.id)).estado == "cerrado"
    assert await pasillo.contar_abiertos(s, t) == 1

    await inc.reabrir_incidente(s, t, uid, i1.id, MOTIVO)
    assert (await inc.estado_de(s, t, i1.id)).estado == "abierto"
    assert await pasillo.contar_abiertos(s, t) == 2

    await inc.cerrar_incidente(s, t, uid, i1.id, MOTIVO)
    assert (await inc.estado_de(s, t, i1.id)).estado == "cerrado"
    assert (await inc.estado_de(s, t, i1.id)).ultima_secuencia == 3
    assert (await inc.estado_de(s, t, i2.id)).estado == "abierto"
    assert await pasillo.contar_abiertos(s, t) == 1


# m2 ---------------------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_m2_cerrar_dos_veces_o_reabrir_lo_abierto_es_409(mundo):
    """Mutación: quitar la comprobación de transición → rojo."""
    incidente = await _registrar(mundo)
    r = await _post(mundo, "coordinador", incidente.id, "reabrir")
    assert r.status_code == 409 and r.json()["code"] == "INCIDENTE_YA_ABIERTO", r.text
    assert (await _post(mundo, "coordinador", incidente.id, "cerrar")).status_code == 200
    r = await _post(mundo, "coordinador", incidente.id, "cerrar")
    assert r.status_code == 409 and r.json()["code"] == "INCIDENTE_YA_CERRADO", r.text


@pytest.mark.asyncio
async def test_incidente_inexistente_o_de_otra_organizacion_es_404(mundo):
    ajeno = await _registrar(mundo, tenant="b")
    r = await _post(mundo, "coordinador", ajeno.id, "cerrar")
    assert r.status_code == 404 and r.json()["code"] == "INCIDENTE_NO_ENCONTRADO", r.text
    assert (await _post(mundo, "coordinador", str(uuid.uuid4()), "cerrar")).status_code == 404


# m3 ---------------------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_m3_dos_cierres_concurrentes_uno_pasa_y_el_otro_409():
    """Mutación: quitar UNIQUE (incidente_id, secuencia) → rojo (los dos pasan)."""
    engine = create_async_engine(_url_async(), hide_parameters=True)
    sufijo = uuid.uuid4().hex[:10]
    async with engine.connect() as dueno:
        datos = await _preparar(dueno, sufijo)
        await dueno.commit()
    uid, tenant, _ = datos["u"]["coordinador"]
    try:
        async with AsyncSession(engine, expire_on_commit=False) as s0:
            await s0.execute(text("SET LOCAL ROLE lopdp_app"))
            await fijar_contexto_rls(s0, tenant, uid)
            incidente = await inc.registrar_incidente(
                s0, tenant, uid, fecha_deteccion=datetime.now(timezone.utc) - timedelta(hours=1), titulo="Concurrencia",
                descripcion="", severidad="Baja", afecta_datos_personales=False, categorias_datos=[],
                medidas_inmediatas="",
            )
            await s0.commit()

        s1, s2 = AsyncSession(engine, expire_on_commit=False), AsyncSession(engine, expire_on_commit=False)
        try:
            for s in (s1, s2):
                await s.execute(text("SET LOCAL ROLE lopdp_app"))
            await inc.cerrar_incidente(s1, tenant, uid, incidente.id, MOTIVO)  # sin commit: retiene la secuencia 1
            segundo = asyncio.create_task(inc.cerrar_incidente(s2, tenant, uid, incidente.id, MOTIVO))
            await asyncio.sleep(0.5)
            await s1.commit()
            with pytest.raises(inc.TransicionInvalida) as error:
                await segundo
            assert error.value.codigo == "INCIDENTE_CAMBIO_CONCURRENTE"
        finally:
            await s1.close()
            await s2.close()
        async with engine.connect() as dueno:
            n = (await dueno.execute(
                text("SELECT count(*) FROM incidentes_eventos_estado WHERE incidente_id = :i"), {"i": incidente.id}
            )).scalar_one()
        assert n == 1
    finally:
        async with engine.connect() as dueno:
            for t in (datos["a"], datos["b"]):
                for sentencia in (
                    "DELETE FROM incidentes_eventos_estado WHERE tenant_id = :t",
                    "DELETE FROM incidentes WHERE tenant_id = :t",
                    "DELETE FROM audit_events WHERE tenant_id = :t",
                    "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
                    "DELETE FROM tenants WHERE id = :t",
                ):
                    await dueno.execute(text(sentencia), {"t": t})
            await dueno.execute(text("DELETE FROM users WHERE id LIKE :p"), {"p": f"inc03-%-{sufijo}"})
            await dueno.commit()
        await engine.dispose()


# m4 ---------------------------------------------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.parametrize("sentencia", [
    "UPDATE incidentes_eventos_estado SET motivo = 'Motivo cambiado a la fuerza'",
    "DELETE FROM incidentes_eventos_estado",
])
async def test_m4_la_aplicacion_no_puede_actualizar_ni_borrar_eventos(mundo, sentencia):
    """Mutación: GRANT UPDATE (o DELETE) a lopdp_app → rojo."""
    uid, t, _ = _actor(mundo, "coordinador")
    incidente = await _registrar(mundo)
    await inc.cerrar_incidente(mundo["s"], t, uid, incidente.id, MOTIVO)
    with pytest.raises(DBAPIError, match="permission denied"):
        async with mundo["s"].begin_nested():
            await mundo["s"].execute(text(sentencia))


# m5 ---------------------------------------------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.parametrize("accion", ["cerrar", "reabrir"])
async def test_m5_el_dpo_no_cambia_el_estado(mundo, accion):
    """Mutación: sumar `dpo` a los roles que cambian el estado → rojo."""
    incidente = await _registrar(mundo)
    assert (await _post(mundo, "dpo", incidente.id, accion)).status_code == 403
    assert (await inc.estado_de(mundo["s"], mundo["a"], incidente.id)).estado == "abierto"


@pytest.mark.asyncio
@pytest.mark.parametrize("rol", ROLES_QUE_CAMBIAN)
async def test_cambian_el_estado_los_roles_de_la_organizacion(mundo, rol):
    incidente = await _registrar(mundo)
    r = await _post(mundo, rol, incidente.id, "cerrar")
    assert r.status_code == 200 and r.json()["estado"] == "cerrado", r.text


# m6 ---------------------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_m6_cerrar_no_cambia_la_huella_ni_rompe_la_cadena(mundo):
    """Mutación: meter el estado en Incidente.contenido() → rojo."""
    uid, t, _ = _actor(mundo, "coordinador")
    await _registrar(mundo)
    incidente = await _registrar(mundo, titulo="Segundo incidente simulado")
    antes = await inc.listar_incidentes(mundo["s"], t, uid)
    await inc.cerrar_incidente(mundo["s"], t, uid, incidente.id, MOTIVO)
    despues = await inc.listar_incidentes(mundo["s"], t, uid)
    assert [i.huella for i in antes] == [i.huella for i in despues]
    assert inc.primer_incidente_alterado(despues) is None


# m7 ---------------------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_m7_un_evento_con_el_incidente_de_otra_organizacion_se_rechaza(mundo):
    """Mutación: dejar la FK solo a incidentes(id) → rojo (el evento de B sobre el incidente de A pasaría)."""
    s = mundo["s"]
    ajeno = await _registrar(mundo, tenant="a")
    uid_b, tenant_b, _ = _actor(mundo, "coord_b")
    await fijar_contexto_rls(s, tenant_b, uid_b)
    insertar = text(
        "INSERT INTO incidentes_eventos_estado (id, tenant_id, incidente_id, secuencia, tipo, motivo, registrado_por) "
        "VALUES (:id, :t, :i, 1, 'cierre', :m, :u)"
    )
    with pytest.raises(DBAPIError, match="fk_incidentes_eventos_incidente_tenant"):
        async with s.begin_nested():
            await s.execute(insertar, {"id": str(uuid.uuid4()), "t": tenant_b, "i": ajeno.id, "m": MOTIVO, "u": uid_b})
    # Y con la organización de B en el evento pero el contexto de A, RLS también lo rechaza.
    uid_a, tenant_a, _ = _actor(mundo, "coordinador")
    await fijar_contexto_rls(s, tenant_a, uid_a)
    with pytest.raises(DBAPIError, match="row-level security"):
        async with s.begin_nested():
            await s.execute(insertar, {"id": str(uuid.uuid4()), "t": tenant_b, "i": ajeno.id, "m": MOTIVO, "u": uid_a})


# m8 ---------------------------------------------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.parametrize("motivo", ["", "   ", "corto", "  nueve car "])
async def test_m8_motivo_vacio_o_de_menos_de_10_caracteres_es_422(mundo, motivo):
    """Mutación: quitar el CHECK de la base y el min_length del cuerpo → rojo."""
    incidente = await _registrar(mundo)
    r = await _post(mundo, "coordinador", incidente.id, "cerrar", cuerpo={"motivo": motivo})
    assert r.status_code == 422, r.text
    assert (await inc.estado_de(mundo["s"], mundo["a"], incidente.id)).estado == "abierto"


@pytest.mark.asyncio
async def test_m8_la_base_rechaza_un_motivo_corto_aunque_la_api_no_lo_pare(mundo):
    """Mutación: quitar ck_incidentes_eventos_motivo → rojo."""
    s = mundo["s"]
    uid, t, _ = _actor(mundo, "coordinador")
    incidente = await _registrar(mundo)
    with pytest.raises(DBAPIError, match="ck_incidentes_eventos_motivo"):
        async with s.begin_nested():
            await s.execute(
                text(
                    "INSERT INTO incidentes_eventos_estado (id, tenant_id, incidente_id, secuencia, tipo, motivo, "
                    "registrado_por) VALUES (:id, :t, :i, 1, 'cierre', '          corto   ', :u)"
                ),
                {"id": str(uuid.uuid4()), "t": t, "i": incidente.id, "u": uid},
            )


# m9 ---------------------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_m9_cierre_con_datos_personales_queda_con_la_decision_pendiente(mundo):
    """Mutación: no escribir la marca → rojo."""
    uid, t, _ = _actor(mundo, "coordinador")
    con = await _registrar(mundo, afecta_datos_personales=True)
    sin = await _registrar(mundo, afecta_datos_personales=False, titulo="Sin datos personales simulado")
    cerrado_con = await inc.cerrar_incidente(mundo["s"], t, uid, con.id, MOTIVO)
    cerrado_sin = await inc.cerrar_incidente(mundo["s"], t, uid, sin.id, MOTIVO)
    assert cerrado_con.decision_notificacion == "pendiente"
    assert cerrado_sin.decision_notificacion is None
    r = await _post(mundo, "coordinador", con.id, "reabrir")
    assert r.status_code == 200 and r.json()["decision_notificacion"] is None  # abierto: no hay marca que mostrar
    r = await _post(mundo, "coordinador", con.id, "cerrar")
    assert r.json()["estado"] == "cerrado" and r.json()["decision_notificacion"] == "pendiente"


# Lista -----------------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_la_lista_trae_el_estado_de_cada_incidente(mundo):
    uid, t, rol = _actor(mundo, "coordinador")
    uno, dos = await _registrar(mundo), await _registrar(mundo, titulo="Segundo incidente simulado")
    await inc.cerrar_incidente(mundo["s"], t, uid, uno.id, MOTIVO)

    async def sesion():
        yield mundo["s"]

    app.dependency_overrides[get_session] = sesion
    app.dependency_overrides[get_usuario_autenticado] = lambda: uid
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://prueba") as api:
            r = await api.get(RUTA, headers={"X-Tenant-ID": t, "X-Role": rol})
    finally:
        app.dependency_overrides.pop(get_session, None)
        app.dependency_overrides.pop(get_usuario_autenticado, None)
    assert r.status_code == 200, r.text
    estados = {i["id"]: i["estado"] for i in r.json()["incidentes"]}
    assert estados == {uno.id: "cerrado", dos.id: "abierto"}
    assert r.json()["cadena_integra"] is True
