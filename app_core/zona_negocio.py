# ¤adpa
# ¤¤developer-architect
"""BIB-120 · Fecha de negocio: los plazos y filtros por día son del negocio ecuatoriano.

`ZONA_NEGOCIO` usa un offset fijo de -5 h porque Ecuador no tiene horario de verano; así no depende de
tzdata (Windows, imágenes slim). `ZONA_NEGOCIO_NOMBRE` es el nombre IANA que se pasa a PostgreSQL en
`AT TIME ZONE`, que sí trae sus propias zonas.
"""
from datetime import date, datetime, timedelta, timezone

ZONA_NEGOCIO_NOMBRE = "America/Guayaquil"
ZONA_NEGOCIO = timezone(timedelta(hours=-5), ZONA_NEGOCIO_NOMBRE)


# ¤adpa
def hoy_negocio(ahora: datetime | None = None) -> date:
    """Día de negocio en Guayaquil. `ahora` permite inyectar el reloj; sin zona se toma como UTC."""
    momento = ahora or datetime.now(timezone.utc)
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento.astimezone(ZONA_NEGOCIO).date()
