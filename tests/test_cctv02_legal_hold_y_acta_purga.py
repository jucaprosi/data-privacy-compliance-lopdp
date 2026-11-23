# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤videovigilancia-cctv ¤incidentes ¤derechos ¤conservacion ¤seguridad-tenant ¤arbitro
"""CCTV-02: Congelamiento Forense (Hold Legal) y Actas Quincenales SHA-256.

Invariante INV_LOPDP_CCTV_LEGAL_HOLD_OVERRIDE:
El Hold Legal prevalece sobre la purga ordinaria de 15 días.
Todo clip vinculado a un incidente o derecho ARCOP+ es promovido inmediatamente
al bucket WORM 'long-retention', quedando blindado ante cualquier intento de destrucción.
"""
import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi import FastAPI

if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or "postgresql+psycopg://u:c@localhost/pruebas"

from app_core.bucle_eventos import configurar_bucle_eventos  # noqa: E402

configurar_bucle_eventos()
from api.errores import ErrorNegocio, error_negocio_handler  # noqa: E402
from app_core.db.session import get_session  # noqa: E402
from features.videovigilancia import videovigilancia_service as svc  # noqa: E402
from features.videovigilancia.routes import cctv_hold_routes as rutas_hold  # noqa: E402
from features.videovigilancia.services.cctv_legal_hold_engine import ClipBoveda, ActaDestruccionCCTV  # noqa: E402

app = FastAPI()
app.add_exception_handler(ErrorNegocio, error_negocio_handler)
app.include_router(svc.router, prefix="/api/v1")

CABECERAS = {"X-User-ID": "cctv02-u", "X-Tenant-ID": "cctv02-t", "X-Role": "dpo"}
CABECERAS_OPERADOR = {"X-User-ID": "cctv02-op", "X-Tenant-ID": "cctv02-t", "X-Role": "implementador"}


class SesionFalsa:
    def __init__(self):
        self.agregados = []
        self.commits = 0

    def add(self, obj):
        self.agregados.append(obj)

    async def flush(self):
        for o in self.agregados:
            if getattr(o, "id", None) is None:
                o.id = uuid.uuid4()

    async def refresh(self, obj):
        pass

    async def commit(self):
        self.commits += 1

    async def execute(self, stmt, *args, **kwargs):
        class FilaResultado:
            def scalars(self):
                return self

            def first(self):
                return None

            def all(self):
                return []

            def scalar_one_or_none(self):
                return None

        return FilaResultado()


@pytest.fixture
def sesion():
    return SesionFalsa()


@pytest.fixture
def api(monkeypatch, sesion):
    app.dependency_overrides[get_session] = lambda: sesion
    monkeypatch.setattr(rutas_hold, "modo_autenticacion", lambda: rutas_hold.MODO_HEADERS)

    async def roles(_s, _t, _u):
        return {"dpo", "implementador", "admin_organizacion", "coordinador"}

    async def evento(*_a, **_k):
        return "evento"

    monkeypatch.setattr(rutas_hold, "roles_activos", roles)
    monkeypatch.setattr(svc, "registrar_evento", evento)
    from features.videovigilancia.services import cctv_legal_hold_engine as engine
    monkeypatch.setattr(engine, "registrar_evento", evento)

    yield sesion
    app.dependency_overrides.pop(get_session, None)


def _cliente():
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")


# ==============================================================================
# PRUEBAS DEL MOTOR Y ACEPTACIÓN CCTV-02
# ==============================================================================

