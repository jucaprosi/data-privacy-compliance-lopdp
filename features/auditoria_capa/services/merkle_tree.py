import hashlib
import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import List

class MerkleTree:
    def __init__(self):
        self.leaves: List[str] = []
        
    def add_leaf(self, data: str):
        """Agrega un hash (hoja) al árbol basado en los datos proporcionados."""
        leaf_hash = hashlib.sha256(data.encode('utf-8')).hexdigest()
        self.leaves.append(leaf_hash)

    def compute_root(self) -> str:
        """Calcula el Root Hash del árbol."""
        if not self.leaves:
            return hashlib.sha256(b"").hexdigest()
        
        current_level = self.leaves[:]
        
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                if i + 1 < len(current_level):
                    right = current_level[i + 1]
                else:
                    right = left # Duplicar el último si es impar
                combined = left + right
                next_level.append(hashlib.sha256(combined.encode('utf-8')).hexdigest())
            current_level = next_level
            
        return current_level[0]

# Instancia global en memoria para simular el estado del árbol de auditoría
_global_tree = MerkleTree()

def registrar_snapshot_merkle(snapshot_data: str):
    """Registra el hash de un snapshot en el árbol de Merkle global."""
    _global_tree.add_leaf(snapshot_data)

def anclar_root_hash_ahora() -> str:
    """Calcula el Root Hash actual y lo guarda con Timestamp UTC en disco."""
    root_hash = _global_tree.compute_root()
    timestamp = datetime.now(timezone.utc).isoformat()
    
    anchor_data = {
        "timestamp_utc": timestamp,
        "root_hash": root_hash,
        "leaves_count": len(_global_tree.leaves)
    }
    
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    anchors_file = data_dir / "merkle_anchors.json"
    
    historico = []
    if anchors_file.exists():
        try:
            historico = json.loads(anchors_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
            
    historico.append(anchor_data)
    anchors_file.write_text(json.dumps(historico, indent=2), encoding="utf-8")
    return root_hash

async def anclar_root_hash_periodicamente(interval_seconds: int = 86400):
    """Tarea asíncrona que simula un anclaje TSA RFC 3161 cada 24 horas."""
    while True:
        anclar_root_hash_ahora()
        await asyncio.sleep(interval_seconds)
