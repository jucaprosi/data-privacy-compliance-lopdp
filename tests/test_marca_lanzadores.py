"""MARCA-05 · Los lanzadores de Windows usan solo el nombre EVYDENTIA.

`¤observabilidad` `¤arbitro`
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LANZADORES = ("iniciar_backend.bat", "iniciar_frontend.bat", "iniciar_todo.bat")


def _sin_nombre_viejo(texto: str) -> bool:
    return "JUBYS" not in texto.upper()


def test_los_lanzadores_dicen_evydentia():
    for nombre in LANZADORES:
        texto = (RAIZ / nombre).read_text(encoding="utf-8")
        assert _sin_nombre_viejo(texto), f"{nombre} conserva el nombre anterior"
        assert "EVYDENTIA" in texto, f"{nombre} no nombra EVYDENTIA"


def test_la_guarda_detecta_el_nombre_viejo():
    """Mutación en miniatura: si el nombre anterior vuelve a un .bat, la comprobación falla."""
    assert _sin_nombre_viejo("title EVYDENTIA Plataforma") is True
    assert _sin_nombre_viejo("title JUBYS Plataforma") is False
    assert _sin_nombre_viejo("title Jubys Plataforma") is False
