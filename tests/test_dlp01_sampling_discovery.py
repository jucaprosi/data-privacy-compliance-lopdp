# ¤dlp-muestreo ¤seguridad-tenant ¤arbitro
"""DLP-01: muestreo acotado, validador Módulo 10 y cero persistencia del dato personal hallado.

Sin red: Cloud DLP se sustituye por un doble que solo devuelve conteos. Datos ficticios (cédulas de la
provincia 30 y 24 calculadas para pasar el Módulo 10, correos .invalid). Las pruebas de la API usan una sesión
falsa; las de base de datos corren contra la PostgreSQL 16 de pruebas (TEST_DATABASE_URL) y se omiten sin
ella. Cada prueba lleva en su docstring la mutación que la pone en rojo.
"""
import logging
import os
import uuid
from datetime import datetime, timezone

import httpx
import pytest
from fastapi import FastAPI

# El motor se crea al importar la sesión; sin base de pruebas basta una URL que nunca se abre.
if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or "postgresql+psycopg://u:c@localhost/pruebas"

from app_core.bucle_eventos import configurar_bucle_eventos  # noqa: E402

configurar_bucle_eventos()  # psycopg async no admite el ProactorEventLoop de Windows
from api.rbac import get_context  # noqa: E402
from app_core.db.session import get_session  # noqa: E402
from features.dlp_discovery import dlp_discovery_service as svc  # noqa: E402
from features.dlp_discovery.routes import dlp_discovery_routes as rutas  # noqa: E402

app = FastAPI()
app.include_router(rutas.router, prefix="/api/v1")

RUTA = "/api/v1/dlp-discovery"
CEDULA = "3000000004"          # centinela: ficticia y válida por Módulo 10
CEDULA_2 = "2400000002"
RUC = "2400000002001"
CORREO = "titular.ficticio@correo.invalid"
CENTINELAS = (CEDULA, CEDULA_2, RUC, CORREO)


class DobleDlp:
    """Doble de Sensitive Data Protection: cuenta correos con una regla trivial; nunca devuelve el hallazgo."""

    def __init__(self, extra=None):
        self.extra = extra or {}
        self.llamadas = []

    def inspeccionar(self, fragmentos, infotypes):
        self.llamadas.append((len(fragmentos), tuple(infotypes)))
        return {"EMAIL": sum(f.count("@") for f in fragmentos), "PHONE": 0, **self.extra}


class SesionFalsa:
    def __init__(self):
        self.agregados = []
        self.commits = 0

    def add(self, obj):
        self.agregados.append(obj)

    async def flush(self):
        return None

    async def refresh(self, obj):
        obj.creado_en = datetime.now(timezone.utc)

    async def commit(self):
        self.commits += 1


def _muestra():
    return [
        f"Socio 1; cédula {CEDULA}; {CORREO}",
        f"Socio 2; cédula {CEDULA_2}; RUC {RUC}",
        "Socio 3; cédula 3000000001; sin correo",   # no pasa el Módulo 10
        "Teléfono 0991234567",                     # tercer dígito 9: no es cédula
    ]


async def _llamar(metodo, ruta, rol="coordinador", cliente=None, sesion=None, **kw):
    sesion = sesion or SesionFalsa()

    async def _sesion():
        yield sesion

    app.dependency_overrides[get_session] = _sesion
    app.dependency_overrides[get_context] = lambda: {"tenant_id": "dlp01-a", "user_id": "dlp01-u", "role": rol}
    app.dependency_overrides[svc.obtener_cliente_dlp] = lambda: cliente or DobleDlp()
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://prueba") as api:
            return await api.request(metodo, f"{RUTA}{ruta}", **kw), sesion
    finally:
        for dep in (get_session, get_context, svc.obtener_cliente_dlp):
            app.dependency_overrides.pop(dep, None)


def _sin_centinelas(texto: str):
    for valor in CENTINELAS:
        assert valor not in texto, "un valor de la muestra salió del motor"


