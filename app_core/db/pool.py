"""GCP-05 · Tamaño del pool de conexiones del motor, leído del entorno.

`¤cloud-run-perf`: presupuesto `maxScale × (pool_size + max_overflow) <= conexiones de la base`
(governance/operaciones/presupuesto_conexiones.yaml). El backend fija `DB_POOL_SIZE` y `DB_MAX_OVERFLOW`
en governance/operaciones/cloudrun_service.yaml.

Sin variables valen los defectos de SQLAlchemy, documentados en governance/operaciones/PRUEBA_DE_CARGA.md:
pool 5 y desborde 10. Un valor presente pero inválido (no entero, fuera de rango) lanza `RuntimeError`
nombrando la variable; nunca vuelve en silencio al defecto.
"""
from __future__ import annotations

import os

POOL_POR_DEFECTO = 5
DESBORDE_POR_DEFECTO = 10
TIEMPO_ESPERA_POR_DEFECTO = 30


def _entero(entorno, nombre: str, minimo: int, maximo: int, defecto: int) -> int:
    crudo = entorno.get(nombre)
    if crudo is None:
        return defecto
    try:
        valor = int(str(crudo).strip())
    except ValueError:
        raise RuntimeError(f"{nombre} debe ser un entero; no lo es") from None
    if not minimo <= valor <= maximo:
        raise RuntimeError(f"{nombre} debe estar entre {minimo} y {maximo}; vale {valor}")
    return valor


def opciones_pool(entorno=None) -> dict:
    """Argumentos de pool para `create_async_engine`."""
    entorno = os.environ if entorno is None else entorno
    return {
        "pool_size": _entero(entorno, "DB_POOL_SIZE", 1, 20, POOL_POR_DEFECTO),
        "max_overflow": _entero(entorno, "DB_MAX_OVERFLOW", 0, 20, DESBORDE_POR_DEFECTO),
        "pool_timeout": TIEMPO_ESPERA_POR_DEFECTO,
    }
