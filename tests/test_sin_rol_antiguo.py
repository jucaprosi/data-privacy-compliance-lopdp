# ¤seguridad
# ¤arbitro
"""Árbitro permanente: el rol antiguo «encargado» no vuelve (ORG-08).

El código se escribe como si `coordinador` hubiera sido siempre el nombre del rol. La palabra
«encargado» sigue siendo legítima en su sentido legal (encargado del tratamiento, Art. 4 LOPDP),
así que este árbitro no vigila la palabra: vigila el ROL.

Regla 1 (todo el código versionado): ni `ROLE_ALIASES` ni el valor del rol como literal
(`'encargado'`, `"encargado"`, `Role.encargado`).

Regla 2 (dominio de roles): en los archivos que tratan roles de la organización, la palabra
«encargado» no aparece en ninguna forma, tampoco en comentarios ni textos de interfaz.

Las exenciones son datos con su motivo, por archivo; ninguna excluye un directorio.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EXTENSIONES = (".py", ".ts", ".tsx", ".js")

ROL_LITERAL = re.compile(r"\bROLE_ALIASES\b|[\"'`]encargado[\"'`]|\bRole\.encargado\b")
PALABRA = re.compile(r"\b[Ee]ncargado\b")

# Archivos que tratan roles de la organización (regla 2).
DOMINIO_ROLES = (
    "api/",
    "features/organizacion/",
    "features/roadmap/",
    "frontend/src/app/harness-roadmap/",
    "frontend/src/components/evidencias/",
    "frontend/src/components/modules/roadmap/",
    "frontend/src/lib/evidencias/",
    "frontend/src/lib/roadmap/",
    "frontend/src/store/",
    "frontend/src/types/",
    "frontend/tests/roadmap/",
    "tests/",
)

EXENCIONES = {
    "tests/test_sin_rol_antiguo.py": "Este árbitro define los patrones que busca.",
    "tests/test_rol_coordinador.py": "Prueba la migración histórica encargado→coordinador y que X-Role: encargado recibe 403.",
    "frontend/tests/roadmap/admin.spec.ts": "Afirma que el selector de roles NO ofrece la opción encargado.",
    "features/ai_copilot/domain/sanitizer.py": "Vocabulario legal de la LOPDP (encargado del tratamiento), no el rol.",
    "features/regulacion_rag/domain/corpus.py": "Términos de búsqueda del corpus legal (Art. 34 LOPDP, encargado del tratamiento), no el rol.",
}


def _archivos_versionados() -> list[str]:
    salida = subprocess.run(
        ["git", "ls-files", "-z"], cwd=RAIZ, capture_output=True, check=True
    ).stdout.decode("utf-8")
    return [r for r in salida.split("\0") if r.endswith(EXTENSIONES) and not r.startswith("alembic/versions/")]


def _violaciones() -> list[str]:
    encontradas = []
    for ruta in _archivos_versionados():
        if ruta in EXENCIONES:
            continue
        en_dominio = ruta.startswith(DOMINIO_ROLES)
        texto = (RAIZ / ruta).read_text(encoding="utf-8", errors="replace")
        for n, linea in enumerate(texto.splitlines(), 1):
            if ROL_LITERAL.search(linea) or (en_dominio and PALABRA.search(linea)):
                encontradas.append(f"{ruta}:{n}: {linea.strip()[:120]}")
    return encontradas


def test_sin_rol_antiguo():
    violaciones = _violaciones()
    assert not violaciones, "Restos del rol antiguo «encargado»:\n" + "\n".join(violaciones)


def test_las_exenciones_existen_y_contienen_lo_que_eximen():
    """Una exención que ya no exime nada es un hueco: se retira."""
    for ruta, motivo in EXENCIONES.items():
        assert motivo.strip(), ruta
        texto = (RAIZ / ruta).read_text(encoding="utf-8")
        assert PALABRA.search(texto) or ROL_LITERAL.search(texto), f"{ruta} ya no necesita exención"
