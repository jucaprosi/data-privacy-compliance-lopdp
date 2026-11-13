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


# === ADPA-06 ===
# ¤adpa Sección reservada del andamiaje ADPA-06 en este pasillo.
# === fin ADPA-06 ===

# === DIAG-04 ===
# Sección reservada para DIAG-04.
# === fin DIAG-04 ===

# === DEMO-03e ===
# ¤demo Copia y siembra de la sala para la demo «Cooperativa Demo»; la lógica vive en el motor de la sala.
async def clonar_desde_plantilla(session, origen: str, destino: str, mapa_ids: dict) -> dict:
    from features.evidencias import evidencias_service

    return await evidencias_service.clonar_desde_plantilla(session, origen, destino, mapa_ids)


async def sembrar_en_plantilla(session, plantilla_id: str, datos: dict) -> None:
    from features.evidencias import evidencias_service

    await evidencias_service.sembrar_en_plantilla(session, plantilla_id, datos)
# === fin DEMO-03e ===


# === CAPA-04 ===
# Sección reservada para CAPA-04.
# === fin CAPA-04 ===


# === FOR-01 ===
# Sección reservada para FOR-01.
# === fin FOR-01 ===


# === EVI-04 ===
# Sección reservada para EVI-04.
# === fin EVI-04 ===

# === MTGE-03 ===
# Sección reservada para MTGE-03.
# === fin MTGE-03 ===
