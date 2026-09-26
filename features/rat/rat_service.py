"""Compuerta pública de la sala ADPA: RAT Maestro."""
from typing import List, Optional
from features.rat.domain.models import ActividadRAT, BaseLegitimacion, CategoriaTitular
from features.rat.services.rat_engine import crear_o_actualizar_actividad, obtener_actividades_tenant

def registrar_actividad_rat(actividad: ActividadRAT) -> ActividadRAT:
    """Registra una actividad de tratamiento en el RAT maestro."""
    return crear_o_actualizar_actividad(actividad)

def listar_actividades_rat(tenant_id: str) -> List[ActividadRAT]:
    """Obtiene el inventario completo de actividades del RAT para un tenant."""
    return obtener_actividades_tenant(tenant_id)

from features.rat.services.rat_engine import eliminar_actividad

def eliminar_actividad_rat(rat_id: str) -> None:
    """Elimina una actividad del RAT."""
    eliminar_actividad(rat_id)
