# ¤boveda-cloud ¤seguridad-tenant ¤arbitro
"""BOV-01: catálogo de paquetes, cuotas de espacio y descargas, y aislamiento RLS de la suscripción.

Las pruebas de base de datos corren contra la PostgreSQL 16 local del arnés (TEST_DATABASE_URL) con el rol
`lopdp_app`, y se omiten sin ella. Cada prueba lleva en su docstring la mutación que la pone en rojo.
"""
import ast
import os
import uuid

import httpx
import pytest
from fastapi import FastAPI

if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or "postgresql+psycopg://u:c@localhost/pruebas"

from app_core.bucle_eventos import configurar_bucle_eventos  # noqa: E402

configurar_bucle_eventos()
from api.errores import ErrorNegocio, error_negocio_handler  # noqa: E402
from app_core.db.session import get_session  # noqa: E402
from features.boveda_cloud import boveda_cloud_service as svc  # noqa: E402
from features.boveda_cloud.routes import boveda_paquetes_routes as rutas  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GB = 1024**3  # VERIFICADO: unidad de facturación de Cloud Storage (2^30 bytes)

app = FastAPI()
app.add_exception_handler(ErrorNegocio, error_negocio_handler)
app.include_router(svc.router, prefix="/api/v1")
RUTA = "/api/v1/boveda-cloud/suscripcion"


# Sin base de datos ------------------------------------------------------------------------------
def test_validar_consumo_no_se_expone_por_http():
    """Mutación: añadir la ruta POST /suscripcion/validar-consumo → rojo."""
    rutas = {(r.path, tuple(sorted(r.methods))) for r in svc.router.routes}
    assert rutas == {("/boveda-cloud/suscripcion", ("GET",)), ("/boveda-cloud/suscripcion", ("POST",))}


async def _peticion(metodo, rol, monkeypatch, **kw):
    """Modo de cabeceras con membresía simulada en todos los roles: solo decide el rol pedido."""
    monkeypatch.setattr(rutas, "modo_autenticacion", lambda: rutas.MODO_HEADERS)

    async def _todos(session, tenant_id, usuario):
        return {"admin_organizacion", "dpo", "coordinador", "auditor", "implementador", "responsable_area"}

    async def _sin_operador(session, email, sub):
        return None

    monkeypatch.setattr(rutas, "roles_activos", _todos)
    monkeypatch.setattr(svc, "operador_activo", _sin_operador)
    app.dependency_overrides[get_session] = lambda: None
    cabeceras = {"X-User-ID": "u", "X-Tenant-ID": "t", "X-Role": rol, "X-User-Email": "admin@correo.invalid"}
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://p") as api:
            return await api.request(metodo, RUTA, headers=cabeceras, **kw)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_roles_de_consulta(monkeypatch):
    """Mutación: añadir "auditor" o "implementador" a ROLES_CONSULTA → rojo."""
    assert svc.ROLES_CONSULTA == ("admin_organizacion", "dpo", "coordinador")
    for rol in ("auditor", "implementador", "responsable_area"):
        assert (await _peticion("GET", rol, monkeypatch)).status_code == 403, rol


@pytest.mark.asyncio
async def test_matriz_propia_get_suscripcion(monkeypatch):
    """Matriz propia (el prefijo no está en PREFIJOS_MATRIZ). Mutación: quitar un rol permitido de
    ROLES_CONSULTA, o no exigir token en modo oidc → rojo."""
    async def _falsa(session, tenant_id):
        return svc.SuscripcionSalida(
            paquete_codigo="INICIAL", paquete_nombre="Inicial", cuota_almacenamiento_bytes=GB,
            uso_almacenamiento_bytes=0, cuota_egress_mensual_bytes=GB, uso_egress_mensual_bytes=0,
            certificaciones_heredadas=[], estado="ACTIVA",
        )

    monkeypatch.setattr(svc, "obtener_suscripcion", _falsa)
    for rol in ("admin_organizacion", "dpo", "coordinador"):
        assert (await _peticion("GET", rol, monkeypatch)).status_code == 200, rol
    for rol in ("implementador", "responsable_area", "auditor"):
        assert (await _peticion("GET", rol, monkeypatch)).status_code == 403, rol
    # Modo oidc sin token: 401 antes de mirar el rol.
    monkeypatch.setattr(rutas, "modo_autenticacion", lambda: "oidc")
    app.dependency_overrides[get_session] = lambda: None
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://p") as api:
            r = await api.get(RUTA, headers={"X-Tenant-ID": "t", "X-Role": "dpo"})
        assert r.status_code == 401
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_alta_solo_operador_admin_recibe_403(monkeypatch):
    """Mutación: aceptar en el alta a quien no es operador (p. ej. al admin de la organización) → rojo."""
    cuerpo = {"tenant_id": "t", "paquete_codigo": "INICIAL"}
    for rol in ("admin_organizacion", "dpo", "coordinador"):
        assert (await _peticion("POST", rol, monkeypatch, json=cuerpo)).status_code == 403, rol