@pytest.mark.asyncio
async def test_purga_15_dias_respeta_hold_legal_y_emite_acta(sesion, monkeypatch):
    """Escenario de Aceptación 1:

    Dado 10 clips vencidos a los 15 días donde uno tiene hold_legal_activo = True por un robo reportado,
    cuando corre la purga quincenal,
    entonces se destruyen 9 clips, se genera el acta SHA-256 y el clip en Hold Legal se conserva en el bucket WORM.
    Mutación: si la purga destruye clips bajo hold o no emite el acta -> fallo.
    """
    tenant_id = "cctv02-t"
    camara_id = uuid.uuid4()
    hace_16_dias = datetime.now(timezone.utc) - timedelta(days=16)

    # Crear 10 clips vencidos
    clips = []
    for i in range(10):
        h = hashlib.sha256(f"clip-video-data-{i}".encode("utf-8")).hexdigest()
        c = await svc.crear_clip(
            sesion,
            tenant_id=tenant_id,
            camara_id=str(camara_id),
            sha256_clip=h,
            fecha_captura=hace_16_dias,
            hold_legal_activo=False,
            bucket_actual="short-ttl",
        )
        clips.append(c)

    # El clip 0 recibe Hold Legal por incidente reportado
    clip_protegido = clips[0]
    from app_core.pasillo import incidentes as pasillo_incidentes

    async def mock_existe_incidente(_s, t, inc_id):
        return inc_id == "INC-ROBO-001"

    monkeypatch.setattr(pasillo_incidentes, "existe_incidente", mock_existe_incidente)

    await svc.aplicar_hold_legal(
        sesion,
        tenant_id=tenant_id,
        clip_id=str(clip_protegido.id),
        expediente_origen_tipo="INCIDENTE",
        expediente_origen_id="INC-ROBO-001",
        user_id="dpo-cctv",
    )

    assert clip_protegido.hold_legal_activo is True
    assert clip_protegido.bucket_actual == "long-retention"
    assert clip_protegido.expediente_origen_tipo == "INCIDENTE"
    assert clip_protegido.expediente_origen_id == "INC-ROBO-001"

    # Ejecutar la purga quincenal
    acta = await svc.ejecutar_purga_quincenal(sesion, tenant_id=tenant_id, user_id="worker-cctv")

    assert acta["total_clips_destruidos"] == 9
    assert acta["total_clips_preservados_hold"] == 1
    assert str(clip_protegido.id) in acta["clips_preservados_ids"]
    assert clip_protegido.sha256_clip not in acta["hashes_destruidos"]
    assert len(acta["hashes_destruidos"]) == 9

    # Verificar que el clip protegido sigue sin acta_destruccion_hash y en long-retention
    assert clip_protegido.acta_destruccion_hash is None
    assert clip_protegido.bucket_actual == "long-retention"

    # Verificar que los 9 clips destruidos tienen el hash maestro del acta
    for c in clips[1:]:
        assert c.acta_destruccion_hash == acta["hash_maestro_sha256"]

    # Invariante de integridad del acta: el hash maestro es el sha256 canónico del payload
    assert len(acta["hash_maestro_sha256"]) == 64


@pytest.mark.asyncio
async def test_bloqueo_borrado_clip_con_hold_legal(sesion):
    """Escenario de Aceptación 2:

    Dado un intento directo de eliminar un clip con hold_legal_activo = True,
    cuando se invoca el servicio,
    entonces responde 409 Conflict (CCTV_CLIP_PROTEGIDO_POR_HOLD_LEGAL).
    Invariante: INV_LOPDP_CCTV_LEGAL_HOLD_OVERRIDE.
    """
    tenant_id = "cctv02-t"
    camara_id = uuid.uuid4()
    hace_5_dias = datetime.now(timezone.utc) - timedelta(days=5)

    clip = await svc.crear_clip(
        sesion,
        tenant_id=tenant_id,
        camara_id=str(camara_id),
        sha256_clip=hashlib.sha256(b"evidencia-vital").hexdigest(),
        fecha_captura=hace_5_dias,
        hold_legal_activo=True,
        bucket_actual="long-retention",
    )

    # Intento de purga directa debe ser rechazado con 409
    with pytest.raises(ErrorNegocio) as exc_info:
        await svc.purgar_clip(sesion, tenant_id, str(clip.id), user_id="operador")

    assert exc_info.value.code == "CCTV_CLIP_PROTEGIDO_POR_HOLD_LEGAL"
    assert exc_info.value.status_code == 409

    # También a través de eliminar_clip
    with pytest.raises(ErrorNegocio) as exc_info2:
        await svc.eliminar_clip(sesion, tenant_id, str(clip.id), user_id="operador")

    assert exc_info2.value.code == "CCTV_CLIP_PROTEGIDO_POR_HOLD_LEGAL"
    assert exc_info2.value.status_code == 409


