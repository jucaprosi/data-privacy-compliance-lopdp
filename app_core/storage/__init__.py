# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""Puerto y adaptador de almacenamiento de objetos en Google Cloud Storage (EVI-01 / RET-02)."""
from app_core.storage import gcs, limites
from app_core.storage.gcs import (
    Almacen,
    AlmacenGcs,
    AlmacenNoDisponible,
    FirmaSubida,
    ObjetoDemasiadoGrande,
    ObjetoYaExiste,
    almacen_por_defecto,
)

__all__ = [
    "Almacen",
    "AlmacenGcs",
    "AlmacenNoDisponible",
    "FirmaSubida",
    "ObjetoDemasiadoGrande",
    "ObjetoYaExiste",
    "almacen_por_defecto",
    "gcs",
    "limites",
]
