"""Servicio de Auditoría para generación de Checklists basados en Snapshots Normativos."""
from dataclasses import dataclass
from typing import List
from features.auditoria_capa.services.merkle_tree import registrar_snapshot_merkle
import json


@dataclass(frozen=True)
class ControlAuditoria:
    """Representa un control dentro del checklist, inmutable por snapshot normativo."""
    id: str
    tenant_id: str
    snapshot_normativo: str
    descripcion: str

def generar_checklist_anual(tenant_id: str, version_normativa: str) -> List[ControlAuditoria]:
    """
    Genera un checklist de auditoría anual con un snapshot normativo inmutable.
    """
    checklist = [
        ControlAuditoria(
            id=f"CTRL-{i:03d}",
            tenant_id=tenant_id,
            snapshot_normativo=version_normativa,
            descripcion=f"Descripción del control {i} basado en versión {version_normativa}"
        )
        for i in range(1, 4)
    ]
    
    # Serializar el snapshot para registrarlo en el árbol de Merkle
    snapshot_data = json.dumps([{"id": c.id, "snap": c.snapshot_normativo} for c in checklist], sort_keys=True)
    registrar_snapshot_merkle(snapshot_data)
    
    return checklist
