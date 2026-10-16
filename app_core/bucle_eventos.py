"""Configuración del bucle de eventos compatible con psycopg en Windows.
`¤arbitro` `¤seguridad`

En Windows, psycopg asíncrono requiere SelectorEventLoop en lugar de ProactorEventLoop.
Esta función es idempotente: fija WindowsSelectorEventLoopPolicy solo en win32 y
no altera el comportamiento en otras plataformas (Linux, macOS, Vercel, CI).
"""
import asyncio
import sys


def configurar_bucle_eventos(plataforma: str | None = None) -> bool:
    """Fija WindowsSelectorEventLoopPolicy si la plataforma es win32.

    Parámetros:
        plataforma: Permite inyectar la plataforma objetivo para pruebas.
                    Si es None, se utiliza sys.platform.

    Retorna:
        True si se configuró la política WindowsSelectorEventLoopPolicy,
        False si la plataforma no es win32 o si ya estaba fijada.
    """
    target_platform = sys.platform if plataforma is None else plataforma

    if target_platform == "win32":
        policy_cls = getattr(asyncio, "WindowsSelectorEventLoopPolicy", None)
        if policy_cls is not None:
            current_policy = asyncio.get_event_loop_policy()
            if not isinstance(current_policy, policy_cls):
                asyncio.set_event_loop_policy(policy_cls())
                return True
            return False
    return False
