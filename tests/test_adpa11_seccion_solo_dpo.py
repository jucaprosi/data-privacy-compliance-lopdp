# ¤adpa ¤frontend-ide
"""ADPA-11: sección #DIAG-14 alrededor de los botones de nivel y de evidencia en DiagnosticCanvas.tsx.

1. Los bloques existen, están equilibrados y contienen los dos grupos de botones.
2. El diff contra main solo añade líneas de comentario (mutación: cambiar una línea de código la hace fallar).
3. Las marcas ajenas (#EVI-01, #DIAG-05, #DIAG-07, #DIAG-11) quedan iguales que en main.
"""
from pathlib import Path
import re
import subprocess

import pytest

RAIZ = Path(__file__).resolve().parents[1]
RUTA = "frontend/src/components/DiagnosticCanvas.tsx"
MARCA = re.compile(r"(?://|\{/\*) --- (INICIO|FIN) ([A-Z]+-\d+[a-z]?) ---(?: \*/\})?")
AJENAS = ["EVI-01", "DIAG-05", "DIAG-07", "DIAG-11"]


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", check=False)


def _base() -> str:
    for ref in ("origin/main", "main"):
        r = _git("merge-base", "HEAD", ref)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    pytest.skip("sin rama main para comparar")


def _bloques(texto: str) -> list[str]:
    return re.findall(r"--- INICIO DIAG-14 ---(.*?)--- FIN DIAG-14 ---", texto, re.S)


def test_bloques_diag14_contienen_los_dos_grupos_de_botones() -> None:
    texto = (RAIZ / RUTA).read_text(encoding="utf-8")
    marcas = [m for m in MARCA.findall(texto) if m[1] == "DIAG-14"]
    assert marcas == [("INICIO", "DIAG-14"), ("FIN", "DIAG-14")] * 2
    bloques = _bloques(texto)
    assert any('aria-labelledby="etiqueta-nivel"' in b and "handleSeleccionarNivel" in b for b in bloques)
    assert any('aria-labelledby="etiqueta-evidencia"' in b and "handleSeleccionarEvidencia" in b for b in bloques)


def test_diff_contra_main_solo_anade_comentarios() -> None:
    diff = _git("diff", "--unified=0", _base(), "--", RUTA).stdout
    cambios = [l for l in diff.splitlines() if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    for linea in cambios:
        assert linea.startswith("+"), f"el diff quita o cambia código: {linea!r}"
        cuerpo = linea[1:].strip()
        assert MARCA.fullmatch(cuerpo), f"el diff añade algo que no es una marca de comentario: {linea!r}"


def test_marcas_ajenas_intactas() -> None:
    antes = _git("show", f"{_base()}:{RUTA}").stdout
    despues = (RAIZ / RUTA).read_text(encoding="utf-8")
    for ident in AJENAS:
        assert [m for m in MARCA.findall(despues) if m[1] == ident] == [m for m in MARCA.findall(antes) if m[1] == ident], ident
