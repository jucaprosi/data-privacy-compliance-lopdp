# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤boveda-cloud ¤videovigilancia-cctv ¤dpo-cockpit ¤conservacion ¤arbitro
"""Pruebas de BOV-04: Orquestador Comercial de las 10 Dimensiones LOPDP y Bóveda Cloud.

Cubre:
- Desglose separado de las 10 dimensiones D01..D10 sin porcentaje único global (`INV_LOPDP_MULTIDIMENSIONAL_METRICS`).
- Endpoint `GET /api/v1/boveda-cloud/orquestador-10d` con autenticación, RBAC (`ROLES_CONSULTA`) y aislamiento por tenant.
- Consulta de solo lectura para el DPO vía `app_core/pasillo/dpo_cockpit.py#BOV-04` con actas SHA-256 y clips en Hold Legal.
- Rechazo estricto (422) ante actas SHA-256 inválidas o intentos de proyectar métrica global.
"""
from __future__ import annotations

import ast
import hashlib
import os
import uuid
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from pydantic import ValidationError

if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or "postgresql+psycopg://u:c@localhost/pruebas"

from app_core.bucle_eventos import configurar_bucle_eventos  # noqa: E402

configurar_bucle_eventos()

from api.errores import ErrorNegocio, error_negocio_handler  # noqa: E402
from app_core.db.session import get_session  # noqa: E402
from app_core.pasillo import boveda_cloud as pasillo_boveda  # noqa: E402
from app_core.pasillo import dpo_cockpit as pasillo_dpo  # noqa: E402
from features.boveda_cloud import boveda_cloud_service as svc  # noqa: E402
from features.boveda_cloud.domain import errores  # noqa: E402
from features.boveda_cloud.routes import orquestador_routes as rutas  # noqa: E402
from features.boveda_cloud.services import orquestador_diez_dimensiones as motor  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
RUTA = "/api/v1/boveda-cloud/orquestador-10d"

app = FastAPI()
app.add_exception_handler(ErrorNegocio, error_negocio_handler)
app.include_router(svc.router_orquestador(), prefix="/api/v1")


@pytest.fixture(autouse=True)
def _limpiar_registro():
    svc.limpiar_registro_orquestador()
    yield
    svc.limpiar_registro_orquestador()


def _sha(semilla: str) -> str:
    return hashlib.sha256(semilla.encode("utf-8")).hexdigest()