# m1 ---------------------------------------------------------------------------------------------
def test_modulo10_valida_cedula_y_ruc():
    """Mutación: usar coeficiente 1 en las posiciones pares del Módulo 10 → rojo."""
    assert svc.cedula_valida(CEDULA) and svc.cedula_valida(CEDULA_2)
    assert not svc.cedula_valida("3000000001")
    assert not svc.cedula_valida("0991234567")
    assert not svc.cedula_valida("2500000000")   # provincia inexistente
    assert svc.ruc_valido(RUC) and not svc.ruc_valido("2400000002000")


# m2 ---------------------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_escaneo_muestreado_detecta_cedula_sin_persistir_pii(caplog):
    """Mutación: guardar la fila o registrarla en el log (logger.info(filas)) → rojo."""
    caplog.set_level(logging.DEBUG)
    doble = DobleDlp()
    r, sesion = await _llamar(
        "POST", "/escanear-muestra", cliente=doble,
        json={"fuente_nombre": "Base de socios", "limite_muestra": 10, "filas": _muestra()},
    )
    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert cuerpo["infotypes_detectados"] == {"EC_CEDULA_MOD10": 2, "EC_RUC": 1, "EMAIL": 1}
    assert cuerpo["filas_evaluadas"] == 4 and cuerpo["contiene_datos_sensibles"] is False
    assert doble.llamadas == [(4, ("EMAIL", "PHONE", "SALUD"))]
    (guardado,) = sesion.agregados
    columnas = {c.name: getattr(guardado, c.name) for c in guardado.__table__.columns}
    _sin_centinelas(repr(columnas))
    _sin_centinelas(r.text)
    _sin_centinelas(caplog.text)


# m3 ---------------------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_rechazo_muestra_excesiva_dlp():
    """Mutación: quitar la comprobación del tope en validar_limite → rojo."""
    r, sesion = await _llamar(
        "POST", "/escanear-muestra",
        json={"fuente_nombre": "Base", "limite_muestra": 50000, "filas": [f"cédula {CEDULA}"]},
    )
    assert r.status_code == 422 and r.json()["detail"]["codigo"] == "DLP_MUESTRA_EXCEDE_LIMITE"
    assert sesion.agregados == []
    _sin_centinelas(r.text)
    r, _ = await _llamar(
        "POST", "/escanear-muestra",
        json={"fuente_nombre": "Base", "limite_muestra": 2, "filas": ["a", "b", f"cédula {CEDULA}"]},
    )
    assert r.status_code == 422 and r.json()["detail"]["codigo"] == "DLP_MUESTRA_EXCEDE_LIMITE"
    with pytest.raises(svc.MuestraExcedeLimite):
        svc.validar_limite(1001, 1)


# m4 ---------------------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_adaptador_real_falla_cerrado(caplog):
    """Mutación: que ClienteDlpDesactivado devuelva {} en vez de lanzar → rojo."""
    caplog.set_level(logging.DEBUG)
    with pytest.raises(svc.AdaptadorDlpDesactivado):
        svc.obtener_cliente_dlp().inspeccionar([CORREO], ("EMAIL",))
    r, sesion = await _llamar(
        "POST", "/escanear-muestra", cliente=svc.ClienteDlpDesactivado(),
        json={"fuente_nombre": "Base", "limite_muestra": 10, "filas": _muestra()},
    )
    assert r.status_code == 503 and r.json()["detail"]["codigo"] == "DLP_ADAPTADOR_DESACTIVADO"
    assert sesion.agregados == []
    _sin_centinelas(r.text)
    _sin_centinelas(caplog.text)


# m5 ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("extra", [{"CREDIT_CARD_NUMBER": 1}, {"EMAIL": CORREO}, {"PHONE": -1}, {"SALUD": True}])
@pytest.mark.asyncio
async def test_lista_blanca_y_solo_conteos(extra):
    """Mutación: aceptar cualquier clave o valor devuelto por el cliente → rojo."""
    r, sesion = await _llamar(
        "POST", "/escanear-muestra", cliente=DobleDlp(extra),
        json={"fuente_nombre": "Base", "limite_muestra": 10, "filas": _muestra()},
    )
    assert r.status_code == 422 and r.json()["detail"]["codigo"] == "DLP_INFOTYPE_NO_PERMITIDO"
    assert sesion.agregados == []
    _sin_centinelas(r.text)


