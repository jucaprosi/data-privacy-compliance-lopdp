# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤regulation-code ¤seguridad ¤arbitro ¤cita-verificada
"""BIB-403 R1 y R8: árbitro de citas de las plantillas, en los dos sentidos.

  (sin opción)   código 0 si cada cita de las 12 plantillas tiene fila `verificada` en
                 governance/artefactos/CITAS_PLANTILLAS_VERIFICADAS.md (ida), cada clave de citas.json
                 aparece en su plantilla (vuelta), citas.json coincide con el artefacto y cada sección con
                 efecto jurídico lleva su cita (R8). Cualquier fallo: código 1.
  --generar      escribe data/biblioteca/pmv/citas.json desde el artefacto y las plantillas (nunca a mano).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from features.biblioteca.domain.plantillas_md import leer_metadatos, separar  # noqa: E402
from features.biblioteca.domain.validacion import (  # noqa: E402
    errores_ida, errores_secciones, errores_vuelta, extraer_citas,
)

ARTEFACTO = RAIZ / "governance" / "artefactos" / "CITAS_PLANTILLAS_VERIFICADAS.md"
CARPETA = RAIZ / "data" / "biblioteca" / "pmv"
CITAS_JSON = CARPETA / "citas.json"
_HUELLA = re.compile(r"`([0-9a-f]{64})`")
_URL = re.compile(r"https://\S+?(?=[\s)]|$)")


# ¤adpa
def _filas(texto: str, titulo: str) -> list[list[str]]:
    seccion = texto.split(titulo, 1)[1].split("\n## ", 1)[0]
    filas = []
    for linea in seccion.splitlines():
        linea = linea.strip()
        if linea.startswith("|") and not re.fullmatch(r"\|[\s:|-]+\|", linea):
            filas.append([c.strip() for c in linea.strip("|").split("|")])
    return filas[1:]


# ¤adpa
def leer_artefacto(texto: str) -> tuple[dict[str, str], dict[str, str], dict[str, dict]]:
    """(estado por clave, fuente por clave, fuentes con url y sha256) del artefacto de LEG-08."""
    estados, fuente_de, fuentes = {}, {}, {}
    for fila in _filas(texto, "\n## Fuentes"):
        fuente_id = fila[0].strip("`")
        url = _URL.search(fila[2])
        huella = _HUELLA.search(fila[3])
        fuentes[fuente_id] = {"url": url.group(0) if url else None, "sha256": huella.group(1) if huella else None}
    for fila in _filas(texto, "\n## Tabla de citas"):
        clave, fuente_id, estado = fila[0].strip("`"), fila[1].strip("`"), fila[5]
        estados[clave], fuente_de[clave] = estado, fuente_id
    return estados, fuente_de, fuentes


# ¤adpa
def leer_plantillas() -> dict[str, tuple[dict, str]]:
    salida = {}
    for ruta in sorted(CARPETA.glob("BIB-*.md")):
        cabecera, cuerpo = separar(ruta.read_bytes().decode("utf-8"))
        salida[ruta.stem] = (leer_metadatos(cabecera), cuerpo)
    return salida


# ¤adpa
def citas_de(meta: dict, cuerpo: str) -> tuple[set[str], list[str]]:
    claves, sin_norma = extraer_citas(str(meta.get("base_lopdp", "")))
    del_cuerpo, sin_norma_cuerpo = extraer_citas(cuerpo)
    return claves | del_cuerpo, sin_norma + sin_norma_cuerpo


# ¤adpa
def generar(estados, fuente_de, fuentes, plantillas) -> dict:
    asignadas = {codigo: sorted(citas_de(meta, cuerpo)[0]) for codigo, (meta, cuerpo) in plantillas.items()}
    return {
        "plantillas": asignadas,
        "estados": dict(sorted(estados.items())),
        "fuente_de": dict(sorted(fuente_de.items())),
        "fuentes": dict(sorted(fuentes.items())),
    }


# ¤adpa
def errores(estados, fuente_de, fuentes, plantillas, publicado: dict | None) -> list[str]:
    fallos: list[str] = []
    verificadas = {c for c, e in estados.items() if e == "verificada"}
    for codigo, (meta, cuerpo) in plantillas.items():
        claves, sin_norma = citas_de(meta, cuerpo)
        fallos += [f"{codigo}: «{s}» sin norma identificable" for s in sin_norma]
        fallos += [f"{codigo}: {f}" for f in errores_ida(claves, estados)]
        informativas = [i.get("titulo", "") for i in meta.get("secciones_informativas", []) or []]
        fallos += [f"{codigo}: {f}" for f in errores_secciones(cuerpo, informativas, verificadas)]
        if publicado is not None:
            fallos += [f"{codigo}: {f}" for f in errores_vuelta(set(publicado["plantillas"].get(codigo, [])), claves)]
    if publicado is None:
        fallos.append("falta data/biblioteca/pmv/citas.json (genérelo con --generar)")
    elif publicado != generar(estados, fuente_de, fuentes, plantillas):
        fallos.append("citas.json no coincide con el artefacto y las plantillas (regenere con --generar)")
    return fallos


# ¤adpa
def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    estados, fuente_de, fuentes = leer_artefacto(ARTEFACTO.read_bytes().decode("utf-8"))
    plantillas = leer_plantillas()
    if "--generar" in argv:
        # LF y sin BOM, también en Windows.
        CITAS_JSON.write_bytes((json.dumps(generar(estados, fuente_de, fuentes, plantillas), ensure_ascii=False,
                                           indent=2, sort_keys=True) + "\n").encode("utf-8"))
        print(f"Generado {CITAS_JSON.relative_to(RAIZ)}")
        return 0
    publicado = json.loads(CITAS_JSON.read_bytes().decode("utf-8")) if CITAS_JSON.exists() else None
    fallos = errores(estados, fuente_de, fuentes, plantillas, publicado)
    for fallo in fallos:
        print(f"[BIB-403] {fallo}")
    if fallos:
        return 1
    print(f"[BIB-403] OK: {len(plantillas)} plantillas con sus citas verificadas y cada sección con su cita.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
