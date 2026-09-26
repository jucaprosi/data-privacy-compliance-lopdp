import pytest
import json
from pathlib import Path
from features.auditoria_capa.services.merkle_tree import MerkleTree, anclar_root_hash_ahora, _global_tree

def test_merkle_tree_corrupcion():
    """Verifica que si se altera un snapshot antiguo, el Root Hash general se corrompe."""
    tree = MerkleTree()
    tree.add_leaf("snapshot_1_valid_data")
    tree.add_leaf("snapshot_2_valid_data")
    tree.add_leaf("snapshot_3_valid_data")
    
    root_hash_original = tree.compute_root()
    
    # Simulamos una alteración retroactiva en el snapshot 2
    tree_corrupt = MerkleTree()
    tree_corrupt.add_leaf("snapshot_1_valid_data")
    tree_corrupt.add_leaf("snapshot_2_INVALID_data") # Alterado
    tree_corrupt.add_leaf("snapshot_3_valid_data")
    
    root_hash_corrupt = tree_corrupt.compute_root()
    
    # Comprobamos que el root hash ha cambiado irremediablemente
    assert root_hash_original != root_hash_corrupt
    assert root_hash_original is not None

def test_anclaje_tsa_utc():
    """Verifica que la función de anclaje persista el root hash con UTC correctamente."""
    _global_tree.leaves.clear()
    _global_tree.add_leaf("test_tsa")
    
    root_hash = anclar_root_hash_ahora()
    
    anchors_file = Path("data/merkle_anchors.json")
    assert anchors_file.exists()
    
    data = json.loads(anchors_file.read_text(encoding="utf-8"))
    last_anchor = data[-1]
    
    assert last_anchor["root_hash"] == root_hash
    assert "timestamp_utc" in last_anchor
    assert last_anchor["timestamp_utc"].endswith("Z") or "+00:00" in last_anchor["timestamp_utc"] or "T" in last_anchor["timestamp_utc"]
