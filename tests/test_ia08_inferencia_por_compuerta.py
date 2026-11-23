# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤gemini-vertex ¤adpa ¤arbitro
"""IA-08: toda inferencia Gemini en Vertex AI entra por una sola compuerta y un solo cliente SDK.

Reglas de `governance/especificaciones/IA-08.md`:
  - R1 · Un solo cliente: en `features/`, `app_core/`, `api/` y `scripts/`, solo
    `features/inferencia/services/cliente_vertex.py` importa `google.genai` o construye `genai.Client`.
  - R2 · Una sola puerta: ningún módulo de `features/` (fuera de `features/inferencia/`) ni de `api/`
    importa `features.inferencia` directamente; las salas consumen `app_core.pasillo.inferencia`.

Mutaciones (cada una pone en rojo su prueba sobre `tmp_path`):
  m1. Un módulo temporal de otra sala con `from google import genai` hace fallar la aserción de cliente único.
  m2. Un módulo temporal `features/roadmap/services/puente_directo.py` con
      `from features.inferencia import inferencia_service` hace fallar la aserción de pasillo único.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterator

import pytest

RAIZ = Path(__file__).resolve().parents[1]
CLIENTE_UNICO = "features/inferencia/services/cliente_vertex.py"
DIRECTORIOS_SDK: tuple[str, ...] = ("features", "app_core", "api", "scripts")
DIRECTORIOS_PUERTA: tuple[str, ...] = ("features", "api")
SALAS_CONSUMIDORAS_ESPERADAS = frozenset({"ai_copilot", "inteligencia_normativa", "preanalisis", "roadmap"})
_CARPETAS_EXCLUIDAS = frozenset({"__pycache__", ".venv", "venv", ".git", ".pytest_cache"})


def _iterar_py(
    raiz: Path,
    carpetas: tuple[str, ...],
    *,
    excluir_prefijo: str | None = None,
) -> Iterator[tuple[Path, str]]:
    """Recorre archivos `.py` bajo `carpetas`, devolviendo `(ruta, ruta_relativa_posix)`."""
    for carpeta in carpetas:
        base = raiz / carpeta
        if not base.is_dir():
            continue
        for ruta in sorted(base.rglob("*.py")):
            rel_path = ruta.relative_to(raiz)
            if any(parte in _CARPETAS_EXCLUIDAS for parte in rel_path.parts):
                continue
            rel = rel_path.as_posix()
            if excluir_prefijo and rel.startswith(excluir_prefijo):
                continue
            yield ruta, rel


def _es_modulo_genai(nombre: str | None) -> bool:
    return nombre == "google.genai" or bool(nombre and nombre.startswith("google.genai."))


def _es_modulo_inferencia(nombre: str | None) -> bool:
    return nombre == "features.inferencia" or bool(nombre and nombre.startswith("features.inferencia."))


def _es_pasillo_inferencia(nombre: str | None) -> bool:
    return nombre == "app_core.pasillo.inferencia" or bool(nombre and nombre.startswith("app_core.pasillo.inferencia."))


def _constante_str(nodo: ast.AST) -> str | None:
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
        return nodo.value
    return None


def _objetivo_import_dinamico(nodo: ast.Call) -> tuple[str | None, set[str]]:
    """Extrae `(modulo, fromlist)` de `importlib.import_module(...)` o `__import__(...)`."""
    func = nodo.func
    nombre = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
    if nombre not in {"import_module", "__import__"}:
        return None, set()

    objetivo = _constante_str(nodo.args[0]) if nodo.args else None
    if objetivo is None:
        for kw in nodo.keywords:
            if kw.arg == "name":
                objetivo = _constante_str(kw.value)
                break
    if objetivo is None:
        return None, set()

    if nombre == "import_module":
        paquete = _constante_str(nodo.args[1]) if len(nodo.args) >= 2 else None
        if paquete is None:
            for kw in nodo.keywords:
                if kw.arg == "package":
                    paquete = _constante_str(kw.value)
                    break
        if paquete and objetivo.startswith("."):
            sufijo = objetivo.lstrip(".")
            objetivo = f"{paquete}.{sufijo}" if sufijo else paquete

    fromlist: set[str] = set()
    if nombre == "__import__":
        fl_nodo = (
            nodo.args[3]
            if len(nodo.args) >= 4
            else next((kw.value for kw in nodo.keywords if kw.arg == "fromlist"), None)
        )
        if isinstance(fl_nodo, (ast.List, ast.Tuple, ast.Set)):
            for elem in fl_nodo.elts:
                texto = _constante_str(elem)
                if texto:
                    fromlist.add(texto)

    return objetivo, fromlist


def _resolver_import_relativo(rel_posix: str, modulo: str | None, level: int) -> str | None:
    partes_paquete = list(Path(rel_posix).parts[:-1])
    subir = level - 1
    if subir > len(partes_paquete):
        return None
    base = partes_paquete[: len(partes_paquete) - subir] if subir else partes_paquete
    if modulo:
        base.extend(modulo.split("."))
    return ".".join(base) if base else None


def _es_referencia_genai(nodo: ast.AST) -> bool:
    return (isinstance(nodo, ast.Name) and nodo.id == "genai") or (
        isinstance(nodo, ast.Attribute) and nodo.attr == "genai"
    )


def _usa_genai(fuente: str, rel_posix: str) -> bool:
    """True si el AST importa `google.genai` o invoca construcción de `genai.Client`."""
    arbol = ast.parse(fuente, filename=rel_posix)
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            if any(_es_modulo_genai(alias.name) for alias in nodo.names):
                return True
        elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0:
            if _es_modulo_genai(nodo.module):
                return True
            if nodo.module == "google" and any(
                alias.name == "genai" or alias.name.startswith("genai.") for alias in nodo.names
            ):
                return True
        elif isinstance(nodo, ast.Attribute):
            if nodo.attr == "genai" and isinstance(nodo.value, ast.Name) and nodo.value.id == "google":
                return True
        elif isinstance(nodo, ast.Call):
            objetivo, fromlist = _objetivo_import_dinamico(nodo)
            if _es_modulo_genai(objetivo) or (objetivo == "google" and "genai" in fromlist):
                return True
            func = nodo.func
            if isinstance(func, ast.Attribute) and func.attr == "Client" and _es_referencia_genai(func.value):
                return True
            if getattr(func, "id", None) == "getattr" and len(nodo.args) >= 2:
                if _constante_str(nodo.args[1]) == "Client" and _es_referencia_genai(nodo.args[0]):
                    return True
    return False


def _importa_features_inferencia(fuente: str, rel_posix: str) -> bool:
    """True si el AST importa `features.inferencia` directamente."""
    arbol = ast.parse(fuente, filename=rel_posix)
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            if any(_es_modulo_inferencia(alias.name) for alias in nodo.names):
                return True
        elif isinstance(nodo, ast.ImportFrom):
            modulo = nodo.module if nodo.level == 0 else _resolver_import_relativo(rel_posix, nodo.module, nodo.level)
            if _es_modulo_inferencia(modulo):
                return True
            if modulo == "features" and any(
                alias.name == "inferencia" or alias.name.startswith("inferencia.") for alias in nodo.names
            ):
                return True
        elif isinstance(nodo, ast.Call):
            objetivo, fromlist = _objetivo_import_dinamico(nodo)
            if _es_modulo_inferencia(objetivo) or (objetivo == "features" and "inferencia" in fromlist):
                return True
    return False


def _importa_pasillo_inferencia(fuente: str, rel_posix: str) -> bool:
    """True si el AST importa `app_core.pasillo.inferencia`."""
    arbol = ast.parse(fuente, filename=rel_posix)
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            if any(_es_pasillo_inferencia(alias.name) for alias in nodo.names):
                return True
        elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0:
            if _es_pasillo_inferencia(nodo.module):
                return True
            if nodo.module == "app_core.pasillo" and any(
                alias.name == "inferencia" or alias.name.startswith("inferencia.") for alias in nodo.names
            ):
                return True
    return False


def escanear_clientes_genai(raiz: Path) -> set[str]:
    """Devuelve los módulos de `features/`, `app_core/`, `api/` y `scripts/` que usan `google.genai`."""
    return {
        rel
        for ruta, rel in _iterar_py(raiz, DIRECTORIOS_SDK)
        if _usa_genai(ruta.read_text(encoding="utf-8"), rel)
    }


def escanear_imports_directos_inferencia(raiz: Path) -> set[str]:
    """Devuelve los módulos de `features/` (salvo `features/inferencia/`) y `api/` que importan `features.inferencia`."""
    return {
        rel
        for ruta, rel in _iterar_py(raiz, DIRECTORIOS_PUERTA, excluir_prefijo="features/inferencia/")
        if _importa_features_inferencia(ruta.read_text(encoding="utf-8"), rel)
    }


def escanear_consumidores_pasillo_inferencia(raiz: Path) -> set[str]:
    """Devuelve los módulos de `features/` (salvo `features/inferencia/`) que usan `app_core.pasillo.inferencia`."""
    return {
        rel
        for ruta, rel in _iterar_py(raiz, ("features",), excluir_prefijo="features/inferencia/")
        if _importa_pasillo_inferencia(ruta.read_text(encoding="utf-8"), rel)
    }


def _escribir_modulo(raiz: Path, relativa: str, contenido: str) -> Path:
    destino = raiz / relativa
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(contenido, encoding="utf-8", newline="\n")
    return destino


def _asegurar_un_solo_cliente(raiz: Path) -> set[str]:
    hallados = escanear_clientes_genai(raiz)
    assert hallados == {CLIENTE_UNICO}, (
        f"Solo {CLIENTE_UNICO} puede importar google.genai o construir genai.Client; "
        f"encontrados: {sorted(hallados)}"
    )
    return hallados


def _asegurar_sin_imports_directos(raiz: Path) -> None:
    directos = escanear_imports_directos_inferencia(raiz)
    assert directos == set(), (
        "Ningún módulo de features/ (fuera de features/inferencia/) ni de api/ puede importar "
        f"features.inferencia directamente; encontrados: {sorted(directos)}"
    )


def test_un_solo_cliente_de_inferencia(tmp_path: Path) -> None:
    """R1 y mutación m1: solo `cliente_vertex.py` importa `google.genai` o construye `genai.Client`."""
    assert _asegurar_un_solo_cliente(RAIZ) == {CLIENTE_UNICO}

    _escribir_modulo(
        tmp_path,
        CLIENTE_UNICO,
        "def crear_cliente():\n"
        "    from google import genai\n"
        "    return genai.Client(vertexai=True, project='p', location='us-central1')\n",
    )
    _escribir_modulo(
        tmp_path,
        "app_core/storage/gcs.py",
        "from google.cloud import storage\n"
        "def crear():\n"
        "    return storage.Client()\n",
    )
    _escribir_modulo(
        tmp_path,
        "scripts/evaluar_ia.py",
        "from features.inferencia import inferencia_service as gate\n",
    )
    assert _asegurar_un_solo_cliente(tmp_path) == {CLIENTE_UNICO}

    # Mutación m1: un módulo intruso en otra sala importa `from google import genai`
    _escribir_modulo(
        tmp_path,
        "features/roadmap/services/intruso.py",
        "from google import genai\n\ncliente = genai.Client(vertexai=True)\n",
    )
    assert escanear_clientes_genai(tmp_path) == {CLIENTE_UNICO, "features/roadmap/services/intruso.py"}
    with pytest.raises(AssertionError, match=r"features/roadmap/services/intruso\.py"):
        _asegurar_un_solo_cliente(tmp_path)


def test_salas_por_el_pasillo_de_inferencia(tmp_path: Path) -> None:
    """R2 y mutación m2: las salas consumidoras entran por `app_core.pasillo.inferencia`."""
    _asegurar_sin_imports_directos(RAIZ)
    consumidores = escanear_consumidores_pasillo_inferencia(RAIZ)
    salas_consumidoras = {Path(ruta).parts[1] for ruta in consumidores}
    assert SALAS_CONSUMIDORAS_ESPERADAS <= salas_consumidoras
    assert "inferencia" not in salas_consumidoras
    assert (RAIZ / "app_core" / "pasillo" / "inferencia.py").is_file()

    _escribir_modulo(
        tmp_path,
        "features/inferencia/inferencia_service.py",
        "from features.inferencia.services import cliente_vertex\n",
    )
    _escribir_modulo(
        tmp_path,
        "app_core/pasillo/inferencia.py",
        "def estado():\n"
        "    from features.inferencia import inferencia_service\n"
        "    return inferencia_service.estado()\n",
    )
    _escribir_modulo(
        tmp_path,
        "scripts/evaluar_ia.py",
        "from features.inferencia import inferencia_service as gate\n",
    )
    _escribir_modulo(
        tmp_path,
        "features/roadmap/ai/client.py",
        "from app_core.pasillo import inferencia as pasillo_inferencia\n",
    )
    _asegurar_sin_imports_directos(tmp_path)

    # Mutación m2: puente directo saltándose el pasillo
    _escribir_modulo(
        tmp_path,
        "features/roadmap/services/puente_directo.py",
        "from features.inferencia import inferencia_service\n",
    )
    assert escanear_imports_directos_inferencia(tmp_path) == {"features/roadmap/services/puente_directo.py"}
    with pytest.raises(AssertionError, match=r"features/roadmap/services/puente_directo\.py"):
        _asegurar_sin_imports_directos(tmp_path)


@pytest.mark.parametrize(
    "codigo",
    [
        "import google.genai\n",
        "import google.genai as sdk\nsdk.Client(vertexai=True)\n",
        "from google import genai\n",
        "from google.genai import Client\nClient(vertexai=True)\n",
        "from google.genai import types\n",
        "import google\ngoogle.genai.Client(vertexai=True)\n",
        "import importlib\nimportlib.import_module('google.genai')\n",
        "def usar(genai):\n    return genai.Client(vertexai=True)\n",
    ],
)
def test_escaner_genai_detecta_cada_forma_y_no_confunde_otros_clientes(tmp_path: Path, codigo: str) -> None:
    _escribir_modulo(tmp_path, "api/routers/violacion.py", codigo)
    _escribir_modulo(
        tmp_path,
        "app_core/storage/ok.py",
        "from google.cloud import storage\nimport httpx\n"
        "def f():\n    return storage.Client(), httpx.Client()\n",
    )
    assert escanear_clientes_genai(tmp_path) == {"api/routers/violacion.py"}


@pytest.mark.parametrize(
    "ruta,codigo",
    [
        ("features/preanalisis/services/salto.py", "import features.inferencia\n"),
        ("features/preanalisis/services/salto.py", "from features import inferencia\n"),
        ("features/preanalisis/services/salto.py", "from features.inferencia import inferencia_service\n"),
        ("features/preanalisis/services/salto.py", "from features.inferencia.domain.errores import InferenciaNoDisponible\n"),
        ("features/preanalisis/services/salto.py", "from ...inferencia import inferencia_service\n"),
        ("features/preanalisis/services/salto.py", "import importlib\nimportlib.import_module('features.inferencia')\n"),
        ("api/routers/salto.py", "from features.inferencia import inferencia_service\n"),
    ],
)
def test_escaner_puerta_detecta_todas_las_formas_de_salto(tmp_path: Path, ruta: str, codigo: str) -> None:
    _escribir_modulo(tmp_path, ruta, codigo)
    _escribir_modulo(tmp_path, "features/inferencia/inferencia_service.py", "from features.inferencia.domain import errores\n")
    _escribir_modulo(tmp_path, "features/ai_copilot/ai/prompts.py", "from app_core.pasillo import inferencia\n")
    _escribir_modulo(tmp_path, "scripts/evaluar_ia.py", "from features.inferencia import inferencia_service\n")
    assert escanear_imports_directos_inferencia(tmp_path) == {ruta}
