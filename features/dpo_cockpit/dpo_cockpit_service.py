"""Compuerta pública de la sala ADPA: Cockpit del DPD/DPO."""
from typing import List
from features.dpo_cockpit.domain.models import DictamenDPO, TipoDictamenDPO
from features.dpo_cockpit.services.dpo_engine import (
    emitir_dictamen_consultivo,
    obtener_bitacora_tenant,
    registrar_acuse_gerencial,
)

def emitir_dictamen_dpo(dictamen: DictamenDPO) -> DictamenDPO:
    """Emite un dictamen técnico-consultivo y lo asienta en la bitácora de diligencia."""
    return emitir_dictamen_consultivo(dictamen)

def consultar_bitacora_dpo(tenant_id: str) -> List[DictamenDPO]:
    """Recupera el historial de dictámenes y advertencias del DPO para el tenant."""
    return obtener_bitacora_tenant(tenant_id)

def firmar_acuse_recibo_dictamen(dictamen_id: str) -> DictamenDPO:
    """Registra la constancia de que la gerencia recibió la recomendación del DPO."""
    return registrar_acuse_gerencial(dictamen_id)