async def _peticion(
    metodo: str,
    rol: str,
    tenant_id: str,
    monkeypatch: pytest.MonkeyPatch,
    params: dict | None = None,
):
    monkeypatch.setattr(rutas, "modo_autenticacion", lambda: rutas.MODO_HEADERS)

    async def _todos(session, t_id, usuario):
        return {"admin_organizacion", "dpo", "coordinador", "auditor", "implementador", "responsable_area"}

    monkeypatch.setattr(rutas, "roles_activos", _todos)
    app.dependency_overrides[get_session] = lambda: None
    cabeceras = {"X-User-ID": "u-bov04", "X-Tenant-ID": tenant_id, "X-Role": rol}
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://bov04.invalid") as api:
            return await api.request(metodo, RUTA, headers=cabeceras, params=params)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_orquestador_10_dimensiones_sin_cifra_unica(monkeypatch):
    """Mutación: devolver < 10 dimensiones o incluir métrica/porcentaje único global -> rojo."""
    sha_acta_1 = _sha("acta-cctv-2026-11-15")
    sha_acta_2 = _sha("acta-conservacion-2026-11-16")

    svc.registrar_estado_orquestador_tenant(
        "org-alfa",
        paquete_codigo="PROFESIONAL",
        estado_suscripcion="ACTIVA",
        uso_boveda_gb=42.5,
        cuota_boveda_gb=250.0,
        uso_egress_gb=18.25,
        cuota_egress_gb=500.0,
        camaras_activas=12,
        clips_en_hold_legal=3,
        escaneos_dlp_completados=7,
        estado_cache_normativo="ACTIVO",
        dimensiones=[
            {
                "codigo": "D01",
                "nombre": "Gobierno y responsabilidad proactiva",
                "nivel_asignado": 4,
                "nivel_evidencia": 3,
                "controles_conformes": 7,
                "controles_totales": 8,
                "evidencias_custodiadas": 11,
                "estado_operativo": "CONFORME",
                "automatizacion_activa": True,
            },
            {
                "codigo": "D05",
                "nombre": "Procesos críticos y ciclo de vida de datos",
                "nivel_asignado": 3,
                "nivel_evidencia": 2,
                "controles_conformes": 5,
                "controles_totales": 6,
                "evidencias_custodiadas": 9,
                "estado_operativo": "PARCIAL",
                "automatizacion_activa": True,
            },
        ],
        actas_sha256=[
            {
                "acta_id": "ACTA-CCTV-001",
                "origen": "CCTV_QUINCENAL",
                "fecha_emision": "2026-11-15T05:00:00+00:00",
                "sha256": sha_acta_1.upper(),
                "elementos_purgados": 48,
                "elementos_hold_legal": 3,
                "verificada_dpo": True,
            },
            {
                "acta_id": "ACTA-CON-002",
                "origen": "CONSERVACION_PURGA",
                "fecha_emision": "2026-11-16T10:30:00+00:00",
                "sha256": sha_acta_2,
                "elementos_purgados": 12,
                "elementos_hold_legal": 0,
                "verificada_dpo": True,
            },
        ],
    )

    resumen = await svc.obtener_resumen_orquestador_10d(None, "org-alfa")
    assert resumen.tenant_id == "org-alfa"
    assert [d.codigo for d in resumen.dimensiones] == [f"D{i:02d}" for i in range(1, 11)]
    assert len(resumen.dimensiones) == 10
    assert resumen.uso_boveda_gb == 42.5
    assert resumen.uso_egress_gb == 18.25
    assert resumen.camaras_activas == 12
    assert resumen.clips_en_hold_legal == 3
    assert resumen.actas_destruccion_emitidas == 2
    assert resumen.escaneos_dlp_completados == 7
    assert resumen.estado_cache_normativo == "ACTIVO"
    assert [a.sha256 for a in resumen.actas_sha256] == [sha_acta_1, sha_acta_2]

    # Ninguna clave del modelo ni de su serialización representa un porcentaje único global.
    serializado = resumen.model_dump()
    assert not (motor.CAMPOS_METRICA_GLOBAL_PROHIBIDOS & set(serializado.keys()))

    # Verificación HTTP: GET /api/v1/boveda-cloud/orquestador-10d para roles autorizados
    resp_admin = await _peticion("GET", "admin_organizacion", "org-alfa", monkeypatch)
    assert resp_admin.status_code == 200
    cuerpo = resp_admin.json()
    assert cuerpo["tenant_id"] == "org-alfa"
    assert len(cuerpo["dimensiones"]) == 10
    assert [d["codigo"] for d in cuerpo["dimensiones"]] == [f"D{i:02d}" for i in range(1, 11)]
    assert cuerpo["uso_boveda_gb"] == 42.5
    assert cuerpo["uso_egress_gb"] == 18.25
    assert cuerpo["camaras_activas"] == 12
    assert cuerpo["clips_en_hold_legal"] == 3
    assert cuerpo["actas_destruccion_emitidas"] == 2
    assert cuerpo["escaneos_dlp_completados"] == 7
    assert cuerpo["modo_lectura"] is False
    assert not (motor.CAMPOS_METRICA_GLOBAL_PROHIBIDOS & set(cuerpo.keys()))

    # Aislamiento por tenant: otro tenant no hereda telemetría ni actas de org-alfa
    resp_beta = await _peticion("GET", "coordinador", "org-beta", monkeypatch)
    assert resp_beta.status_code == 200
    cuerpo_beta = resp_beta.json()
    assert cuerpo_beta["tenant_id"] == "org-beta"
    assert cuerpo_beta["camaras_activas"] == 0
    assert cuerpo_beta["actas_sha256"] == []

    # Roles fuera de ROLES_CONSULTA reciben 403
    for rol_denegado in ("auditor", "implementador", "responsable_area"):
        resp_denegado = await _peticion("GET", rol_denegado, "org-alfa", monkeypatch)
        assert resp_denegado.status_code == 403

    # Modo OIDC sin Bearer token rechaza 401
    monkeypatch.setattr(rutas, "modo_autenticacion", lambda: "oidc")
    app.dependency_overrides[get_session] = lambda: None
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://bov04.invalid") as api:
            resp_sin_token = await api.get(RUTA, headers={"X-Tenant-ID": "org-alfa", "X-Role": "dpo"})
            assert resp_sin_token.status_code == 401
            resp_sin_tenant = await api.get(RUTA, headers={"X-Tenant-ID": "   ", "X-Role": "dpo"})
            assert resp_sin_tenant.status_code == 400
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_dpo_consulta_orquestador_boveda_read_only(monkeypatch):
    """Mutación: permitir mutar la proyección del DPO o exponer modo_lectura=False -> rojo."""
    sha_purga = _sha("acta-quincenal-hold-legal")
    svc.registrar_estado_orquestador_tenant(
        "org-dpo",
        camaras_activas=6,
        clips_en_hold_legal=4,
        escaneos_dlp_completados=3,
        actas_sha256=[
            {
                "acta_id": "ACTA-DPO-001",
                "origen": "CCTV_QUINCENAL",
                "sha256": sha_purga,
                "elementos_purgados": 19,
                "elementos_hold_legal": 4,
                "verificada_dpo": True,
            }
        ],
    )

    vista_dpo = await pasillo_dpo.consultar_orquestador_boveda_dpo(None, "org-dpo")
    assert vista_dpo.modo_lectura is True
    assert vista_dpo.clips_en_hold_legal == 4
    assert vista_dpo.actas_destruccion_emitidas == 1
    assert vista_dpo.actas_sha256[0].sha256 == sha_purga

    # El pasillo propio de bóveda también expone la consulta en modo solo lectura
    vista_pasillo = await pasillo_boveda.consultar_orquestador_boveda_dpo(None, "org-dpo")
    assert vista_pasillo.modo_lectura is True
    assert vista_pasillo.actas_sha256 == vista_dpo.actas_sha256

    # La proyección entregada al DPO es inmutable (solo lectura)
    with pytest.raises(ValidationError):
        vista_dpo.modo_lectura = False  # type: ignore[misc]
    with pytest.raises(ValidationError):
        vista_dpo.clips_en_hold_legal = 0  # type: ignore[misc]

    # Vía HTTP como rol `dpo`: responde 200 con modo_lectura=True y no admite escritura (405)
    resp_dpo = await _peticion("GET", "dpo", "org-dpo", monkeypatch)
    assert resp_dpo.status_code == 200
    datos_dpo = resp_dpo.json()
    assert datos_dpo["modo_lectura"] is True
    assert datos_dpo["clips_en_hold_legal"] == 4
    assert datos_dpo["actas_sha256"][0]["sha256"] == sha_purga

    resp_post = await _peticion("POST", "dpo", "org-dpo", monkeypatch)
    assert resp_post.status_code == 405


