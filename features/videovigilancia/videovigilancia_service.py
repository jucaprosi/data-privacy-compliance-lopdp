# ¤videovigilancia-cctv ¤boveda-cloud ¤rat ¤seguridad-tenant ¤adpa
"""Compuerta de la sala Videovigilancia. Fuera de la sala solo se importa este módulo (o el pasillo)."""
# === CCTV-01 ===
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from features.videovigilancia.domain import errores
from features.videovigilancia.models import CamaraInventario
from features.videovigilancia.schemas import CamaraSalida, SolicitudCamara

__all__ = [
    "BUCKET_DESTINO",
    "CODECS_PERMITIDOS",
    "MODO_GRABACION_PERMITIDO",
    "ROLES_ALTA",
    "ROLES_CONSULTA",
    "CamaraSalida",
    "SolicitudCamara",
    "errores",
    "listar_camaras",
    "registrar_camara",
    "router",
    "validar_perfil_tecnico",
]

CODECS_PERMITIDOS = ("H265", "H265_PLUS")
MODO_GRABACION_PERMITIDO = "EVENTO_MOVIMIENTO"
# Las grabaciones ordinarias van al pool de 15 días de la Bóveda Dual (INV 30); el congelamiento forense es de CCTV-02.
BUCKET_DESTINO = "short-ttl"

# Dan de alta quienes operan el inventario; consultan, además, el DPO y el auditor (supuesto: la especificación no fija roles).
ROLES_ALTA = ("admin_organizacion", "coordinador", "implementador")
ROLES_CONSULTA = ROLES_ALTA + ("dpo", "auditor")


def __getattr__(nombre: str):
    # El router se carga al pedirlo (main.py), para que las rutas importen esta compuerta sin ciclo.
    if nombre == "router":
        from features.videovigilancia.routes.videovigilancia_routes import router

        return router
    raise AttributeError(nombre)


def validar_perfil_tecnico(solicitud: SolicitudCamara) -> None:
    """R1 y R2: rechaza con ErrorNegocio 422 la cámara intrusiva o sin el perfil técnico LOPDP."""
    if solicitud.audio_ambiental_activo:
        raise errores.error(errores.CCTV_AUDIO_AMBIENTAL_PROHIBIDO)
    if solicitud.codec not in CODECS_PERMITIDOS:
        raise errores.error(errores.CCTV_CODEC_NO_OPTIMIZADO)
    if solicitud.modo_grabacion != MODO_GRABACION_PERMITIDO or not solicitud.mascara_privacidad_activa:
        raise errores.error(errores.CCTV_CONFIGURACION_NO_CONFORME)


def _a_salida(c: CamaraInventario) -> CamaraSalida:
    return CamaraSalida(
        id=str(c.id), nombre_ubicacion=c.nombre_ubicacion, codec=c.codec, modo_grabacion=c.modo_grabacion,
        audio_ambiental_activo=c.audio_ambiental_activo, mascara_privacidad_activa=c.mascara_privacidad_activa,
        plazo_retencion_dias=c.plazo_retencion_dias, estado_conformidad=c.estado_conformidad,
        actividad_rat_id=c.actividad_rat_id, bucket_destino=BUCKET_DESTINO, creado_en=c.creado_en,
    )


async def registrar_camara(
    session: AsyncSession, tenant_id: str, user_id: str, solicitud: SolicitudCamara
) -> CamaraSalida:
    """Valida el perfil, comprueba la actividad del RAT (si viene) y da de alta la cámara habilitada para la Bóveda."""
    validar_perfil_tecnico(solicitud)
    if solicitud.actividad_rat_id is not None:
        from app_core.pasillo import rat as pasillo_rat

        if not await pasillo_rat.existe_actividad(session, tenant_id, solicitud.actividad_rat_id):
            raise errores.error(errores.CCTV_ACTIVIDAD_RAT_NO_ENCONTRADA)
    camara = CamaraInventario(
        tenant_id=tenant_id, nombre_ubicacion=solicitud.nombre_ubicacion.strip(), codec=solicitud.codec,
        modo_grabacion=solicitud.modo_grabacion, audio_ambiental_activo=False, mascara_privacidad_activa=True,
        plazo_retencion_dias=solicitud.plazo_retencion_dias, estado_conformidad="CONFORME",
        actividad_rat_id=solicitud.actividad_rat_id, creado_por=user_id,
    )
    session.add(camara)
    await session.flush()
    await session.refresh(camara)
    await registrar_evento(
        session, tenant_id, "cctv_camara", str(camara.id), "alta_camara", user_id=user_id,
        payload={"codec": camara.codec, "plazo_retencion_dias": camara.plazo_retencion_dias},
    )
    await session.commit()
    return _a_salida(camara)


