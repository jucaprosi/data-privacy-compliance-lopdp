# ¤adpa
"""Capacidades de la sala RAT para otras salas."""
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class ActividadResumen:
    id: str
    codigo: str
    nombre: str
    datos_sensibles: bool
    es_gran_escala: bool
    requiere_eipd: bool


async def listar_actividades_resumen(session: AsyncSession, tenant_id: str) -> list[ActividadResumen]:
    from features.rat import rat_service

    return [
        ActividadResumen(
            id=a.id,
            codigo=a.codigo,
            nombre=a.nombre,
            datos_sensibles=a.datos_sensibles,
            es_gran_escala=a.es_gran_escala,
            requiere_eipd=a.requiere_eipd,
        )
        for a in await rat_service.listar_actividades_rat(session, tenant_id)
    ]


# === ADPA-06 ===
# ¤adpa Sección reservada del andamiaje ADPA-06 en este pasillo.
# === fin ADPA-06 ===

# === DLP-01 ===
async def agregar_categorias_datos(
    session: AsyncSession, tenant_id: str, rat_id: str, categorias: list[str], user_id: str | None
) -> str | None:
    """Agrega categorías de datos confirmadas a una actividad (sin duplicar). Devuelve su nombre o None."""
    from features.rat import rat_service

    actividad = await rat_service.obtener_actividad_rat(session, tenant_id, rat_id)
    if actividad is None:
        return None
    nuevas = [c for c in categorias if c not in actividad.categorias_datos]
    if nuevas:
        await rat_service.editar_actividad_rat(
            session, tenant_id, rat_id, {"categorias_datos": [*actividad.categorias_datos, *nuevas]}, user_id
        )
    return actividad.nombre
# === fin DLP-01 ===

# === MTGE-03 ===
# Sección reservada para MTGE-03.
# === fin MTGE-03 ===

# === CON-01 ===
async def existe_actividad(session: AsyncSession, tenant_id: str, actividad_id: str) -> bool:
    """True si la actividad existe en el RAT del inquilino (R1 de CON-01)."""
    from features.rat import rat_service

    return await rat_service.obtener_actividad_rat(session, tenant_id, actividad_id) is not None
# === fin CON-01 ===

# === CCTV-01 ===
# Videovigilancia vincula sus cámaras con `existe_actividad` (definida arriba en CON-01).
# === fin CCTV-01 ===
