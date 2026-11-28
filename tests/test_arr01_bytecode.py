# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤qa-engineer
# ¤arbitro
"""ARR-01 §5: el Dockerfile compila el bytecode de la app después de copiar el código."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCKERFILE = RAIZ / "Dockerfile"

PATRON_COPY = re.compile(r"^COPY\s+\.\s+\.\s*$")
PATRON_COMPILEALL = re.compile(r"^RUN\s+.*python\s+-m\s+compileall\b.*\s/app(\s|$)")


def _lineas_activas():
    texto = DOCKERFILE.read_text(encoding="utf-8")
    return [l.strip() for l in texto.splitlines() if l.strip() and not l.strip().startswith("#")]


def test_dockerfile_compila_bytecode_tras_copy_del_codigo():
    lineas = _lineas_activas()
    copys = [i for i, l in enumerate(lineas) if PATRON_COPY.match(l)]
    assert copys, "el Dockerfile debe tener COPY . . (copia del código)"
    compiles = [i for i, l in enumerate(lineas) if PATRON_COMPILEALL.match(l)]
    assert compiles, "falta RUN python -m compileall ... /app en el Dockerfile"
    assert compiles[0] > copys[0], "compileall debe ir después de COPY . ."


def test_dockerfile_compileall_sobre_el_workdir_de_la_app():
    texto = DOCKERFILE.read_text(encoding="utf-8")
    workdir = re.findall(r"^WORKDIR\s+(\S+)\s*$", texto, flags=re.MULTILINE)
    assert workdir and workdir[-1] == "/app", "el WORKDIR debe ser /app"
    assert any(PATRON_COMPILEALL.match(l) for l in _lineas_activas())
