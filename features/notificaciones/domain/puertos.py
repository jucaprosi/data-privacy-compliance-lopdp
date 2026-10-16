# -*- coding: utf-8 -*-
# ¤adpa
# ¤roadmap
"""Puerto e interfaces de dominio para notificaciones (sala ADPA: Notificaciones)."""
from __future__ import annotations

from typing import Protocol, Sequence
from features.notificaciones.domain.models import (
    CorreoLoteNotificacion,
    ResultadoDespacho,
)


class Notificador(Protocol):
    """Puerto formal (interfaz abstracta) para proveedores de notificación."""

    async def enviar_correo(
        self, correo: CorreoLoteNotificacion
    ) -> ResultadoDespacho:
        """Despacha un correo agrupado hacia el proveedor."""
        ...
