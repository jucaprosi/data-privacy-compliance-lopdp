# ¤adpa
"""Capacidades de la sala Evidencias para otras salas."""
from typing import Optional


def huella_registrada(tenant_id: str, sha256: str) -> Optional[str]:
    """Devuelve la huella normalizada si es válida y existe en la organización; si no, None."""
    from features.evidencias import evidencias_service

    try:
        huella = evidencias_service.normalizar_sha256(sha256)
    except evidencias_service.HashInvalido:
        return None
    return huella if evidencias_service.verificar_hash(tenant_id, huella) is not None else None
