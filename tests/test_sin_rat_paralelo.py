# ¤rat
# ¤arbitro
"""Árbitro estático: el frontend no mantiene un RAT paralelo al backend.

El RAT canónico vive en ``features/rat``. Este detector recorre también archivos
no versionados para que una recreación local de ``rat_master.json`` no quede fuera
del arbitraje. Cada hallazgo incluye ruta y línea.
"""
from __future__ import annotations

import re
from pathlib import Path


RAIZ = Path(__file__).resolve().parent.parent
FRONTEND = RAIZ / "frontend"
EXTENSIONES_TEXTO = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}
DIRECTORIOS_IGNORADOS = {".git", ".next", "node_modules", "test-results"}

NOMBRE_DATO_RAT = re.compile(r"rat[_-]?master", re.IGNORECASE)
TOKEN_RAT = re.compile(r"\brat\b|rat[_-]?master", re.IGNORECASE)
ESCRITURA_ARCHIVO = re.compile(
    r"\b(?:writeFile|writeFileSync|appendFile|appendFileSync|createWriteStream)\s*\(",
    re.IGNORECASE,
)


def _archivos_frontend() -> list[Path]:
    return sorted(
        ruta
        for ruta in FRONTEND.rglob("*")
        if ruta.is_file() and not DIRECTORIOS_IGNORADOS.intersection(ruta.relative_to(FRONTEND).parts)
    )


def _relativa(ruta: Path) -> str:
    return ruta.relative_to(RAIZ).as_posix()


def _hallazgos() -> list[str]:
    hallazgos: list[str] = []
    for ruta in _archivos_frontend():
        relativa = _relativa(ruta)

        if NOMBRE_DATO_RAT.search(ruta.name):
            hallazgos.append(f"{relativa}:1: archivo de datos RAT paralelo")

        if ruta.suffix.lower() not in EXTENSIONES_TEXTO:
            continue
        texto = ruta.read_text(encoding="utf-8", errors="replace")
        lineas = texto.splitlines()
        archivo_identificado_como_rat = bool(
            TOKEN_RAT.search(ruta.stem) or NOMBRE_DATO_RAT.search(texto)
        )
        es_accion_servidor_rat = (
            relativa.startswith("frontend/src/app/actions/")
            and any(linea.strip().strip(";") in {'"use server"', "'use server'"} for linea in lineas)
            and archivo_identificado_como_rat
        )
        if es_accion_servidor_rat:
            numero = next(
                (n for n, linea in enumerate(lineas, 1) if TOKEN_RAT.search(linea)),
                1,
            )
            hallazgos.append(f"{relativa}:{numero}: acción de servidor RAT en el frontend")

        for numero, linea in enumerate(lineas, 1):
            if ESCRITURA_ARCHIVO.search(linea):
                if archivo_identificado_como_rat or TOKEN_RAT.search(linea):
                    hallazgos.append(
                        f"{relativa}:{numero}: escritura de archivo para datos RAT: {linea.strip()[:120]}"
                    )
    return hallazgos


def test_frontend_no_reintroduce_un_rat_paralelo():
    hallazgos = _hallazgos()
    assert not hallazgos, "RAT paralelo detectado:\n" + "\n".join(hallazgos)
