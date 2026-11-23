# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤videovigilancia-cctv ¤boveda-cloud ¤rat ¤seguridad-tenant ¤arbitro
"""CCTV-01: perfil técnico LOPDP de las cámaras (H.265, eventos, sin audio, máscara) y retención de 15 días.

Las pruebas de la API usan una sesión falsa y AUTH_MODE=headers simulado; las de base de datos corren contra la
PostgreSQL 16 de pruebas (fixture `db_engine`, que llama a `exigir_base_de_pruebas()`) y se omiten sin ella.
Cada prueba lleva en su docstring la mutación que la pone en rojo.
"""
import os
import uuid
from datetime import datetime, timezone

import httpx
import pytest
from fastapi import FastAPI

if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or "postgresql+psycopg://u:c@localhost/pruebas"

from app_core.bucle_eventos import configurar_bucle_eventos  # noqa: E402

configurar_bucle_eventos()  # psycopg async no admite el ProactorEventLoop de Windows
from api.errores import ErrorNegocio, error_negocio_handler  # noqa: E402
from app_core.db.session import get_session  # noqa: E402
from features.videovigilancia import videovigilancia_service as svc  # noqa: E402
from features.videovigilancia.routes import videovigilancia_routes as rutas  # noqa: E402

RUTA = "/api/v1/videovigilancia/camaras"
CABECERAS = {"X-User-ID": "cctv01-u", "X-Tenant-ID": "cctv01-t", "X-Role": "implementador"}

app = FastAPI()
app.add_exception_handler(ErrorNegocio, error_negocio_handler)
app.include_router(svc.router, prefix="/api/v1")


class SesionFalsa:
    def __init__(self):
        self.agregados = []
        self.commits = 0

    def add(self, obj):
        self.agregados.append(obj)

    async def flush(self):
        for o in self.agregados:
            o.id = o.id or uuid.uuid4()

    async def refresh(self, obj):
        obj.creado_en = datetime.now(timezone.utc)

    async def commit(self):
        self.commits += 1


@pytest.fixture
def api(monkeypatch):
    sesion = SesionFalsa()
    app.dependency_overrides[get_session] = lambda: sesion
    monkeypatch.setattr(rutas, "modo_autenticacion", lambda: rutas.MODO_HEADERS)

    async def roles(_s, _t, _u):
        return {"implementador", "dpo"}

    async def evento(*_a, **_k):
        return "evento"

    monkeypatch.setattr(rutas, "roles_activos", roles)
    monkeypatch.setattr(svc, "registrar_evento", evento)
    yield sesion
    app.dependency_overrides.pop(get_session, None)


def _cliente():
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t")


def _cuerpo(**cambios):
    base = {"nombre_ubicacion": "Sede Quito - bodega", "codec": "H265_PLUS", "modo_grabacion": "EVENTO_MOVIMIENTO",
            "audio_ambiental_activo": False, "mascara_privacidad_activa": True}
    return {**base, **cambios}


@pytest.mark.asyncio
async def test_rechazo_camara_con_audio_ambiental(api):
    """Mutación: omitir la comprobación de audio_ambiental_activo o devolver otro código → rojo."""
    async with _cliente() as c:
        r = await c.post(RUTA, json=_cuerpo(audio_ambiental_activo=True), headers=CABECERAS)
    assert r.status_code == 422 and r.json()["code"] == "CCTV_AUDIO_AMBIENTAL_PROHIBIDO"
    assert api.agregados == [] and api.commits == 0


@pytest.mark.asyncio
async def test_alta_camara_conforme_retencion_15_dias(api):
    """Mutación: cambiar el plazo por defecto, el bucket de destino o no persistir la cámara → rojo."""
    async with _cliente() as c:
        r = await c.post(RUTA, json=_cuerpo(), headers=CABECERAS)
    assert r.status_code == 201
    salida = r.json()
    assert salida["plazo_retencion_dias"] == 15 and salida["bucket_destino"] == "short-ttl"
    assert salida["estado_conformidad"] == "CONFORME" and salida["codec"] == "H265_PLUS"
    assert len(api.agregados) == 1 and api.agregados[0].tenant_id == "cctv01-t" and api.commits == 1
    assert api.agregados[0].creado_por == "cctv01-u"


@pytest.mark.asyncio
@pytest.mark.parametrize("cambios,codigo", [
    ({"codec": "H264"}, "CCTV_CODEC_NO_OPTIMIZADO"),
    ({"codec": "MJPEG"}, "CCTV_CODEC_NO_OPTIMIZADO"),
    ({"modo_grabacion": "CONTINUA"}, "CCTV_CONFIGURACION_NO_CONFORME"),
    ({"mascara_privacidad_activa": False}, "CCTV_CONFIGURACION_NO_CONFORME"),
])
async def test_rechazo_perfil_no_conforme(api, cambios, codigo):
    """Mutación: aceptar H.264, grabación continua o cámara sin máscara de privacidad → rojo."""
    async with _cliente() as c:
        r = await c.post(RUTA, json=_cuerpo(**cambios), headers=CABECERAS)
    assert r.status_code == 422 and r.json()["code"] == codigo
    assert api.agregados == []


@pytest.mark.asyncio
async def test_plazo_fuera_de_rango_y_campos_ajenos_se_rechazan(api):
    """Mutación: quitar los límites 1 a 30 del esquema o permitir campos extra (creado_por, tenant_id) → rojo."""
    async with _cliente() as c:
        assert (await c.post(RUTA, json=_cuerpo(plazo_retencion_dias=31), headers=CABECERAS)).status_code == 422
        assert (await c.post(RUTA, json=_cuerpo(plazo_retencion_dias=0), headers=CABECERAS)).status_code == 422
        assert (await c.post(RUTA, json=_cuerpo(tenant_id="otro"), headers=CABECERAS)).status_code == 422
    assert api.agregados == []


