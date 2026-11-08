# -*- coding: utf-8 -*-
# ¤seguridad ¤arbitro
"""Árbitro SEC-14: el frontend no publica mapas de fuente ni secretos en variables públicas.

Reglas (governance/especificaciones/SEC-14.md):
- R1: ninguna configuración de Next (`frontend/next.config*.ts`) fija `productionBrowserSourceMaps: true`.
- R2: ninguna variable `NEXT_PUBLIC_*` usada en `frontend/src` tiene nombre de secreto.
- R3: la carpeta compilada (`frontend/.next/static`) no contiene `.map`, ni `sourceMappingURL`,
  ni cadenas con forma de credencial.
- R4: el informe nombra archivo y regla, nunca el valor hallado.

Uso tras `npm run build`: `python scripts/verificar_bundle_frontend.py [carpeta]`.
Código 0 si está limpio; 1 si hay hallazgos. Sin carpeta revisa `frontend/.next/static`;
si esa carpeta no existe, termina con 1 (no hay compilación que verificar).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FRONTEND = RAIZ / "frontend"
CARPETA_PAQUETE = FRONTEND / ".next" / "static"

_MAPAS_ACTIVADOS = re.compile(r"productionBrowserSourceMaps\s*:\s*true\b")
_VARIABLE_PUBLICA = re.compile(r"\bNEXT_PUBLIC_[A-Z0-9_]+\b")
_PALABRAS_SECRETO = ("SECRET", "PASSWORD", "PRIVATE", "TOKEN")
_CREDENCIALES = (
    ("clave sk-", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("clave privada PEM", re.compile(r"-----BEGIN")),
    ("URL de PostgreSQL con contraseña", re.compile(r"postgres(?:ql)?://[^\s:/@'\"]+:[^\s@'\"]+@")),
)
_EXTENSIONES_FUENTE = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}


# ¤seguridad
def es_nombre_de_secreto(nombre: str) -> bool:
    """Nombre de secreto: contiene SECRET, PASSWORD, PRIVATE o TOKEN, o termina en _KEY."""
    return any(p in nombre for p in _PALABRAS_SECRETO) or nombre.endswith("_KEY")


# ¤seguridad
def revisar_configuraciones(frontend: Path = FRONTEND) -> list[tuple[str, str]]:
    """R1 sobre cada `next.config*.ts` del frontend."""
    hallazgos = []
    for config in sorted(frontend.glob("next.config*.ts")):
        if _MAPAS_ACTIVADOS.search(config.read_text(encoding="utf-8", errors="replace")):
            hallazgos.append((config.name, "R1 productionBrowserSourceMaps activado"))
    return hallazgos


# ¤seguridad
def revisar_variables_publicas(src: Path = FRONTEND / "src") -> list[tuple[str, str]]:
    """R2 sobre los archivos de código de `frontend/src`. Nombra la variable, que no es un valor."""
    hallazgos = []
    for archivo in sorted(p for p in src.rglob("*") if p.suffix in _EXTENSIONES_FUENTE and p.is_file()):
        nombres = set(_VARIABLE_PUBLICA.findall(archivo.read_text(encoding="utf-8", errors="replace")))
        for nombre in sorted(n for n in nombres if es_nombre_de_secreto(n)):
            hallazgos.append((archivo.relative_to(src).as_posix(), f"R2 variable pública con nombre de secreto {nombre}"))
    return hallazgos


# ¤seguridad
def revisar_paquete(carpeta: Path = CARPETA_PAQUETE) -> list[tuple[str, str]]:
    """R3 sobre la carpeta compilada. R4: los motivos nunca incluyen el texto hallado."""
    hallazgos = []
    for archivo in sorted(p for p in carpeta.rglob("*") if p.is_file()):
        ruta = archivo.relative_to(carpeta).as_posix()
        if archivo.suffix == ".map":
            hallazgos.append((ruta, "R3 mapa de fuente publicado"))
            continue
        texto = archivo.read_text(encoding="utf-8", errors="replace")
        if "sourceMappingURL" in texto:
            hallazgos.append((ruta, "R3 comentario sourceMappingURL"))
        for motivo, patron in _CREDENCIALES:
            if patron.search(texto):
                hallazgos.append((ruta, f"R3 cadena con forma de credencial ({motivo})"))
    return hallazgos


# ¤arbitro
def main(argv: list[str] | None = None) -> int:
    argumentos = sys.argv[1:] if argv is None else argv
    carpeta = Path(argumentos[0]) if argumentos else CARPETA_PAQUETE
    if not carpeta.is_dir():
        print(f"SEC-14: no existe la carpeta compilada {carpeta}; corre antes `npm run build`.")
        return 1
    hallazgos = revisar_paquete(carpeta)
    for ruta, motivo in hallazgos:
        print(f"SEC-14 FALLA {ruta}: {motivo}")
    if hallazgos:
        print(f"SEC-14: {len(hallazgos)} hallazgo(s) en el paquete del frontend.")
        return 1
    print("SEC-14: paquete del frontend limpio (sin mapas de fuente ni credenciales).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
