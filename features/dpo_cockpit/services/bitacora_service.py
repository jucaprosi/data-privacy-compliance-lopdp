"""Servicio de Bitácora Inmutable (Append-Only) con Hashing Criptográfico Chained SHA-256."""
import hashlib
import json
from typing import Dict, List, Optional
from datetime import datetime, timezone
from features.dpo_cockpit.domain.models import DictamenDPO

class BitacoraInmutableService:
    def __init__(self):
        self._store: Dict[str, DictamenDPO] = {}
        self._chain: List[str] = []
        self._hashes: Dict[str, str] = {}
        
    def _calcular_hash(self, dictamen: DictamenDPO, prev_hash: str) -> str:
        payload = {
            "id": dictamen.id,
            "tenant_id": dictamen.tenant_id,
            "dpo_id": dictamen.dpo_id,
            "tipo": dictamen.tipo.value,
            "fecha_emision": dictamen.fecha_emision.isoformat(),
            "prev_hash": prev_hash
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def registrar_dictamen(self, dictamen: DictamenDPO) -> DictamenDPO:
        if dictamen.id in self._store:
            raise PermissionError("Violación de integridad: La bitácora del DPD/DPO es inalterable (Append-Only).")
            
        prev_hash = self._hashes[self._chain[-1]] if self._chain else "0" * 64
        current_hash = self._calcular_hash(dictamen, prev_hash)
        
        # Guardar en memoria (simulando BD inmutable)
        self._store[dictamen.id] = dictamen
        self._chain.append(dictamen.id)
        self._hashes[dictamen.id] = current_hash
        
        return dictamen

    def listar_por_tenant(self, tenant_id: str) -> List[DictamenDPO]:
        return [self._store[did] for did in self._chain if self._store[did].tenant_id == tenant_id]

    def acusar_recibo(self, dictamen_id: str) -> DictamenDPO:
        if dictamen_id not in self._store:
            raise KeyError(f"Dictamen {dictamen_id} no encontrado")
        doc = self._store[dictamen_id]
        doc.acuse_recibo_alta_direccion = True
        doc.fecha_acuse = datetime.now(timezone.utc)
        return doc

    def verificar_integridad(self) -> bool:
        """Verifica que la cadena de hashes no haya sido alterada."""
        prev_hash = "0" * 64
        for did in self._chain:
            dictamen = self._store[did]
            expected_hash = self._calcular_hash(dictamen, prev_hash)
            if self._hashes[did] != expected_hash:
                return False
            prev_hash = expected_hash
        return True

# Singleton instance para propósitos de prueba
bitacora_inmutable = BitacoraInmutableService()