def test_actas_sha256_validacion_estricta():
    """R2: rechaza con 422 BOVEDA_ACTA_SHA256_INVALIDA cualquier huella que no sea 64 hexadecimales."""
    sha_valido = _sha("evidencia-destruccion-valida")
    acta = svc.ActaDestruccionCertificada(
        acta_id="ACTA-OK",
        sha256=sha_valido.upper(),
        elementos_purgados=5,
        elementos_hold_legal=1,
    )
    assert acta.sha256 == sha_valido

    for huella_mala in ("", "no-es-sha", "abc123", "g" * 64, "a" * 63):
        with pytest.raises(ErrorNegocio) as exc:
            svc.registrar_estado_orquestador_tenant(
                "org-bad-sha",
                actas_sha256=[{"acta_id": "ACTA-MALA", "sha256": huella_mala}],
            )
        assert (exc.value.code, exc.value.status_code) == (errores.BOVEDA_ACTA_SHA256_INVALIDA, 422)


@pytest.mark.asyncio
async def test_prohibicion_metrica_global_en_servicio_y_http(monkeypatch):
    """R1 (INV_LOPDP_MULTIDIMENSIONAL_METRICS): rechaza con 422 todo intento de métrica global única."""
    for clave_prohibida in ("porcentaje_global", "puntaje_global", "metrica_global"):
        with pytest.raises(ErrorNegocio) as exc:
            svc.registrar_estado_orquestador_tenant("org-global", {clave_prohibida: 88.5})
        assert (exc.value.code, exc.value.status_code) == (errores.BOVEDA_METRICA_GLOBAL_PROHIBIDA, 422)

    with pytest.raises(ErrorNegocio) as exc_dim:
        svc.registrar_estado_orquestador_tenant(
            "org-global",
            dimensiones=[{"codigo": "GLOBAL", "nombre": "Global"}],
        )
    assert (exc_dim.value.code, exc_dim.value.status_code) == (errores.BOVEDA_METRICA_GLOBAL_PROHIBIDA, 422)

    with pytest.raises(ErrorNegocio) as exc_svc:
        await svc.obtener_resumen_orquestador_10d(None, "org-global", incluir_metrica_global=True)
    assert (exc_svc.value.code, exc_svc.value.status_code) == (errores.BOVEDA_METRICA_GLOBAL_PROHIBIDA, 422)

    resp = await _peticion(
        "GET",
        "dpo",
        "org-global",
        monkeypatch,
        params={"incluir_metrica_global": "true"},
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == errores.BOVEDA_METRICA_GLOBAL_PROHIBIDA


def test_bov04_cumple_mamparos_adpa_sin_imports_cruzados():
    """ADPA §3 y §7.1: la sala boveda_cloud no importa api ni otras salas de features."""
    for rel in (
        "features/boveda_cloud/services/orquestador_diez_dimensiones.py",
        "features/boveda_cloud/routes/orquestador_routes.py",
    ):
        arbol = ast.parse((RAIZ / rel).read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            modulos: list[str] = []
            if isinstance(nodo, ast.Import):
                modulos = [a.name for a in nodo.names]
            elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0:
                modulos = [nodo.module]
            for mod in modulos:
                assert mod != "api" and not mod.startswith("api."), f"{rel} importa {mod}"
                if mod.startswith("features."):
                    assert mod.startswith("features.boveda_cloud"), f"{rel} cruza sala hacia {mod}"


_URL_BD = os.environ.get("TEST_DATABASE_URL", "")


@pytest.mark.skipif(not _URL_BD, reason="TEST_DATABASE_URL no configurada")
@pytest.mark.asyncio
async def test_integracion_bd_orquestador_con_suscripcion():
    """Con PostgreSQL de pruebas, consolida suscripción real de Bóveda Cloud respetando RLS."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

    url = _URL_BD.replace("postgresql://", "postgresql+psycopg://", 1) if _URL_BD.startswith("postgresql://") else _URL_BD
    engine = create_async_engine(url, hide_parameters=True)
    tid = f"bov04-{uuid.uuid4().hex[:10]}"
    gb = 1024**3
    try:
        async with engine.connect() as conn:
            tx = await conn.begin()
            try:
                await conn.execute(
                    text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:t, :t, :t, :t)"),
                    {"t": tid},
                )
                await conn.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tid})
                await conn.execute(
                    text(
                        "INSERT INTO boveda_suscripciones_tenant (tenant_id, paquete_codigo, "
                        "cuota_almacenamiento_bytes, uso_almacenamiento_bytes, "
                        "cuota_egress_mensual_bytes, uso_egress_mensual_bytes) "
                        "VALUES (:t, 'INICIAL', :ca, :ua, :ce, :ue)"
                    ),
                    {"t": tid, "ca": 50 * gb, "ua": 10 * gb, "ce": 100 * gb, "ue": 5 * gb},
                )
                await conn.execute(text("SET LOCAL ROLE lopdp_app"))
                async with AsyncSession(bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint") as s:
                    resumen = await pasillo_dpo.consultar_orquestador_boveda_dpo(s, tid)
                    assert resumen.modo_lectura is True
                    assert resumen.paquete_codigo == "INICIAL"
                    assert resumen.uso_boveda_gb == 10.0
                    assert resumen.cuota_boveda_gb == 50.0
                    assert resumen.uso_egress_gb == 5.0
                    assert resumen.cuota_egress_gb == 100.0
                    assert len(resumen.dimensiones) == 10
            finally:
                await tx.rollback()
    finally:
        await engine.dispose()
