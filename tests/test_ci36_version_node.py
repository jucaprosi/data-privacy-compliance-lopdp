# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""CI-36 · Una sola versión mayor de Node en imágenes, engines y CI.

`¤arbitro`

La versión sale de `engines.node` de `frontend/package.json` (R2) y contra ella se comparan
los `FROM node:<N>-…` de los dos Dockerfiles, el `nodejs` de apk del `runner` alpine y cada
`node-version` del workflow (R1). El workflow se lee como texto, sin `import yaml` (R-ADPA).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
FRONTEND = RAIZ / "frontend"
PAQUETE = FRONTEND / "package.json"
DOCKERFILES = (FRONTEND / "Dockerfile.cloudrun", FRONTEND / "Dockerfile")
WORKFLOW = RAIZ / ".github" / "workflows" / "zero-regression-pipeline.yml"

# Dato de Alpine, no del proyecto: versión mayor del paquete `nodejs` de cada rama estable
# (pkgs.alpinelinux.org, repositorio main). Una rama que no esté aquí falla cerrada.
NODEJS_DE_ALPINE = {
    "3.18": 18,
    "3.19": 20,
    "3.20": 20,
    "3.21": 22,
    "3.22": 22,
}

_FROM = re.compile(r"^\s*FROM\s+(\S+)(?:\s+AS\s+(\S+))?\s*$", re.I)
_NODE_VERSION = re.compile(r"^\s*node-version:\s*(\S+)\s*$")


class VersionIncoherente(AssertionError):
    """Un sitio declara una versión mayor de Node distinta de la de engines."""


def version_de_engines(paquete: dict) -> int:
    """Versión mayor de `engines.node` con la forma `>=N <N+1`."""
    engines = paquete.get("engines")
    if not isinstance(engines, dict) or "node" not in engines:
        raise VersionIncoherente("frontend/package.json no declara engines.node")
    rango = re.fullmatch(r">=\s*(\d+)\s+<\s*(\d+)", str(engines["node"]).strip())
    if not rango or int(rango.group(2)) != int(rango.group(1)) + 1:
        raise VersionIncoherente(f"engines.node no fija una sola versión mayor: {engines['node']!r}")
    return int(rango.group(1))


def _etapas(texto: str) -> list[tuple[str, str | None, list[str]]]:
    """(base, alias, líneas RUN) de cada etapa de un Dockerfile."""
    etapas: list[tuple[str, str | None, list[str]]] = []
    for linea in texto.splitlines():
        coincidencia = _FROM.match(linea)
        if coincidencia:
            etapas.append((coincidencia.group(1), coincidencia.group(2), []))
        elif etapas:
            etapas[-1][2].append(linea.strip())
    return etapas


def version_de_alpine(base: str) -> int:
    """Versión mayor del `nodejs` de apk de una base `alpine:X.Y`."""
    rama = re.fullmatch(r"alpine:(\d+\.\d+)(?:\.\d+)?", base)
    if not rama or rama.group(1) not in NODEJS_DE_ALPINE:
        raise VersionIncoherente(f"no se sabe qué nodejs trae {base!r}")
    return NODEJS_DE_ALPINE[rama.group(1)]


def versiones_de_dockerfile(texto: str) -> list[tuple[str, int]]:
    """(sitio, versión mayor) de cada etapa con Node: `FROM node:<N>-…` o alpine con `apk add nodejs`."""
    sitios: list[tuple[str, int]] = []
    for base, alias, cuerpo in _etapas(texto):
        nombre = alias or base
        if base.startswith("node:"):
            mayor = re.fullmatch(r"node:(\d+)(?:[.-]\S*)?", base)
            if not mayor:
                raise VersionIncoherente(f"la etapa {nombre} no fija la versión mayor: {base!r}")
            sitios.append((f"{nombre} ({base})", int(mayor.group(1))))
        elif base.startswith("alpine:") and any("apk add" in r and "nodejs" in r for r in cuerpo):
            sitios.append((f"{nombre} ({base}, nodejs de apk)", version_de_alpine(base)))
    return sitios


def versiones_de_workflow(texto: str) -> list[tuple[str, int]]:
    """(línea, versión mayor) de cada `node-version` del workflow."""
    sitios: list[tuple[str, int]] = []
    for numero, linea in enumerate(texto.splitlines(), start=1):
        coincidencia = _NODE_VERSION.match(linea)
        if coincidencia:
            valor = coincidencia.group(1).strip("\"'")
            mayor = re.fullmatch(r"(\d+)(?:\.\S*)?", valor)
            if not mayor:
                raise VersionIncoherente(f"node-version sin versión mayor en la línea {numero}: {valor!r}")
            sitios.append((f"workflow:{numero}", int(mayor.group(1))))
    return sitios


def exigir_misma_version(esperada: int, sitios: list[tuple[str, int]]) -> None:
    distintos = [f"{sitio} → {mayor}" for sitio, mayor in sitios if mayor != esperada]
    if distintos:
        raise VersionIncoherente(f"engines.node pide {esperada}; difieren: {distintos}")


def _leer(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def esperada() -> int:
    return version_de_engines(json.loads(_leer(PAQUETE)))


def test_engines_declarado(esperada):
    assert esperada > 0
    with pytest.raises(VersionIncoherente):
        version_de_engines({"name": "frontend"})
    with pytest.raises(VersionIncoherente):
        version_de_engines({"engines": {"node": f">={esperada}"}})


def test_runner_alpine_trae_la_misma_version(esperada):
    etapas = _etapas(_leer(FRONTEND / "Dockerfile.cloudrun"))
    base, alias, _ = etapas[-1]
    assert alias == "runner" and base.startswith("alpine:"), base
    assert version_de_alpine(base) == esperada, base

    # Un runner en otra rama de alpine trae otro nodejs: la regla lo rechaza.
    ajenas = [rama for rama, mayor in NODEJS_DE_ALPINE.items() if mayor != esperada]
    assert ajenas
    for rama in ajenas:
        sintetico = f"FROM node:{esperada}-alpine AS builder\nFROM alpine:{rama} AS runner\nRUN apk add --no-cache nodejs\n"
        with pytest.raises(VersionIncoherente):
            exigir_misma_version(esperada, versiones_de_dockerfile(sintetico))
    with pytest.raises(VersionIncoherente):
        version_de_alpine("alpine:9.99")


def test_una_sola_version_de_node(esperada):
    sitios: list[tuple[str, int]] = []
    for dockerfile in DOCKERFILES:
        propios = versiones_de_dockerfile(_leer(dockerfile))
        assert propios, f"{dockerfile.name} no declara Node"
        sitios += [(f"{dockerfile.name}:{sitio}", mayor) for sitio, mayor in propios]
    del_workflow = versiones_de_workflow(_leer(WORKFLOW))
    assert del_workflow, "el workflow no fija node-version"
    exigir_misma_version(esperada, sitios + del_workflow)
