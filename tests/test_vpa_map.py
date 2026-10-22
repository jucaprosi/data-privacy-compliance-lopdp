# ¤vpa
# ¤arbitro
"""Árbitro del mapa de rastros (GOB-01).

Decisión del propietario (2026-10-22): manda el repositorio. Todo rastro que declara una ficha de
`governance/tareas/` figura en `governance/artefactos/VPA_MAP.md` y `git grep` lo encuentra fuera
de las fichas. Los rastros aún sin alta van en PENDIENTES con su motivo; uno que ya figura en el
mapa no puede seguir pendiente.
"""
from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MAPA = RAIZ / "governance" / "artefactos" / "VPA_MAP.md"

PENDIENTES: dict[str, str] = {}


def _rastros_del_mapa() -> set[str]:
    return set(re.findall(r"`(¤[a-z0-9-]+)`", MAPA.read_text(encoding="utf-8")))


def _rastros_de_las_fichas() -> set[str]:
    rastros: set[str] = set()
    for ficha in (RAIZ / "governance" / "tareas").glob("*.md"):
        texto = ficha.read_text(encoding="utf-8").replace("\r\n", "\n")
        cabecera = re.match(r"\+\+\+\n(.*?)\n\+\+\+", texto, re.S)
        if cabecera:
            rastros.update(tomllib.loads(cabecera.group(1)).get("rastros", []))
    return rastros


def _git_grep_encuentra(rastro: str) -> bool:
    salida = subprocess.run(
        ["git", "grep", "-F", "-l", rastro, "--", ".", ":!governance/tareas"],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
    )
    return bool(salida.stdout.strip())


def test_cada_rastro_de_las_fichas_esta_en_el_mapa():
    faltan = sorted(_rastros_de_las_fichas() - _rastros_del_mapa() - PENDIENTES.keys())
    assert not faltan, f"Rastros de las fichas sin alta en VPA_MAP.md: {faltan}"


def test_los_rastros_de_gob_01_figuran_y_se_encuentran():
    mapa = _rastros_del_mapa()
    for rastro in ("¤roadmap", "¤rbac-tenant"):
        assert rastro in mapa, f"{rastro} no figura en VPA_MAP.md"
        assert _git_grep_encuentra(rastro), f"git grep no encuentra {rastro} fuera de las fichas"


def test_un_pendiente_que_ya_figura_deja_de_serlo():
    ya_en_mapa = sorted(PENDIENTES.keys() & _rastros_del_mapa())
    assert not ya_en_mapa, f"Retire de PENDIENTES los que ya figuran en el mapa: {ya_en_mapa}"
    for rastro, motivo in PENDIENTES.items():
        assert motivo.strip(), rastro
