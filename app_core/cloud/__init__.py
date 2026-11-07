"""Chasis de ejecución en Google Cloud (GCP-01). `¤cloud-run-perf`

Importar este paquete no abre conexiones ni crea clientes de Google Cloud:
todo se inicializa al primer uso.
"""

from app_core.cloud.gcp_runtime import (
    argumentos_motor,
    cliente_gcp,
    es_pooler_transaccional,
    leer_secreto,
    telemetria_cloudrun,
)

__all__ = [
    "argumentos_motor",
    "cliente_gcp",
    "es_pooler_transaccional",
    "leer_secreto",
    "telemetria_cloudrun",
]
