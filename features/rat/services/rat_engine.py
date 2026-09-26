"""Lógica de negocio e integridad del RAT como Master Record (Compliance Graph)."""
from typing import Dict, List, Optional
from features.rat.domain.models import ActividadRAT, BaseLegitimacion, CategoriaTitular

class InMemoryRATRepository:
    def __init__(self):
        self._store: Dict[str, ActividadRAT] = {}

    def guardar(self, actividad: ActividadRAT) -> ActividadRAT:
        self._store[actividad.id] = actividad
        return actividad

    def obtener_por_id(self, actividad_id: str) -> Optional[ActividadRAT]:
        return self._store.get(actividad_id)

    def listar_por_tenant(self, tenant_id: str) -> List[ActividadRAT]:
        return [a for a in self._store.values() if a.tenant_id == tenant_id]

repo_rat = InMemoryRATRepository()

def crear_o_actualizar_actividad(actividad: ActividadRAT) -> ActividadRAT:
    """Registra o versiona una actividad del RAT asegurando el Single Source of Truth."""
    # Validación de reglas básicas
    if not actividad.codigo:
        actividad.codigo = f"RAT-{len(repo_rat.listar_por_tenant(actividad.tenant_id)) + 1:03d}"
    
    # Si trata datos de salud o pacientes, activa bandera sensible
    if CategoriaTitular.PACIENTES in actividad.categorias_titulares:
        actividad.datos_sensibles = True

    return repo_rat.guardar(actividad)

def obtener_actividades_tenant(tenant_id: str) -> List[ActividadRAT]:
    return repo_rat.listar_por_tenant(tenant_id)

def eliminar_actividad(rat_id: str) -> None:
    if rat_id in repo_rat._store:
        del repo_rat._store[rat_id]
