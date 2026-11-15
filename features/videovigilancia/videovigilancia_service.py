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