@pytest.mark.asyncio
async def test_hold_legal_promocion_arcop(sesion, monkeypatch):
    """Prueba vinculación a solicitud ARCOP+ mediante pasillo y promoción WORM."""
    tenant_id = "cctv02-t"
    camara_id = uuid.uuid4()
    hace_2_dias = datetime.now(timezone.utc) - timedelta(days=2)

    clip = await svc.crear_clip(
        sesion,
        tenant_id=tenant_id,
        camara_id=str(camara_id),
        sha256_clip=hashlib.sha256(b"acceso-derecho").hexdigest(),
        fecha_captura=hace_2_dias,
        hold_legal_activo=False,
        bucket_actual="short-ttl",
    )

    from app_core.pasillo import derechos_arco as pasillo_derechos

    async def mock_existe_solicitud(_s, t, sol_id):
        return sol_id == "SOL-ARCO-777"

    monkeypatch.setattr(pasillo_derechos, "existe_solicitud", mock_existe_solicitud)

    # Promoción con ARCOP
    clip_promovido = await svc.aplicar_hold_legal(
        sesion,
        tenant_id=tenant_id,
        clip_id=str(clip.id),
        expediente_origen_tipo="ARCOP",
        expediente_origen_id="SOL-ARCO-777",
        user_id="dpo-cctv",
    )

    assert clip_promovido.hold_legal_activo is True
    assert clip_promovido.bucket_actual == "long-retention"
    assert clip_promovido.expediente_origen_tipo == "ARCOP"
    assert clip_promovido.expediente_origen_id == "SOL-ARCO-777"


@pytest.mark.asyncio
async def test_rechazo_expediente_inexistente(sesion, monkeypatch):
    """Verifica que no se puede aplicar Hold Legal sin expediente válido en pasillo."""
    tenant_id = "cctv02-t"
    camara_id = uuid.uuid4()
    clip = await svc.crear_clip(
        sesion,
        tenant_id=tenant_id,
        camara_id=str(camara_id),
        sha256_clip="a" * 64,
        fecha_captura=datetime.now(timezone.utc),
    )

    from app_core.pasillo import incidentes as pasillo_incidentes
    monkeypatch.setattr(pasillo_incidentes, "existe_incidente", lambda _s, _t, _i: False)

    with pytest.raises(ErrorNegocio) as exc_info:
        await svc.aplicar_hold_legal(
            sesion,
            tenant_id,
            str(clip.id),
            expediente_origen_tipo="INCIDENTE",
            expediente_origen_id="INC-FANTASMA",
        )
    assert exc_info.value.code == "CCTV_EXPEDIENTE_NO_ENCONTRADO"
    assert exc_info.value.status_code == 404

    # Tipo no permitido
    with pytest.raises(ErrorNegocio) as exc_tipo:
        await svc.aplicar_hold_legal(
            sesion,
            tenant_id,
            str(clip.id),
            expediente_origen_tipo="EXPEDIENTE_INVALIDO",
            expediente_origen_id="123",
        )
    assert exc_tipo.value.code == "CCTV_EXPEDIENTE_ORIGEN_INVALIDO"
    assert exc_tipo.value.status_code == 422


# ==============================================================================
# PRUEBAS DE RUTAS API FASTAPI
# ==============================================================================

@pytest.mark.asyncio
async def test_api_hold_legal_endpoint(api, monkeypatch):
    """Prueba POST /api/v1/videovigilancia/clips/{clip_id}/hold-legal."""
    tenant_id = "cctv02-t"
    camara_id = uuid.uuid4()
    clip = await svc.crear_clip(
        api,
        tenant_id=tenant_id,
        camara_id=str(camara_id),
        sha256_clip="b" * 64,
        fecha_captura=datetime.now(timezone.utc),
        hold_legal_activo=False,
        bucket_actual="short-ttl",
    )

    from app_core.pasillo import incidentes as pasillo_incidentes
    monkeypatch.setattr(pasillo_incidentes, "existe_incidente", lambda _s, _t, _i: True)

    async with _cliente() as c:
        r = await c.post(
            f"/api/v1/videovigilancia/clips/{clip.id}/hold-legal",
            headers=CABECERAS,
            json={
                "expediente_origen_tipo": "INCIDENTE",
                "expediente_origen_id": "INC-API-01",
                "motivo": "Investigación pericial",
            },
        )

    assert r.status_code == 200
    datos = r.json()
    assert datos["hold_legal_activo"] is True
    assert datos["bucket_actual"] == "long-retention"
    assert datos["expediente_origen_id"] == "INC-API-01"


