# ¤adpa ¤seguridad
"""Capacidades de la sala Plataforma para otras salas (solo reexporta; se importa al usarla)."""
# === BOV-01 ===


async def verificar_operador(session, email: str, sub=None) -> dict:
    """Operador de plataforma activo (ORG-09); si no lo es, la sala Plataforma responde 403.

    Delegación pura en plataforma_service.verificar_operador, la misma que usa api/routers/plataforma.py.
    """
    from features.plataforma import plataforma_service

    return await plataforma_service.verificar_operador(session, email=email, sub=sub)
# === fin BOV-01 ===
