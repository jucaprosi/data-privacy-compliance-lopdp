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
# === BOV-02 ===


async def solicitar_url_subida(session, tenant_id, solicitud, usuario_id, firmador=None):
    """URL firmada V4 de subida directa a la bóveda dual; registra la custodia del objeto."""
    from features.boveda_cloud import boveda_cloud_service as svc

    return await svc.solicitar_url_subida(session, tenant_id, solicitud, usuario_id, firmador)


async def solicitar_url_descarga(session, tenant_id, objeto_id, usuario_id, firmador=None):
    """URL firmada V4 de descarga de un objeto de la bóveda; cuenta el egress."""
    from features.boveda_cloud import boveda_cloud_service as svc

    return await svc.solicitar_url_descarga(session, tenant_id, objeto_id, usuario_id, firmador)
# === fin BOV-02 ===

# --- INICIO BOV-03 ---
def generar_preview_forense(objeto, formato="WEBP", destino_gcs_uri=None):
    from features.boveda_cloud import boveda_cloud_service as svc
    return svc.generar_preview_forense(objeto, formato, destino_gcs_uri)

def verificar_integridad_forense(objeto):
    from features.boveda_cloud import boveda_cloud_service as svc
    return svc.verificar_integridad_forense(objeto)
# --- FIN BOV-03 ---
