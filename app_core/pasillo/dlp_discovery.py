# ¤adpa ¤dlp-muestreo
"""Capacidades de la sala Descubrimiento DLP Muestreado para otras salas (solo conteos, nunca la muestra)."""
# === DLP-01 ===


async def listar_escaneos(session, tenant_id: str, limite: int = 50):
    from features.dlp_discovery import dlp_discovery_service as svc

    return await svc.listar_escaneos(session, tenant_id, limite)


def cedula_valida(cedula: str) -> bool:
    from features.dlp_discovery import dlp_discovery_service as svc

    return svc.cedula_valida(cedula)
# === fin DLP-01 ===