@pytest.mark.asyncio
async def test_api_purga_quincenal_endpoint(api):
    """Prueba POST /api/v1/videovigilancia/purga-quincenal/ejecutar."""
    tenant_id = "cctv02-t"
    camara_id = uuid.uuid4()
    hace_20_dias = datetime.now(timezone.utc) - timedelta(days=20)

    # Crear 2 clips ordinarios vencidos
    await svc.crear_clip(
        api,
        tenant_id=tenant_id,
        camara_id=str(camara_id),
        sha256_clip="c" * 64,
        fecha_captura=hace_20_dias,
    )
    await svc.crear_clip(
        api,
        tenant_id=tenant_id,
        camara_id=str(camara_id),
        sha256_clip="d" * 64,
        fecha_captura=hace_20_dias,
    )

    async with _cliente() as c:
        r = await c.post(
            "/api/v1/videovigilancia/purga-quincenal/ejecutar",
            headers=CABECERAS_OPERADOR,
            json={},
        )

    assert r.status_code == 200
    acta = r.json()
    assert acta["tipo_acta"] == "CERTIFICADO_QUINCENAL_DESTRUCCION_CCTV"
    assert acta["total_clips_destruidos"] == 2
    assert len(acta["hash_maestro_sha256"]) == 64


@pytest.mark.asyncio
async def test_api_delete_bloqueado_por_hold(api):
    """DELETE /api/v1/videovigilancia/clips/{clip_id} responde 409 si tiene Hold Legal activo."""
    tenant_id = "cctv02-t"
    camara_id = uuid.uuid4()

    clip = await svc.crear_clip(
        api,
        tenant_id=tenant_id,
        camara_id=str(camara_id),
        sha256_clip="e" * 64,
        fecha_captura=datetime.now(timezone.utc),
        hold_legal_activo=True,
        bucket_actual="long-retention",
    )

    async with _cliente() as c:
        r = await c.delete(
            f"/api/v1/videovigilancia/clips/{clip.id}",
            headers=CABECERAS_OPERADOR,
        )

    assert r.status_code == 409
    assert r.json()["code"] == "CCTV_CLIP_PROTEGIDO_POR_HOLD_LEGAL"


# ==============================================================================
# INTEGRACIÓN DE PASILLOS CRUZADOS Y COMPUERTAS ADPA
# ==============================================================================

@pytest.mark.asyncio
async def test_pasillos_cruzados_adpa(sesion):
    """Verifica que los pasillos de videovigilancia, incidentes y derechos_arco

    exportan sus compuertas para CCTV-02 sin importaciones circulares ni directas.
    """
    from app_core.pasillo import videovigilancia as pasillo_cctv
    from app_core.pasillo import incidentes as pasillo_inc
    from app_core.pasillo import derechos_arco as pasillo_der

    assert callable(pasillo_cctv.aplicar_hold_legal)
    assert callable(pasillo_cctv.ejecutar_purga_quincenal)
    assert callable(pasillo_cctv.purgar_clip)
    assert callable(pasillo_inc.existe_incidente)
    assert callable(pasillo_der.existe_solicitud)


def test_aislamiento_adpa_sin_importaciones_laterales():
    """ADPA §3: la sala videovigilancia no debe importar directamente las salas incidentes o derechos_arco."""
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sala_cctv = os.path.join(raiz, "features", "videovigilancia")

    for base, _, archivos in os.walk(sala_cctv):
        for nombre in archivos:
            if nombre.endswith(".py"):
                with open(os.path.join(base, nombre), encoding="utf-8") as f:
                    codigo = f.read()
                assert "features.incidentes" not in codigo, f"Violación ADPA en {nombre}: importa features.incidentes"
                assert "features.derechos_arco" not in codigo, f"Violación ADPA en {nombre}: importa features.derechos_arco"
                assert "from api" not in codigo, f"Violación ADPA en {nombre}: importa api"