async def listar_camaras(session: AsyncSession, tenant_id: str, limite: int = 200) -> list[CamaraSalida]:
    filas = await session.execute(
        select(CamaraInventario)
        .where(CamaraInventario.tenant_id == tenant_id)
        .order_by(CamaraInventario.creado_en.desc())
        .limit(limite)
    )
    return [_a_salida(c) for c in filas.scalars()]
# === fin CCTV-01 ===
# === CCTV-02 ===
from typing import Any, Optional
from features.videovigilancia.services import cctv_legal_hold_engine as hold_engine

ROLES_HOLD_LEGAL = ("admin_organizacion", "coordinador", "implementador", "dpo")
ROLES_PURGA = ("admin_organizacion", "coordinador", "implementador", "dpo")
ROLES_CONSULTA_CLIPS = ROLES_CONSULTA

__all__ += [
    "ROLES_HOLD_LEGAL",
    "ROLES_PURGA",
    "ROLES_CONSULTA_CLIPS",
    "aplicar_hold_legal",
    "crear_clip",
    "ejecutar_purga_quincenal",
    "eliminar_clip",
    "listar_actas_purga",
    "listar_clips",
    "obtener_clip",
    "purgar_clip",
]


async def aplicar_hold_legal(
    session: AsyncSession,
    tenant_id: str,
    clip_id: str,
    expediente_origen_tipo: str,
    expediente_origen_id: str,
    user_id: Optional[str] = None,
):
    """R2: Promueve el clip al bucket WORM 'long-retention' con Object Lock."""
    return await hold_engine.aplicar_hold_legal(
        session, tenant_id, clip_id, expediente_origen_tipo, expediente_origen_id, user_id
    )


async def ejecutar_purga_quincenal(
    session: AsyncSession,
    tenant_id: str,
    user_id: Optional[str] = None,
    fecha_corte: Optional[datetime] = None,
) -> dict[str, Any]:
    """R1 y R3: Destruye clips >= 15 días ordinarios y emite acta SHA-256; respeta Hold Legal."""
    return await hold_engine.ejecutar_purga_quincenal(session, tenant_id, user_id, fecha_corte)


async def purgar_clip(
    session: AsyncSession,
    tenant_id: str,
    clip_id: str,
    user_id: Optional[str] = None,
) -> None:
    """R1: Purga individual; rechaza con 409 si hold_legal_activo (INV_LOPDP_CCTV_LEGAL_HOLD_OVERRIDE)."""
    await hold_engine.purgar_clip_individual(session, tenant_id, clip_id, user_id)


async def eliminar_clip(
    session: AsyncSession,
    tenant_id: str,
    clip_id: str,
    user_id: Optional[str] = None,
) -> None:
    """R1: Intento directo de borrado de clip; rechaza con 409 si hold_legal_activo."""
    await hold_engine.purgar_clip_individual(session, tenant_id, clip_id, user_id)


async def crear_clip(
    session: AsyncSession,
    tenant_id: str,
    camara_id: str,
    sha256_clip: str,
    fecha_captura: datetime,
    expira_en: Optional[datetime] = None,
    hold_legal_activo: bool = False,
    expediente_origen_tipo: Optional[str] = None,
    expediente_origen_id: Optional[str] = None,
    bucket_actual: str = "short-ttl",
):
    """Crea un clip para custodia en la bóveda dual."""
    return await hold_engine.crear_clip(
        session,
        tenant_id,
        camara_id,
        sha256_clip,
        fecha_captura,
        expira_en,
        hold_legal_activo,
        expediente_origen_tipo,
        expediente_origen_id,
        bucket_actual,
    )


async def obtener_clip(session: AsyncSession, tenant_id: str, clip_id: str):
    return await hold_engine.obtener_clip(session, tenant_id, clip_id)


async def listar_clips(
    session: AsyncSession,
    tenant_id: str,
    limite: int = 200,
    incluir_destruidos: bool = False,
):
    return await hold_engine.listar_clips(session, tenant_id, limite, incluir_destruidos)


async def listar_actas_purga(session: AsyncSession, tenant_id: str, limite: int = 100):
    return await hold_engine.listar_actas(session, tenant_id, limite)


_getattr_cctv01 = __getattr__


def __getattr__(nombre: str):
    if nombre == "router":
        from fastapi import APIRouter
        from features.videovigilancia.routes.videovigilancia_routes import router as r1
        from features.videovigilancia.routes.cctv_hold_routes import router as r2

        unificado = APIRouter()
        unificado.include_router(r1)
        unificado.include_router(r2)
        return unificado
    if nombre == "hold_router":
        from features.videovigilancia.routes.cctv_hold_routes import router as r2

        return r2
    return _getattr_cctv01(nombre)
# === fin CCTV-02 ===

# === DEMO-03f ===
from features.videovigilancia.services.clon_plantilla_engine import (  # noqa: E402
    clonar_desde_plantilla,
    sembrar_en_plantilla,
)

__all__.extend(["clonar_desde_plantilla", "sembrar_en_plantilla"])
# === fin DEMO-03f ===

