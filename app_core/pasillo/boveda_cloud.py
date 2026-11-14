# ¤adpa ¤boveda-cloud
"""Capacidades de la sala Bóveda Cloud para otras salas (solo reexporta; se importa al usarla)."""
# === BOV-01 ===


async def techos_integracion(session, tenant_id):
    """{"claves": int|None, "webhooks": int|None} del paquete de la organización (API-02)."""
    from features.boveda_cloud import boveda_cloud_service as svc

    return await svc.techos_integracion(session, tenant_id)


async def limites_uso(session, tenant_id):
    """{"peticiones_api_minuto": int|None, "tokens_ia_mes": int|None}; solo dato hasta SEC-13c."""
    from features.boveda_cloud import boveda_cloud_service as svc

    return await svc.limites_uso(session, tenant_id)


async def validar_consumo(session, tenant_id, tipo, bytes_solicitados):
    """Suma el consumo si cabe en la cuota; si no, ErrorNegocio 409 (o 404 sin suscripción)."""
    from features.boveda_cloud import boveda_cloud_service as svc

    return await svc.validar_consumo(session, tenant_id, tipo, bytes_solicitados)
# === fin BOV-01 ===