def test_limites_uso_no_conectado_al_limitador():
    """Mutación m4: importar limites_uso (o el pasillo de la bóveda) desde api/middleware o app_core/limites → rojo."""
    for carpeta in ("api/middleware", "app_core/limites"):
        base = os.path.join(RAIZ, *carpeta.split("/"))
        for raiz, _, archivos in os.walk(base):
            for nombre in archivos:
                if not nombre.endswith(".py"):
                    continue
                with open(os.path.join(raiz, nombre), encoding="utf-8") as f:
                    arbol = ast.parse(f.read())
                for nodo in ast.walk(arbol):
                    if isinstance(nodo, ast.ImportFrom):
                        modulo = nodo.module or ""
                        assert "boveda_cloud" not in modulo, nombre
                        assert "limites_uso" not in {a.name for a in nodo.names}, nombre
                    elif isinstance(nodo, ast.Import):
                        assert not any("boveda_cloud" in a.name for a in nodo.names), nombre
                    elif isinstance(nodo, ast.Attribute):
                        assert nodo.attr != "limites_uso", nombre


# Base de datos ----------------------------------------------------------------------------------
_URL = os.environ.get("TEST_DATABASE_URL", "")
_con_bd = pytest.mark.skipif(not _URL, reason="TEST_DATABASE_URL no configurada")


def _url_async() -> str:
    return _URL.replace("postgresql://", "postgresql+psycopg://", 1) if _URL.startswith("postgresql://") else _URL


