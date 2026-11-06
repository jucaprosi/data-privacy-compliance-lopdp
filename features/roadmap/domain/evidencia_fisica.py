# ¤roadmap ¤evidencias
"""Interruptor de la evidencia física del servidor (FE-26).

El PMV no guarda evidencias: el DPO declara su nivel en el diagnóstico (DIAG-13) y la hoja de ruta
no sube archivos a R2. Solo EVYDENTIA enciende la custodia física (`EVIDENCIA_FISICA=true`, con
EVI-01 y EVI-02). `EVIDENCIA_FISICA` se lee únicamente en `evidencia_fisica_activa`.

Valores: «true» enciende; «false» o la variable ausente o vacía apagan (por omisión, el PMV);
cualquier otro valor es un error de configuración explícito, y hace fallar el arranque: este módulo
lo comprueba al importarse.
"""
from __future__ import annotations

import os

VARIABLE_EVIDENCIA_FISICA = "EVIDENCIA_FISICA"
_ENCENDIDA = "true"
_APAGADA = "false"


class EvidenciaFisicaDesconocida(RuntimeError):
    """`EVIDENCIA_FISICA` trae un valor que no es «true» ni «false»."""


def evidencia_fisica_activa() -> bool:
    """Única lectura del interruptor: apagado si no está fijado; otro valor no se tolera."""
    valor = os.environ.get(VARIABLE_EVIDENCIA_FISICA, "").strip().lower() or _APAGADA
    if valor not in (_ENCENDIDA, _APAGADA):
        raise EvidenciaFisicaDesconocida(
            f"{VARIABLE_EVIDENCIA_FISICA} solo admite «true» o «false»; llegó «{valor}»"
        )
    return valor == _ENCENDIDA


evidencia_fisica_activa()  # falla el arranque con un valor desconocido