# m6 ---------------------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_error_de_validacion_no_devuelve_la_muestra():
    """Mutación: declarar el cuerpo como SolicitudEscaneo en la firma (FastAPI devuelve `input`) → rojo."""
    r, _ = await _llamar("POST", "/escanear-muestra", json={"limite_muestra": 10, "filas": [CORREO, 7]})
    assert r.status_code == 422 and r.json()["detail"]["codigo"] == "DLP_SOLICITUD_INVALIDA"
    _sin_centinelas(r.text)


# m7 ---------------------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_cuerpo_excesivo_se_corta_antes_de_leerlo():
    """Mutación: quitar la comprobación de Content-Length y del acumulado en _leer_json_con_tope → rojo."""
    grande = b'{"filas": ["' + b"x" * (rutas.TOPE_CUERPO_BYTES + 1) + b'"]}'
    r, sesion = await _llamar(
        "POST", "/escanear-muestra", content=grande, headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 413 and r.json()["detail"]["codigo"] == "DLP_CUERPO_EXCEDE_TOPE"
    assert sesion.agregados == []


# m8 ---------------------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_roles_dpo_lee_y_no_escanea():
    """Mutación: añadir "dpo" o "auditor" a ROLES_ESCANEO, o "auditor" a ROLES_VINCULO → rojo."""
    cuerpo = {"fuente_nombre": "Base", "limite_muestra": 10, "filas": _muestra()}
    for rol in ("dpo", "auditor", "responsable_area"):
        r, _ = await _llamar("POST", "/escanear-muestra", rol=rol, json=cuerpo)
        assert r.status_code == 403, rol
    for rol in ("implementador", "auditor", "dpo"):
        r, _ = await _llamar(
            "POST", f"/escaneos/{uuid.uuid4()}/vincular-rat", rol=rol,
            json={"actividad_rat_id": "rat-1", "infotypes": ["EMAIL"]},
        )
        assert r.status_code == 403, rol
    assert {"dpo", "auditor"} <= set(svc.ROLES_CONSULTA) and "responsable_area" not in svc.ROLES_CONSULTA
    assert svc.ROLES_VINCULO == ("coordinador",)


# m9 ---------------------------------------------------------------------------------------------
def test_compuerta_y_pasillos():
    """Mutación: importar la sala RAT desde dlp_discovery o una sala ajena desde el pasillo → rojo."""
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for base, _, archivos in os.walk(os.path.join(raiz, "features", "dlp_discovery")):
        for nombre in archivos:
            if nombre.endswith(".py"):
                with open(os.path.join(base, nombre), encoding="utf-8") as f:
                    assert "features.rat" not in f.read(), nombre
    from app_core.pasillo import dlp_discovery as pasillo

    assert pasillo.cedula_valida(CEDULA) and not pasillo.cedula_valida("3000000001")


# Base de datos ----------------------------------------------------------------------------------
_URL = os.environ.get("TEST_DATABASE_URL", "")
_con_bd = pytest.mark.skipif(not _URL, reason="TEST_DATABASE_URL no configurada")


def _url_async() -> str:
    return _URL.replace("postgresql://", "postgresql+psycopg://", 1) if _URL.startswith("postgresql://") else _URL


async def _con_lopdp_app(cuerpo, rol: str | None = "lopdp_app"):
    """Con `rol=None` la sesión queda con el usuario de la conexión (el que migra), sin SET ROLE."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

    engine = create_async_engine(_url_async(), hide_parameters=True)
    sufijo = uuid.uuid4().hex[:10]
    a, b = f"dlp01-a-{sufijo}", f"dlp01-b-{sufijo}"
    try:
        async with engine.connect() as conexion:
            transaccion = await conexion.begin()
            try:
                for t in (a, b):
                    await conexion.execute(
                        text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                             "VALUES (:t, :t, :t, :t)"), {"t": t},
                    )
                if rol:
                    await conexion.execute(text(f"SET LOCAL ROLE {rol}"))
                async with AsyncSession(bind=conexion, expire_on_commit=False,
                                        join_transaction_mode="create_savepoint") as s:
                    await cuerpo(s, conexion, a, b)
            finally:
                await transaccion.rollback()
    finally:
        await engine.dispose()


async def _tenant(s, tenant):
    from app_core.db.session import fijar_contexto_rls

    await fijar_contexto_rls(s, tenant, None)


@_con_bd
@pytest.mark.asyncio
async def test_bd_solo_conteos_y_rls():
    """Mutación: política RLS con USING (true), quitar el CHECK de valores numéricos o conceder DELETE → rojo."""
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    async def cuerpo(s, conexion, a, b):
        await _tenant(s, a)
        salida = await svc.escanear_muestra(s, a, None, "Base de socios", 10, _muestra(), DobleDlp())
        assert salida.infotypes_detectados["EC_CEDULA_MOD10"] == 2
        filas = (await s.execute(text("SELECT row_to_json(e)::text FROM dlp_escaneos_muestreados e"))).scalars().all()
        assert len(filas) == 1
        _sin_centinelas(" ".join(filas))
        # La base rechaza un valor de texto (p. ej. una cédula) en los conteos.
        with pytest.raises(DBAPIError):
            async with s.begin_nested():
                await s.execute(text(
                    "INSERT INTO dlp_escaneos_muestreados (tenant_id, fuente_nombre, infotypes_detectados, "
                    "contiene_datos_sensibles) VALUES (:t, 'x', CAST(:j AS jsonb), false)"),
                    {"t": a, "j": '{"EC_CEDULA_MOD10": "%s"}' % CEDULA},
                )
        with pytest.raises(DBAPIError):
            async with s.begin_nested():
                await s.execute(text("DELETE FROM dlp_escaneos_muestreados"))
        await _tenant(s, b)
        assert await svc.listar_escaneos(s, b) == []
        assert (await s.execute(text("SELECT count(*) FROM dlp_escaneos_muestreados"))).scalar() == 0

    await _con_lopdp_app(cuerpo)


@_con_bd
@pytest.mark.asyncio
async def test_bd_filtro_de_tenant_es_barrera_propia_sin_rls():
    """Mutación: quitar `.where(EscaneoMuestreado.tenant_id == tenant_id)` de listar_escaneos → rojo.

    Con lopdp_app (que no salta RLS) quitar ese filtro no se observa: la política ya oculta las filas
    ajenas (lo cubre test_bd_solo_conteos_y_rls). Aquí la sesión usa un rol que salta RLS (superusuario o
    BYPASSRLS), así que el filtro de la aplicación es la única barrera y su ausencia mezcla organizaciones.
    """
    from sqlalchemy import text

    async def cuerpo(s, conexion, a, b):
        salta = (await s.execute(text(
            "SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = current_user"))).scalar()
        if not salta:
            pytest.skip("el usuario de la base de pruebas no salta RLS: el filtro no se puede aislar")
        await _tenant(s, a)
        await svc.escanear_muestra(s, a, None, "Base A", 10, _muestra(), DobleDlp())
        await _tenant(s, b)
        await svc.escanear_muestra(s, b, None, "Base B", 10, ["sin datos"], DobleDlp())
        assert (await s.execute(text("SELECT count(*) FROM dlp_escaneos_muestreados WHERE tenant_id IN (:a, :b)"),
                                {"a": a, "b": b})).scalar() == 2  # RLS no filtra en esta sesión
        assert [e.fuente_nombre for e in await svc.listar_escaneos(s, b)] == ["Base B"]
        assert [e.fuente_nombre for e in await svc.listar_escaneos(s, a)] == ["Base A"]

    await _con_lopdp_app(cuerpo, rol=None)
