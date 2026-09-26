"""Lógica de negocio e independencia del DPD/DPO (Invariante INV_LOPDP_DPO_INDEPENDENCE)."""
from typing import List
from features.dpo_cockpit.domain.models import DictamenDPO
from features.dpo_cockpit.services.bitacora_service import bitacora_inmutable

def emitir_dictamen_consultivo(dictamen: DictamenDPO) -> DictamenDPO:
    """Emite un dictamen técnico no vinculante garantizando la trazabilidad de la diligencia del DPO."""
    dictamen.es_vinculante = False
    return bitacora_inmutable.registrar_dictamen(dictamen)

def obtener_bitacora_tenant(tenant_id: str) -> List[DictamenDPO]:
    return bitacora_inmutable.listar_por_tenant(tenant_id)

def registrar_acuse_gerencial(dictamen_id: str) -> DictamenDPO:
    return bitacora_inmutable.acusar_recibo(dictamen_id)