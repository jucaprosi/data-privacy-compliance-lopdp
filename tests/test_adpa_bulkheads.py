"""Test de verificación arquitectónica de Mamparos Estancos ADPA.
Invariante: INV_ADPA_BULKHEAD_ISOLATION (Imports cruzados entre salas directos == 0).
"""
import os
import ast
import pytest

FEATURES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "features")

SALAS_ESPERADAS = [
    "diagnostico",
    "rat",
    "riesgos_mtge",
    "dpo_cockpit",
    "auditoria_capa",
    "evidencias",
    "regulacion_rag",
]

def test_salas_tienen_compuerta_service():
    """Toda sala ADPA debe exponer su compuerta pública <sala>_service.py."""
    for sala in SALAS_ESPERADAS:
        sala_path = os.path.join(FEATURES_DIR, sala)
        assert os.path.isdir(sala_path), f"La sala {sala} no existe en features/"
        
        compuerta = os.path.join(sala_path, f"{sala}_service.py")
        assert os.path.isfile(compuerta), f"La sala {sala} carece de compuerta pública {sala}_service.py"

def test_cero_imports_cruzados_internos_entre_salas():
    """Ninguna sala puede importar archivos internos de una sala hermana directamente."""
    violaciones = []
    
    for root, _, files in os.walk(FEATURES_DIR):
        for file in files:
            if not file.endswith(".py"):
                continue
            
            filepath = os.path.join(root, file)
            # Determinar la sala actual
            rel_path = os.path.relpath(filepath, FEATURES_DIR)
            partes = rel_path.split(os.sep)
            if len(partes) < 2:
                continue
            sala_actual = partes[0]
            
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=filepath)
                
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    mod_partes = node.module.split(".")
                    if mod_partes[0] == "features" and len(mod_partes) > 1:
                        sala_importada = mod_partes[1]
                        # Si importa de otra sala
                        if sala_importada != sala_actual and sala_importada in SALAS_ESPERADAS:
                            # Solo se permite importar de la compuerta pública <sala>_service
                            if len(mod_partes) > 2:
                                violaciones.append(
                                    f"Violación ADPA en {rel_path}: importa módulo interno '{node.module}' de sala '{sala_importada}' en lugar de usar su compuerta {sala_importada}_service.py"
                                )

    assert len(violaciones) == 0, f"Se detectaron violaciones de mamparos ADPA:\n" + "\n".join(violaciones)
