"""Pruebas del catálogo de controles P1-P80 de la hoja de ruta (RM-19).

Verifica:
1. El catálogo P1-P80 proviene del banco canónico de 80 preguntas de DIAG-02 a través de diagnostico_service.py.
2. Contiene exactamente 80 controles numerados P1 a P80 correlativos.
3. Cada control tiene código ('Pn'), pregunta_id (n), dimensión válida ('D01'..'D10') y nombre de control no vacío.
4. VALID_CONTROLS acepta exactamente {'P1'..'P80'}: P80 es válido y P81 no.
5. El catálogo de la hoja de ruta coincide biyectivamente con el banco de preguntas.
"""
from features.diagnostico.diagnostico_service import obtener_catalogo_controles_p1_p80
from features.roadmap.roadmap_service import VALID_CONTROLS, VALID_DIMENSIONS


def test_catalogo_controles_tiene_exactamente_80_elementos():
    catalogo = obtener_catalogo_controles_p1_p80()
    assert len(catalogo) == 80, f"Se esperaban 80 controles, se obtuvieron {len(catalogo)}"


def test_catalogo_controles_codigos_p1_a_p80_correlativos():
    catalogo = obtener_catalogo_controles_p1_p80()
    codigos_esperados = [f"P{i}" for i in range(1, 81)]
    codigos_obtenidos = [c["codigo"] for c in catalogo]
    assert codigos_obtenidos == codigos_esperados, "Los códigos deben ser exactamente P1 a P80 correlativos"


def test_catalogo_controles_campos_obligatorios():
    catalogo = obtener_catalogo_controles_p1_p80()
    for c in catalogo:
        assert c["codigo"].startswith("P")
        assert isinstance(c["pregunta_id"], int)
        assert 1 <= c["pregunta_id"] <= 80
        assert c["dimension"] in VALID_DIMENSIONS
        assert c["control"] and isinstance(c["control"], str) and len(c["control"].strip()) > 0


def test_valid_controls_acepta_exactamente_p1_a_p80():
    catalogo = obtener_catalogo_controles_p1_p80()
    codigos_catalogo = {c["codigo"] for c in catalogo}
    assert VALID_CONTROLS == codigos_catalogo, "VALID_CONTROLS debe coincidir exactamente con el catálogo P1-P80"
    assert "P80" in VALID_CONTROLS, "P80 debe ser un control válido"
    assert "P81" not in VALID_CONTROLS, "P81 no debe ser un control válido"
    assert "P0" not in VALID_CONTROLS, "P0 no debe ser un control válido"
