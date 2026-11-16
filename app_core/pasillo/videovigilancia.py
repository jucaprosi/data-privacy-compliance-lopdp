# ¤adpa ¤videovigilancia-cctv
"""Capacidades de la sala Videovigilancia para otras salas (solo reexporta; se importa al usarla)."""
# === CCTV-01 ===


async def listar_camaras(session, tenant_id: str, limite: int = 200):
    from features.videovigilancia import videovigilancia_service as svc

    return await svc.listar_camaras(session, tenant_id, limite)
# === fin CCTV-01 ===
# === CCTV-02 ===


async def aplicar_hold_legal(session, tenant_id: str, clip_id: str, expediente_origen_tipo: str, expediente_origen_id: str, user_id=None):
    """Promueve el clip a long-retention WORM por incidente o derecho ARCOP+ (CCTV-02)."""
    from features.videovigilancia import videovigilancia_service as svc

    return await svc.aplicar_hold_legal(session, tenant_id, clip_id, expediente_origen_tipo, expediente_origen_id, user_id)


async def ejecutar_purga_quincenal(session, tenant_id: str, user_id=None, fecha_corte=None):
    """Ejecuta la purga quincenal de 15 días y emite acta SHA-256 (CCTV-02)."""
    from features.videovigilancia import videovigilancia_service as svc

    return await svc.ejecutar_purga_quincenal(session, tenant_id, user_id, fecha_corte)


async def purgar_clip(session, tenant_id: str, clip_id: str, user_id=None):
    """Intento de purgar clip individual: 409 si hold_legal_activo (INV_LOPDP_CCTV_LEGAL_HOLD_OVERRIDE)."""
    from features.videovigilancia import videovigilancia_service as svc

    return await svc.purgar_clip(session, tenant_id, clip_id, user_id)


async def obtener_clip(session, tenant_id: str, clip_id: str):
    """Obtiene un clip de la bóveda (CCTV-02)."""
    from features.videovigilancia import videovigilancia_service as svc

    return await svc.obtener_clip(session, tenant_id, clip_id)


async def listar_clips(session, tenant_id: str, limite: int = 200, incluir_destruidos: bool = False):
    """Lista clips para la línea de tiempo (CCTV-02)."""
    from features.videovigilancia import videovigilancia_service as svc

    return await svc.listar_clips(session, tenant_id, limite, incluir_destruidos)
# === fin CCTV-02 ===

# === DEMO-03f ===
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


async def clonar_desde_plantilla(
    session: AsyncSession, origen: str, destino: str, mapa_ids: dict[str, str]
) -> dict[str, str]:
    """Copia las cámaras de la plantilla al tenant destino (DEMO-02 la llama en su orden)."""
    from features.videovigilancia import videovigilancia_service

    return await videovigilancia_service.clonar_desde_plantilla(session, origen, destino, mapa_ids)


async def sembrar_en_plantilla(session: AsyncSession, plantilla_id: str, datos: Any = None) -> None:
    from features.videovigilancia import videovigilancia_service

    return await videovigilancia_service.sembrar_en_plantilla(session, plantilla_id, datos)
# === fin DEMO-03f ===

# --- INICIO GOCA-01 ---
async def generar_aprovisionamiento_agente_go(camara_id: str, tenant_id: str):
    from features.videovigilancia.services.cctv_provisioning_bundle import generar_bundle_aprovisionamiento
    return generar_bundle_aprovisionamiento(camara_id, tenant_id)
# --- FIN GOCA-01 ---
