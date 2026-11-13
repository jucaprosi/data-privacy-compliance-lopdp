# ¤rbac-tenant ¤arbitro
"""Las secciones de tests/matriz/roles/auditor.py no declaran la misma clave dos veces."""
from pathlib import Path

import pytest

RUTA = Path(__file__).parent / "matriz" / "roles" / "auditor.py"


def _cargar(texto: str):
    espacio: dict = {}
    exec(compile(texto, str(RUTA), "exec"), espacio)
    return espacio


def test_carga_sin_duplicados():
    espacio = _cargar(RUTA.read_text(encoding="utf-8"))
    assert espacio["PERMITIDO"], "PERMITIDO vacío"
    assert set(espacio["_DUENO"]) == set(espacio["PERMITIDO"])


def test_clave_duplicada_rompe_la_carga():
    # Mutación: repetir en una sección una clave que ya es de ORG-22.
    texto = RUTA.read_text(encoding="utf-8") + "\n_seccion('PRUEBA', {'ver_assessment': True})\n"
    with pytest.raises(ValueError, match="ver_assessment"):
        _cargar(texto)
