# ¤adpa ¤videovigilancia-cctv
"""Capacidades de la sala Videovigilancia para otras salas (solo reexporta; se importa al usarla)."""
# === CCTV-01 ===


async def listar_camaras(session, tenant_id: str, limite: int = 200):
    from features.videovigilancia import videovigilancia_service as svc

    return await svc.listar_camaras(session, tenant_id, limite)
# === fin CCTV-01 ===