async def _con_lopdp_app(cuerpo, antes=None):
    """Dos organizaciones nuevas y una sesión con lopdp_app dentro de una transacción que se deshace."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

    engine = create_async_engine(_url_async(), hide_parameters=True)
    sufijo = uuid.uuid4().hex[:10]
    a, b = f"bov01-a-{sufijo}", f"bov01-b-{sufijo}"
    try:
        async with engine.connect() as conexion:
            transaccion = await conexion.begin()
            try:
                for t in (a, b):
                    await conexion.execute(
                        text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                             "VALUES (:t, :t, :t, :t)"), {"t": t},
                    )
                if antes:
                    await antes(conexion, sufijo)
                await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
                async with AsyncSession(bind=conexion, expire_on_commit=False,
                                        join_transaction_mode="create_savepoint") as s:
                    await cuerpo(s, a, b)
            finally:
                await transaccion.rollback()
    finally:
        await engine.dispose()


async def _contexto(s, tenant):
    from app_core.db.session import fijar_contexto_rls

    await fijar_contexto_rls(s, tenant, None)


async def _alta(s, tenant, paquete="INICIAL", **cuotas):
    return await svc.crear_suscripcion(s, svc.SolicitudAlta(tenant_id=tenant, paquete_codigo=paquete, **cuotas), "op")


def _codigo(exc_info):
    return exc_info.value.code, exc_info.value.status_code


@_con_bd
@pytest.mark.asyncio
async def test_catalogo_paquetes_prd():
    """Mutación m1: `max_claves_integracion` de INICIAL a 3 (o 51 GB en su cuota) en la siembra → rojo."""
    from sqlalchemy import text

    async def cuerpo(s, a, b):
        filas = (await s.execute(text(
            "SELECT codigo, cuota_almacenamiento_bytes, cuota_egress_mensual_bytes, peticiones_api_minuto, "
            "tokens_ia_mes, max_claves_integracion, max_webhooks FROM boveda_paquetes ORDER BY codigo"))).all()
        assert {f[0]: tuple(f[1:]) for f in filas} == {
            "INICIAL": (50 * GB, 100 * GB, 300, 2_000_000, 2, 2),
            "PROFESIONAL": (250 * GB, 500 * GB, 1200, 10_000_000, 10, 10),
            "CORPORATIVO": (1024 * GB, 2048 * GB, 5000, 50_000_000, 50, 50),
            "ENTERPRISE": (None, None, None, None, None, None),
        }

    await _con_lopdp_app(cuerpo)


@_con_bd
@pytest.mark.asyncio
async def test_bloqueo_preventivo_cuota_egress_excedida():
    """Mutación m6: quitar `AND uso_egress_mensual_bytes + :b <= cuota...` del UPDATE → rojo.

    Además: el rechazo no persiste CUOTA_EXCEDIDA ni suma el consumo rechazado.
    """
    from sqlalchemy import text

    async def cuerpo(s, a, b):
        salida = await _alta(s, a)
        assert (salida.paquete_codigo, salida.estado, salida.cuota_egress_mensual_bytes) == ("INICIAL", "ACTIVA", 100 * GB)
        assert salida.certificaciones_heredadas == ["ISO 27001", "ISO 27701", "SOC 2"]
        await svc.validar_consumo(s, a, "egress", 100 * GB - 1)
        await svc.validar_consumo(s, a, "egress", 1)          # justo en la cuota: se admite
        with pytest.raises(ErrorNegocio) as e:
            await svc.validar_consumo(s, a, "egress", 1)
        assert _codigo(e) == ("BOVEDA_CUOTA_EGRESS_EXCEDIDA", 409)
        fila = (await s.execute(text("SELECT uso_egress_mensual_bytes, estado FROM boveda_suscripciones_tenant"))).one()
        assert tuple(fila) == (100 * GB, "ACTIVA")
        # Mutación: no derivar el estado al leer → la lectura diría ACTIVA con la cuota agotada.
        assert (await svc.obtener_suscripcion(s, a)).estado == "CUOTA_EXCEDIDA"
        ev = (await s.execute(text("SELECT action, payload->>'operador_id' FROM audit_events WHERE entity_type = 'boveda_suscripcion'"))).one()
        assert tuple(ev) == ("alta_por_operador", "op")

    await _con_lopdp_app(cuerpo)


@_con_bd
@pytest.mark.asyncio
async def test_cuota_almacenamiento_y_suspendida():
    """Mutación: quitar `AND estado = 'ACTIVA'` del UPDATE, o la condición de almacenamiento → rojo."""
    from sqlalchemy import text

    async def cuerpo(s, a, b):
        await _alta(s, a)
        await svc.validar_consumo(s, a, "almacenamiento", 50 * GB)
        with pytest.raises(ErrorNegocio) as e:
            await svc.validar_consumo(s, a, "almacenamiento", 1)
        assert _codigo(e) == ("BOVEDA_CUOTA_ALMACENAMIENTO_EXCEDIDA", 409)
        await s.execute(text("UPDATE boveda_suscripciones_tenant SET estado = 'SUSPENDIDA'"))
        with pytest.raises(ErrorNegocio) as e:
            await svc.validar_consumo(s, a, "egress", 1)
        assert _codigo(e) == ("BOVEDA_SUSCRIPCION_SUSPENDIDA", 409)
        assert (await s.execute(text("SELECT uso_egress_mensual_bytes FROM boveda_suscripciones_tenant"))).scalar() == 0

    await _con_lopdp_app(cuerpo)


@_con_bd
@pytest.mark.asyncio
async def test_alta_enterprise_exige_cuotas_y_una_por_organizacion():
    """Mutación: copiar las cuotas NULL del paquete personalizado o quitar `ON CONFLICT ... DO NOTHING` → rojo."""
    async def cuerpo(s, a, b):
        with pytest.raises(ErrorNegocio) as e:
            await _alta(s, a, "ENTERPRISE")
        assert _codigo(e) == ("BOVEDA_CUOTA_PERSONALIZADA_REQUERIDA", 422)
        salida = await _alta(s, a, "ENTERPRISE", cuota_almacenamiento_bytes=5 * 1024 * GB, cuota_egress_mensual_bytes=GB)
        assert salida.cuota_egress_mensual_bytes == GB
        with pytest.raises(ErrorNegocio) as e:
            await _alta(s, a, "INICIAL")
        assert _codigo(e) == ("BOVEDA_SUSCRIPCION_YA_EXISTE", 409)
        with pytest.raises(ErrorNegocio) as e:
            await _alta(s, b, "NO_EXISTE")
        assert _codigo(e) == ("BOVEDA_PAQUETE_NO_ENCONTRADO", 422)

    await _con_lopdp_app(cuerpo)


@_con_bd
@pytest.mark.asyncio
async def test_boveda_suscripcion_aislamiento_rls():
    """Mutación m5: política con USING (true), o quitar ENABLE/FORCE ROW LEVEL SECURITY → rojo.

    B no ve la suscripción de A ni por la API ni por SQL, y no puede consumir la cuota de A.
    """
    from sqlalchemy import text

    async def cuerpo(s, a, b):
        await _alta(s, a, "PROFESIONAL")
        await _alta(s, b, "INICIAL")
        await _contexto(s, a)
        await svc.validar_consumo(s, a, "egress", GB)

        async def _sesion():
            yield s

        app.dependency_overrides[get_session] = _sesion
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://p") as api:
                await _contexto(s, b)
                app.dependency_overrides[rutas.contexto_consulta] = lambda: {"tenant_id": b, "user_id": "u", "role": "dpo"}
                r = await api.get(RUTA)
                assert r.status_code == 200 and r.json()["paquete_codigo"] == "INICIAL"
                assert r.json()["uso_egress_mensual_bytes"] == 0
                # Con el contexto de B, pedir la de A no devuelve nada.
                app.dependency_overrides[rutas.contexto_consulta] = lambda: {"tenant_id": a, "user_id": "u", "role": "dpo"}
                r = await api.get(RUTA)
                assert r.status_code == 404 and r.json()["code"] == "BOVEDA_SUSCRIPCION_NO_ENCONTRADA"
        finally:
            app.dependency_overrides.clear()
        assert (await s.execute(text("SELECT count(*) FROM boveda_suscripciones_tenant"))).scalar() == 1
        with pytest.raises(ErrorNegocio) as e:
            await svc.validar_consumo(s, a, "egress", 1)
        assert _codigo(e) == ("BOVEDA_SUSCRIPCION_NO_ENCONTRADA", 404)
        await _contexto(s, a)
        assert (await s.execute(text("SELECT uso_egress_mensual_bytes FROM boveda_suscripciones_tenant"))).scalar() == GB
        # Tampoco puede insertar una suscripción a nombre de otra organización.
        await _contexto(s, b)
        from sqlalchemy.exc import DBAPIError

        with pytest.raises(DBAPIError):
            async with s.begin_nested():
                await s.execute(text(
                    "INSERT INTO boveda_suscripciones_tenant (tenant_id, paquete_codigo, cuota_almacenamiento_bytes, "
                    "cuota_egress_mensual_bytes) VALUES (:t, 'INICIAL', 1, 1)"), {"t": f"{a}-x"})

    await _con_lopdp_app(cuerpo)


@_con_bd
@pytest.mark.asyncio
async def test_techos_integracion_por_paquete():
    """Mutación m2: que techos_integracion lea siempre el paquete INICIAL → rojo."""
    async def cuerpo(s, a, b):
        await _alta(s, a, "PROFESIONAL")
        await _alta(s, b, "ENTERPRISE", cuota_almacenamiento_bytes=GB, cuota_egress_mensual_bytes=GB)
        from app_core.pasillo import boveda_cloud as pasillo

        await _contexto(s, a)
        assert await pasillo.techos_integracion(s, a) == {"claves": 10, "webhooks": 10}
        await _contexto(s, b)
        assert await pasillo.techos_integracion(s, b) == {"claves": None, "webhooks": None}
        await _contexto(s, "bov01-sin-suscripcion")
        with pytest.raises(ErrorNegocio) as e:
            await pasillo.techos_integracion(s, "bov01-sin-suscripcion")
        assert _codigo(e) == ("BOVEDA_SUSCRIPCION_NO_ENCONTRADA", 404)

    await _con_lopdp_app(cuerpo)


@_con_bd
@pytest.mark.asyncio
async def test_limites_uso_solo_dato():
    """Mutación: devolver los techos de integración en lugar de peticiones y tokens → rojo (m4 en la prueba AST)."""
    async def cuerpo(s, a, b):
        await _alta(s, a, "INICIAL")
        from app_core.pasillo import boveda_cloud as pasillo

        await _contexto(s, a)
        assert await pasillo.limites_uso(s, a) == {"peticiones_api_minuto": 300, "tokens_ia_mes": 2_000_000}

    await _con_lopdp_app(cuerpo)


@_con_bd
@pytest.mark.asyncio
async def test_lopdp_app_no_edita_paquetes():
    """Mutación m3: `GRANT UPDATE` (o INSERT, o DELETE en suscripciones) a lopdp_app → rojo."""
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    async def cuerpo(s, a, b):
        await _alta(s, a)
        await _contexto(s, a)
        for sql in (
            "UPDATE boveda_paquetes SET max_webhooks = 99 WHERE codigo = 'INICIAL'",
            "INSERT INTO boveda_paquetes (codigo, nombre) VALUES ('PIRATA', 'x')",
            "DELETE FROM boveda_suscripciones_tenant",
            "UPDATE boveda_suscripciones_tenant SET cuota_egress_mensual_bytes = 1",
        ):
            with pytest.raises(DBAPIError, match="permission denied|permiso denegado"):
                async with s.begin_nested():
                    await s.execute(text(sql))

    await _con_lopdp_app(cuerpo)


@_con_bd
@pytest.mark.asyncio
async def test_alta_operador_real_frente_a_no_operador(monkeypatch):
    """Mutación: que requiere_operador acepte a cualquiera con identidad (p. ej. el admin de la organización),
    o que operador_activo ignore el 403 del pasillo de Plataforma → rojo.

    El operador activo da de alta (201); el inactivo y el que no es operador reciben 403 y no se crea nada.
    """
    from sqlalchemy import text

    correos = {}

    async def antes(conexion, sufijo):
        for clave, activo in (("activo", True), ("inactivo", False)):
            correos[clave] = f"op-{clave}-{sufijo}@correo.invalid"
            await conexion.execute(text(
                "INSERT INTO operadores_plataforma (id, email, nombre, activo) VALUES (:i, :e, 'Operador', :a)"),
                {"i": f"op-{clave}-{sufijo}", "e": correos[clave], "a": activo})

    async def cuerpo(s, a, b):
        async def _sesion():
            yield s

        monkeypatch.setattr(rutas, "modo_autenticacion", lambda: rutas.MODO_HEADERS)
        app.dependency_overrides[get_session] = _sesion
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://p") as api:
                for correo in (correos["inactivo"], "admin.org@correo.invalid"):
                    r = await api.post(RUTA, headers={"X-User-Email": correo},
                                       json={"tenant_id": a, "paquete_codigo": "INICIAL"})
                    assert r.status_code == 403, correo
                r = await api.post(RUTA, headers={"X-User-Email": correos["activo"]},
                                   json={"tenant_id": a, "paquete_codigo": "INICIAL"})
                assert r.status_code == 201, r.text
                assert r.json()["paquete_codigo"] == "INICIAL"
        finally:
            app.dependency_overrides.clear()
        await _contexto(s, a)
        creado_por = (await s.execute(text("SELECT creado_por FROM boveda_suscripciones_tenant"))).scalar()
        assert creado_por == correos["activo"].split("@")[0]  # el id del operador activo es «op-activo-<sufijo>»

    await _con_lopdp_app(cuerpo, antes)
