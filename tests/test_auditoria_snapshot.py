"""Test de generación de Checklists de Auditoría basados en Snapshots Normativos."""
from features.auditoria_capa.services.auditoria_service import generar_checklist_anual

def test_auditoria_snapshot_inmutabilidad():
    """
    Verifica que un checklist generado con version_normativa='2021' 
    no se vea afectado si otra parte del sistema invoca el corpus legal '2026'.
    """
    tenant_id = "tenant-123"
    
    # Generamos checklist con corpus legal 2021
    checklist_2021 = generar_checklist_anual(tenant_id, version_normativa="2021")
    
    # Simulamos que el sistema (u otro tenant) invoca el corpus 2026
    checklist_2026 = generar_checklist_anual(tenant_id, version_normativa="2026")
    
    # Validamos inmutabilidad: el checklist original preserva su snapshot normativo
    for control in checklist_2021:
        assert control.snapshot_normativo == "2021"
        
    for control in checklist_2026:
        assert control.snapshot_normativo == "2026"
        
    assert checklist_2021[0].snapshot_normativo != checklist_2026[0].snapshot_normativo
