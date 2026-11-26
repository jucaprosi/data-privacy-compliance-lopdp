# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
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
# === NORM-02b ===


async def destinatarios_normativos(session) -> list[dict]:
    """[{tenant_id, correos_admin, correos_dpo}] de las organizaciones activas, solo por fn_destinatarios_normativos().

    Única lectura entre organizaciones de NORM-02b (R1, R2): sin nombres ni datos de la organización.
    """
    from features.plataforma import plataforma_service

    return await plataforma_service.destinatarios_normativos(session)


async def contar_organizaciones_activas(session) -> int:
    """Solo un número, para contar en la bitácora las organizaciones sin destinatarios (NORM-02b R7)."""
    from features.plataforma import plataforma_service

    return await plataforma_service.contar_organizaciones_activas(session)
# === fin NORM-02b ===
# === OPE-01 ===


async def operador_activo(session, usuario_id: str) -> bool:
    """El usuario es un operador activo de la plataforma; se lee en cada llamada (OPE-01 R3)."""
    from features.plataforma import plataforma_service

    return await plataforma_service.operador_activo(session, usuario_id)


async def usuario_de_operador(session, email: str, sub) -> "str | None":
    """El `usuario_id` del operador activo con esa identidad verificada, o None (OPE-01 R2)."""
    from features.plataforma import plataforma_service

    return await plataforma_service.usuario_de_operador(session, email, sub)


async def listar_operadores_activos(session) -> list[dict]:
    """Operadores activos con `usuario_id`, `nombre`, `email` y `ha_entrado` (OPE-01)."""
    from features.plataforma import plataforma_service

    return await plataforma_service.listar_operadores_activos(session)
# === fin OPE-01 ===