@pytest.mark.asyncio
async def test_vinculo_con_rat_por_el_pasillo(api, monkeypatch):
    """Mutación: aceptar una actividad inexistente o no llamar al pasillo del RAT → rojo."""
    from app_core.pasillo import rat as pasillo_rat

    existentes = {"rat-1"}

    async def existe(_s, tenant, rat_id):
        assert tenant == "cctv01-t"
        return rat_id in existentes

    monkeypatch.setattr(pasillo_rat, "existe_actividad", existe)
    async with _cliente() as c:
        ok = await c.post(RUTA, json=_cuerpo(actividad_rat_id="rat-1"), headers=CABECERAS)
        mal = await c.post(RUTA, json=_cuerpo(actividad_rat_id="rat-x"), headers=CABECERAS)
    assert ok.status_code == 201 and ok.json()["actividad_rat_id"] == "rat-1"
    assert mal.status_code == 404 and mal.json()["code"] == "CCTV_ACTIVIDAD_RAT_NO_ENCONTRADA"
    assert len(api.agregados) == 1


@pytest.mark.asyncio
async def test_roles_dpo_lee_y_no_da_de_alta(api):
    """Mutación: permitir el alta al DPO o a un rol sin permiso → rojo."""
    async with _cliente() as c:
        alta = await c.post(RUTA, json=_cuerpo(), headers={**CABECERAS, "X-Role": "dpo"})
        ajeno = await c.get(RUTA, headers={**CABECERAS, "X-Role": "visor"})
    assert alta.status_code == 403 and ajeno.status_code == 403
    assert api.agregados == []


def test_compuerta_y_pasillos():
    """Mutación: importar otra sala o la capa api desde videovigilancia, o quitar el pasillo → rojo."""
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for base, _, archivos in os.walk(os.path.join(raiz, "features", "videovigilancia")):
        for nombre in archivos:
            if nombre.endswith(".py"):
                with open(os.path.join(base, nombre), encoding="utf-8") as f:
                    texto = f.read()
                for ajeno in ("features.rat", "features.boveda_cloud", "from api", "import api"):
                    assert ajeno not in texto, (nombre, ajeno)
    from app_core.pasillo import rat as pasillo_rat
    from app_core.pasillo import videovigilancia as pasillo

    assert callable(pasillo.listar_camaras) and callable(pasillo_rat.existe_actividad)


# Base de datos ----------------------------------------------------------------------------------
async def _con_lopdp_app(engine, cuerpo):
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession

    sufijo = uuid.uuid4().hex[:10]
    a, b = f"cctv01-a-{sufijo}", f"cctv01-b-{sufijo}"
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            for t in (a, b):
                await conexion.execute(
                    text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                         "VALUES (:t, :t, :t, :t)"), {"t": t},
                )
            await conexion.execute(  # audit_events.user_id es FK a users
                text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"), {"u": f"cctv01-u-{sufijo}", "e": f"{sufijo}@test.local"},
            )
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False,
                                    join_transaction_mode="create_savepoint") as s:
                await cuerpo(s, a, b)
        finally:
            await transaccion.rollback()


@pytest.mark.asyncio
async def test_bd_perfil_rls_y_aislamiento(db_engine):
    """Mutación: política RLS con USING (true), quitar un CHECK del perfil, conceder UPDATE o DELETE → rojo."""
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    from app_core.db.session import fijar_contexto_rls
    from features.videovigilancia.schemas import SolicitudCamara

    insertar = ("INSERT INTO cctv_camaras_inventario (tenant_id, nombre_ubicacion, codec, modo_grabacion, "
                "audio_ambiental_activo, mascara_privacidad_activa, plazo_retencion_dias, creado_por) "
                "VALUES (:t, 'x', :c, :m, :a, :k, :p, 'u')")
    ok = {"c": "H265", "m": "EVENTO_MOVIMIENTO", "a": False, "k": True, "p": 15}

    async def cuerpo(s, a, b):
        usuario = f"cctv01-u-{a.rsplit('-', 1)[1]}"
        await fijar_contexto_rls(s, a, None)
        salida = await svc.registrar_camara(s, a, usuario, SolicitudCamara(**_cuerpo()))
        assert salida.plazo_retencion_dias == 15 and salida.bucket_destino == "short-ttl"
        for malo in ({"c": "H264"}, {"m": "CONTINUA"}, {"a": True}, {"k": False}, {"p": 31}, {"p": 0}):
            with pytest.raises(DBAPIError):
                async with s.begin_nested():
                    await s.execute(text(insertar), {"t": a, **ok, **malo})
        with pytest.raises(DBAPIError):  # RLS: no se inserta a nombre de otra organización
            async with s.begin_nested():
                await s.execute(text(insertar), {"t": b, **ok})
        with pytest.raises(DBAPIError):
            async with s.begin_nested():
                await s.execute(text("DELETE FROM cctv_camaras_inventario"))
        with pytest.raises(DBAPIError):
            async with s.begin_nested():
                await s.execute(text("UPDATE cctv_camaras_inventario SET plazo_retencion_dias = 30"))
        assert len(await svc.listar_camaras(s, a)) == 1
        await fijar_contexto_rls(s, b, None)
        assert await svc.listar_camaras(s, b) == []
        assert (await s.execute(text("SELECT count(*) FROM cctv_camaras_inventario"))).scalar() == 0

    await _con_lopdp_app(db_engine, cuerpo)
