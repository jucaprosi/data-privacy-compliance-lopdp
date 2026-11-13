"""GCP-10 · El contexto de la imagen del frontend no lleva dependencias locales, compilados ni secretos.

`¤navegacion-menus` `¤arbitro`. Prueba estática: no ejecuta Docker.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DOCKERIGNORE = RAIZ / "frontend" / ".dockerignore"
DOCKERFILE = RAIZ / "frontend" / "Dockerfile.cloudrun"
OBLIGATORIAS = ("node_modules", ".next", ".env*", "tests", "playwright-report", "test-results", "*.log")


def _patrones(texto: str) -> list[str]:
    return [l.strip().rstrip("/") for l in texto.splitlines() if l.strip() and not l.lstrip().startswith("#")]


def _excluye(patrones: list[str], nombre: str) -> bool:
    if nombre == ".env*":  # basta con `.env.*` (o `.env*`) además de `.env`
        return ".env" in patrones and (".env.*" in patrones or ".env*" in patrones)
    return nombre in patrones


def _copia_todo(dockerfile: str) -> bool:
    return any(l.split()[:3] == ["COPY", ".", "."] for l in dockerfile.splitlines() if l.strip() and not l.lstrip().startswith("#"))


def faltas(dockerfile: str, dockerignore: str | None) -> list[str]:
    """Qué incumple el par (Dockerfile, .dockerignore); lista vacía si cumple."""
    if dockerignore is None:
        return ["falta frontend/.dockerignore"] if _copia_todo(dockerfile) else []
    patrones = _patrones(dockerignore)
    return [f"no excluye {n}" for n in OBLIGATORIAS if not _excluye(patrones, n)]


def _real() -> str | None:
    return DOCKERIGNORE.read_text(encoding="utf-8") if DOCKERIGNORE.is_file() else None


def test_el_dockerignore_existe_y_excluye_lo_obligatorio():
    assert DOCKERIGNORE.is_file(), "falta frontend/.dockerignore"
    assert faltas(DOCKERFILE.read_text(encoding="utf-8"), _real()) == []


def test_el_dockerfile_copia_el_contexto_entero():
    """Es la razón de ser del archivo: si deja de copiar `.`, hay que revisar esta ficha."""
    assert _copia_todo(DOCKERFILE.read_text(encoding="utf-8"))


def test_los_secretos_se_excluyen_salvo_el_ejemplo():
    patrones = _patrones(_real() or "")
    assert ".env" in patrones and ".env.*" in patrones
    assert patrones.index("!.env.example") > patrones.index(".env.*")  # la excepción va después


def test_mutacion_sin_dockerignore():
    assert faltas(DOCKERFILE.read_text(encoding="utf-8"), None) == ["falta frontend/.dockerignore"]


def test_mutacion_sin_node_modules_ni_next():
    base = _real() or ""
    for nombre in ("node_modules", ".next"):
        mutado = "\n".join(l for l in base.splitlines() if l.strip() != nombre)
        assert faltas(DOCKERFILE.read_text(encoding="utf-8"), mutado) == [f"no excluye {nombre}"]


def test_mutacion_sin_patron_de_secretos():
    mutado = "\n".join(l for l in (_real() or "").splitlines() if not l.startswith(".env"))
    assert "no excluye .env*" in faltas(DOCKERFILE.read_text(encoding="utf-8"), mutado)
