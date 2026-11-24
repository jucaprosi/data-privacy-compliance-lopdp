# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤vigilancia-spdp ¤inteligencia-normativa ¤seguridad
"""Punto de entrada del Cloud Run Job `evydentia-monitoreo-normativo` (NORM-04).

    python -m features.inteligencia_normativa.trabajo_monitoreo

Cloud Scheduler lanza el Job a las 05:00 de Guayaquil con la cuenta `sa-evydentia-normativa`. Sale con 0 si la
corrida queda `ok` o `parcial` y con 1 si queda `fallida` o algo inesperado la corta, para que el Job registre el
fallo. No imprime la URL de la base, secretos ni el detalle de ninguna excepción.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable

from sqlalchemy import text

ORIGEN = "programado"  # cabe en `origen varchar(20)`
VENTANA_CORRIDA_EN_CURSO = timedelta(minutes=30)


async def _hay_corrida_en_curso(sesion_factory: Callable[[], Any] | None = None) -> bool:
    """R4: una corrida sin `fin`, abierta hace menos de 30 minutos, sigue viva; no se abre otra."""
    from features.inteligencia_normativa.services import monitoreo

    fabrica = sesion_factory or monitoreo._sesion_por_defecto
    limite = datetime.now(timezone.utc) - VENTANA_CORRIDA_EN_CURSO
    async with fabrica() as sesion:
        await monitoreo._como_normativa(sesion)
        fila = (await sesion.execute(
            text("SELECT 1 FROM normativa_monitoreo_logs WHERE fin IS NULL AND inicio > :limite LIMIT 1"),
            {"limite": limite},
        )).first()
    return fila is not None


async def correr(
    *,
    disparar: Callable[[str], Awaitable[Any]] | None = None,
    en_curso: Callable[[], Awaitable[bool]] | None = None,
    sesion_factory: Callable[[], Any] | None = None,
    salida: Callable[[str], None] = print,
) -> int:
    """Una pasada del Job. Devuelve el código de salida del proceso."""
    try:
        hay_otra = await (en_curso() if en_curso else _hay_corrida_en_curso(sesion_factory))
        if hay_otra:
            salida("monitoreo normativo: hay una corrida en curso; no se abre otra")
            return 0
        if disparar is None:
            from features.inteligencia_normativa import inteligencia_normativa_service as svc

            disparar = svc.disparar_monitoreo
        resumen = await disparar(ORIGEN)
    except Exception as exc:  # el detalle puede traer la URL de la base: solo el tipo
        salida(f"monitoreo normativo: error inesperado ({type(exc).__name__})")
        return 1
    salida(
        f"monitoreo normativo: corrida {resumen.id} {resumen.estado}; vistos={resumen.documentos_vistos} "
        f"nuevos={resumen.nuevos} versiones={resumen.versiones_nuevas} errores={resumen.errores} "
        f"codigos={','.join(resumen.codigos_error) or '-'}"
    )
    return 1 if resumen.estado == "fallida" else 0


def main() -> int:
    return asyncio.run(correr())


if __name__ == "__main__":
    raise SystemExit(main())
