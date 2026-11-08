# ¤regulation-code ¤seguridad ¤arbitro
"""Árbitro de LEG-03: estructura de governance/apoyo/CITAS_LEGALES_VERIFICADAS.md.

Comprueba, sin juzgar el contenido jurídico (lo aprueba el propietario):
- cada fila de la tabla de verificación tiene dato, artículo, fuente, URL oficial (https, dominio
  .gob.ec) y estado «verificado» o «no verificado»;
- el inventario de citas de la interfaz coincide, en los dos sentidos, con el git grep de la ficha:
  `Art(\\.|ículo) ?[0-9]+` sobre frontend/src y features, y además `Arts?\\. ?[0-9]+|SLA ?[0-9]+`
  sobre frontend/src. Cada par (archivo, cita) tiene una fila con norma, cita correcta y estado.

Uso: python scripts/verificar_citas_legales.py   (código 0 si todo cumple)
     python scripts/verificar_citas_legales.py --pares   (lista los pares que exige el inventario)
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parent.parent
DOCUMENTO = RAIZ / "governance" / "apoyo" / "CITAS_LEGALES_VERIFICADAS.md"

PATRON_ARTICULO = r"Art(\.|ículo) ?[0-9]+"
PATRON_PLAZO = r"Arts?\. ?[0-9]+|SLA ?[0-9]+"
ESTADOS = {"verificado", "no verificado"}
TITULO_TABLA = "## Tabla de verificación"
TITULO_INVENTARIO = "## Inventario de citas de la interfaz"
_ARTICULO = re.compile(r"Art(?:s?\.|ículo) ?([0-9]+)")
_SLA = re.compile(r"SLA ?([0-9]+)")


def _grep(patron: str, *rutas: str) -> list[tuple[str, str]]:
    salida = subprocess.run(
        ["git", "grep", "-nE", patron, "--", *rutas],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", check=False,
    ).stdout
    lineas = []
    for linea in salida.splitlines():
        archivo, _, texto = linea.split(":", 2)
        lineas.append((archivo, texto))
    return lineas


def normalizar(cita: str) -> str:
    """«Arts. 21», «Art.21» y «Artículo 21» → «Art. 21»; «SLA 72» → «SLA 72»."""
    cita = cita.strip()
    m = _ARTICULO.fullmatch(cita)
    if m:
        return f"Art. {m.group(1)}"
    m = _SLA.fullmatch(cita)
    if m:
        return f"SLA {m.group(1)}"
    return cita


def pares_esperados() -> set[tuple[str, str]]:
    """Pares (archivo, cita normalizada) que encuentran los git grep de la ficha."""
    pares: set[tuple[str, str]] = set()
    for archivo, texto in _grep(PATRON_ARTICULO, "frontend/src", "features"):
        for m in re.finditer(PATRON_ARTICULO, texto):
            pares.add((archivo, normalizar(m.group(0))))
    for archivo, texto in _grep(PATRON_PLAZO, "frontend/src"):
        for m in re.finditer(PATRON_PLAZO, texto):
            pares.add((archivo, normalizar(m.group(0))))
    return pares


def _filas(texto: str, titulo: str) -> list[list[str]]:
    """Filas de la tabla bajo el título (sin cabecera ni separador)."""
    if titulo not in texto:
        return []
    seccion = texto.split(titulo, 1)[1].split("\n## ", 1)[0]
    filas = []
    for linea in seccion.splitlines():
        linea = linea.strip()
        if not linea.startswith("|") or re.fullmatch(r"\|[\s:|-]+\|", linea):
            continue
        filas.append([c.strip() for c in linea.strip("|").split("|")])
    return filas[1:]  # la primera es la cabecera


def _url_oficial(url: str) -> bool:
    url = url.strip("<>` ")
    m = re.search(r"\((https?://[^)]+)\)", url)  # admite [texto](url)
    partes = urlparse(m.group(1) if m else url)
    return partes.scheme == "https" and bool(partes.hostname) and partes.hostname.endswith(".gob.ec")


def errores(texto: str, esperados: set[tuple[str, str]]) -> list[str]:
    fallos: list[str] = []
    tabla = _filas(texto, TITULO_TABLA)
    if not tabla:
        fallos.append(f"Falta la tabla bajo «{TITULO_TABLA}».")
    for i, fila in enumerate(tabla, 1):
        if len(fila) != 7:
            fallos.append(f"Tabla de verificación, fila {i}: se esperan 7 columnas y hay {len(fila)}.")
            continue
        dato, _prd, articulo, fuente, url, _valor, estado = fila
        if not dato or not articulo or not fuente:
            fallos.append(f"Tabla de verificación, fila {i}: falta dato, artículo o fuente.")
        if not _url_oficial(url):
            fallos.append(f"Tabla de verificación, fila {i} («{dato}»): la URL no es oficial (https, .gob.ec).")
        if estado not in ESTADOS:
            fallos.append(f"Tabla de verificación, fila {i} («{dato}»): estado «{estado}» fuera de {sorted(ESTADOS)}.")

    inventario = _filas(texto, TITULO_INVENTARIO)
    if not inventario:
        fallos.append(f"Falta la tabla bajo «{TITULO_INVENTARIO}».")
    documentados: set[tuple[str, str]] = set()
    for i, fila in enumerate(inventario, 1):
        if len(fila) != 5:
            fallos.append(f"Inventario, fila {i}: se esperan 5 columnas y hay {len(fila)}.")
            continue
        archivo, cita, norma, correcta, estado = (c.strip("`") for c in fila)
        par = (archivo, normalizar(cita))
        if par in documentados:
            fallos.append(f"Inventario: el par {par} está repetido.")
        documentados.add(par)
        if not norma or not correcta:
            fallos.append(f"Inventario, {par}: falta la norma o la cita correcta.")
        if estado not in ESTADOS:
            fallos.append(f"Inventario, {par}: estado «{estado}» fuera de {sorted(ESTADOS)}.")
    for par in sorted(esperados - documentados):
        fallos.append(f"Inventario: falta la fila de {par} (lo encuentra el git grep).")
    for par in sorted(documentados - esperados):
        fallos.append(f"Inventario: sobra la fila de {par} (el git grep ya no la encuentra).")
    return fallos


def main(argv: list[str]) -> int:
    esperados = pares_esperados()
    if "--pares" in argv:
        for archivo, cita in sorted(esperados):
            print(f"{archivo}\t{cita}")
        return 0
    if not DOCUMENTO.exists():
        print(f"[LEG-03] Falta {DOCUMENTO.relative_to(RAIZ)}.")
        return 1
    fallos = errores(DOCUMENTO.read_text(encoding="utf-8"), esperados)
    for fallo in fallos:
        print(f"[LEG-03] {fallo}")
    if fallos:
        return 1
    print(f"[LEG-03] OK: tabla de verificación y {len(esperados)} citas inventariadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
