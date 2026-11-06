# ¤adpa
"""Adaptador del puerto de avisos de impacto de Biblioteca (BIB-304) sobre la compuerta de Notificaciones.

La sala biblioteca no conoce a notificaciones: su motor recibe el constructor de avisos y el router
inyecta este adaptador. Aquí no hay lógica de negocio."""


def construir_aviso_impacto(expediente_id: str, tenant_id: str, app_base_url: str) -> dict[str, str]:
    from features.notificaciones import notificaciones_service

    return notificaciones_service.construir_aviso_impacto(expediente_id, tenant_id, app_base_url)
