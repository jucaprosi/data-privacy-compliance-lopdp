# ¤adpa ¤arbitro
"""ADPA-12: pruebas y mutaciones del cargador modular de compuerta y pasillo (sala roadmap).

Mutaciones documentadas:
- M1: submódulo sin __all__ o con __all__ vacío -> ValueError.
- M2: colisión accidental de símbolos entre dos fichas sin REEMPLAZA -> ValueError.
- M3: reemplazo explícito con REEMPLAZA -> se aplica correctamente.
- M4: linter AST: ningún archivo en app_core/pasillo/roadmap_fichas/ puede importar features en top-level.
"""
from __future__ import annotations

import ast
from pathlib import Path
from types import ModuleType
import pytest

from features.roadmap.roadmap_service import cargar_extensiones_compuerta
from app_core.pasillo.roadmap import _cargar_fichas_pasillo

RAIZ = Path(__file__).resolve().parent.parent


def test_carga_nominal_submodulos(tmp_path: Path):
    """Carga en orden determinista y exporta símbolos a globals y __all__."""
    sub_a = ModuleType("compuerta_a")
    sub_a.__all__ = ["funcion_a"]
    sub_a.funcion_a = lambda: "A"

    sub_b = ModuleType("compuerta_b")
    sub_b.__all__ = ["funcion_b"]
    sub_b.funcion_b = lambda: "B"

    modulos = {
        "features.roadmap.compuerta.compuerta_a": sub_a,
        "features.roadmap.compuerta.compuerta_b": sub_b,
    }

    (tmp_path / "compuerta_a.py").write_text("# a", encoding="utf-8")
    (tmp_path / "compuerta_b.py").write_text("# b", encoding="utf-8")

    espacio: dict[str, object] = {}
    publicos: list[str] = []

    cargados = cargar_extensiones_compuerta(
        "features.roadmap.compuerta",
        tmp_path,
        espacio,
        publicos,
        importar=lambda name: modulos[name],
    )

    assert cargados == ["compuerta_a", "compuerta_b"]
    assert "funcion_a" in espacio and "funcion_b" in espacio
    assert publicos == ["funcion_a", "funcion_b"]
    assert espacio["funcion_a"]() == "A"
    assert espacio["funcion_b"]() == "B"


def test_mutacion_sin_all_falla(tmp_path: Path):
    """M1: módulo sin __all__ o con __all__ vacío detiene la carga con ValueError."""
    sub_invalido = ModuleType("sin_all")
    (tmp_path / "sin_all.py").write_text("# err", encoding="utf-8")

    with pytest.raises(ValueError, match="debe declarar __all__ no vacío"):
        cargar_extensiones_compuerta(
            "features.roadmap.compuerta",
            tmp_path,
            {},
            [],
            importar=lambda _: sub_invalido,
        )

    sub_vacio = ModuleType("all_vacio")
    sub_vacio.__all__ = []
    with pytest.raises(ValueError, match="debe declarar __all__ no vacío"):
        cargar_extensiones_compuerta(
            "features.roadmap.compuerta",
            tmp_path,
            {},
            [],
            importar=lambda _: sub_vacio,
        )


def test_mutacion_colision_accidental_falla(tmp_path: Path):
    """M2: colisión de símbolo sin declarar REEMPLAZA lanza ValueError."""
    (tmp_path / "mod_a.py").write_text("# a", encoding="utf-8")

    mod = ModuleType("mod_a")
    mod.__all__ = ["simbolo_existente"]
    mod.simbolo_existente = lambda: "nuevo"

    espacio = {"simbolo_existente": lambda: "original"}

    with pytest.raises(ValueError, match="ya existe y mod_a no lo declara en REEMPLAZA"):
        cargar_extensiones_compuerta(
            "features.roadmap.compuerta",
            tmp_path,
            espacio,
            ["simbolo_existente"],
            importar=lambda _: mod,
        )


def test_reemplazo_explicito_valido(tmp_path: Path):
    """M3: una ficha que declara REEMPLAZA sustituye el símbolo y puede envolverlo."""
    (tmp_path / "mod_b.py").write_text("# b", encoding="utf-8")

    original = lambda: "original"
    espacio = {"fn": original}

    mod = ModuleType("mod_b")
    mod.__all__ = ["fn"]
    mod.REEMPLAZA = ("fn",)
    mod.fn = lambda: f"envuelto({original()})"

    publicos = ["fn"]
    cargados = cargar_extensiones_compuerta(
        "features.roadmap.compuerta",
        tmp_path,
        espacio,
        publicos,
        importar=lambda _: mod,
    )

    assert cargados == ["mod_b"]
    assert espacio["fn"]() == "envuelto(original)"
    assert publicos == ["fn"]


def test_pasillo_cero_imports_top_level_features():
    """M4: ningún módulo de app_core/pasillo/roadmap_fichas/ puede importar features en top-level."""
    carpeta_fichas = RAIZ / "app_core" / "pasillo" / "roadmap_fichas"
    if not carpeta_fichas.is_dir():
        return
    for py_file in carpeta_fichas.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        arbol = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for nodo in arbol.body:
            if isinstance(nodo, ast.ImportFrom):
                assert not (nodo.module or "").startswith("features"), (
                    f"{py_file.name}: import top-level prohibido desde features ({nodo.module})"
                )
            elif isinstance(nodo, ast.Import):
                assert not any(a.name.startswith("features") for a in nodo.names), (
                    f"{py_file.name}: import top-level prohibido de features"
                )
