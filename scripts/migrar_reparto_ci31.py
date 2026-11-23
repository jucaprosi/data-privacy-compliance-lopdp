# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa
"""CI-31 R5 · Traslado de una sola vez del reparto a «un brief por ficha, sin numeración global».

Sin `--escribir` muestra lo que cambiaría; con `--escribir` lo aplica. Es idempotente: sobre un árbol ya migrado no
cambia nada. Hace, sin perder ni duplicar líneas de bloque:
  1. en cada brief, `### BL-<n> · … (tanda N)` pasa a `### <ID> · … (tanda N)` (ID = nombre del archivo) y las
     citas `BL-<n>` de los briefs pasan al id de su ficha;
  2. cada línea de «Sin agente» que cita una ficha pendiente sin brief se añade al cuerpo de esa ficha como
     «**Sin agente.** <texto>» y la ficha recibe `agente = "ninguno"`;
  3. las demás líneas de «Sin agente» pasan a «## Decisiones del propietario» de la portada (que ningún árbitro lee);
  4. la tabla de tandas se quita de la portada: la vista se reconstruye con `verificar_reparto.py --tandas`.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PORTADA = RAIZ / "governance" / "apoyo" / "BRIEFS_POR_BLOQUE.md"
DIR_BRIEFS = RAIZ / "governance" / "apoyo" / "briefs"
DIR_TAREAS = RAIZ / "governance" / "tareas"

_CAB_BL = re.compile(r"(?m)^### (BL-\d+)( · .+?\(tanda \d+\)\s*)$")
_ID_CITADO = re.compile(r"`([A-Z]+-\d+[a-z]?)`")
_BL = re.compile(r"\bBL-\d+\b")
_TAREA = re.compile(r"(?m)^\d+\. `([A-Za-z0-9-]+)`")
_TANDAS = "## Tandas de lanzamiento"
_SIN_AGENTE = "## Sin agente"
TEXTO_TANDAS = ("La tanda de cada bloque va en la cabecera de su brief (`### <ID> · título (tanda N)`); "
                "`python scripts/verificar_reparto.py --tandas` imprime la vista de tandas, calculada al leer (CI-31). "
                "Lanza una tanda cuando la anterior esté **integrada en `main`**. Dentro de una tanda los bloques "
                "son independientes.\n\n")


# ¤adpa
def quitar_citas_bl(linea: str) -> str:
    """Quita de una línea de la portada las citas `BL-<n>` (numeración retirada), sin tocar nada más."""
    linea = re.sub(r"\s*\((?:BL-\d+(?:,\s*)?)+\)", "", linea)
    linea = re.sub(r",\s*BL-\d+", "", linea)
    linea = re.sub(r"\s*\bBL-\d+\b", "", linea)
    return linea


# ¤adpa
def _seccion(texto: str, titulo: str) -> tuple[int, int] | None:
    """Rango [inicio, fin) de una sección «## …»: hasta la siguiente «## »."""
    m = re.search(rf"(?m)^{re.escape(titulo)}\b.*$", texto)
    if m is None:
        return None
    sig = re.compile(r"(?m)^## ").search(texto, m.end())
    return m.start(), (sig.start() if sig else len(texto))


# ¤adpa
def migrar_briefs(briefs: dict[str, str]) -> dict[str, str]:
    """Paso 1: cabeceras y citas de los briefs. Un id `BL-<n>` sin brief que lo lleve es un error."""
    mapa: dict[str, str] = {}
    for nombre, texto in briefs.items():
        for m in _CAB_BL.finditer(texto):
            mapa[m.group(1)] = nombre
    salida: dict[str, str] = {}
    for nombre, texto in briefs.items():
        nuevo = _CAB_BL.sub(lambda m: f"### {nombre}{m.group(2)}", texto)
        huerfanas = sorted({c for c in _BL.findall(nuevo) if c not in mapa})
        if huerfanas:
            raise ValueError(f"briefs/{nombre}.md cita {huerfanas}, que ningún brief lleva: resuélvelo a mano")
        salida[nombre] = _BL.sub(lambda m: mapa[m.group(0)], nuevo)
    return salida


# ¤adpa
def _con_agente_ninguno(texto: str, frase: list[str]) -> str:
    eol = "\r\n" if "\r\n" in texto else "\n"
    lineas = texto.split(eol)
    if lineas[0].strip() != "+++":
        raise ValueError("falta la cabecera '+++'")
    fin = lineas.index("+++", 1)
    if not any(l.startswith("agente") for l in lineas[1:fin]):
        lineas.insert(fin, 'agente = "ninguno"')
    cuerpo = eol.join(lineas).rstrip("\r\n") + eol
    for linea in frase:
        cuerpo += eol + f"**Sin agente.** {linea}" + eol
    return cuerpo


# ¤adpa
def migrar_portada(portada: str, fichas: dict[str, str], con_brief: set[str]) -> tuple[str, dict[str, list[str]], list[str]]:
    """Pasos 2 a 4 sobre la portada. Devuelve (portada nueva, líneas por ficha, líneas a «Decisiones»)."""
    rango = _seccion(portada, _SIN_AGENTE)
    por_ficha: dict[str, list[str]] = {}
    decisiones: list[str] = []
    nueva = portada
    if rango is not None:
        inicio, fin = rango
        seccion = portada[inicio:fin]
        sub = re.search(r"(?m)^### ", seccion)  # un «### » de la sección sigue en la portada, tras las decisiones
        cola = seccion[sub.start():] if sub else ""
        for linea in seccion[:sub.start() if sub else len(seccion)].splitlines():
            if not linea.startswith("- "):
                continue
            citadas = [i for i in dict.fromkeys(_ID_CITADO.findall(linea)) if i in fichas and i not in con_brief]
            if citadas:
                for i in citadas:
                    por_ficha.setdefault(i, []).append(linea[2:])
            else:
                decisiones.append(quitar_citas_bl(linea))
        bloque = "## Decisiones del propietario (ningún árbitro lo lee)\n\n" + "".join(l + "\n" for l in decisiones)
        nueva = portada[:inicio] + bloque + ("\n" + cola if cola else "\n") + portada[fin:]
    t = _seccion(nueva, _TANDAS)
    if t is not None:
        nueva = nueva[:t[0]] + _TANDAS + "\n\n" + TEXTO_TANDAS + nueva[t[1]:]
    nueva = nueva.replace("<BL-xx>", "<ID>").replace("BL-xx", "<ID>")
    nueva = nueva.replace("o en «Sin agente»", 'o tiene `agente = "ninguno"` en su ficha')
    nueva = "".join(quitar_citas_bl(l) if _BL.search(l) else l for l in nueva.splitlines(keepends=True))
    return nueva, por_ficha, decisiones


# ¤adpa
def migrar(portada: str, briefs: dict[str, str], fichas: dict[str, str]):
    """Núcleo puro. `fichas` es {id: texto}. Devuelve (portada, briefs, fichas cambiadas, informe)."""
    estado = {i: re.search(r'(?m)^estado = "([^"]+)"', t) for i, t in fichas.items()}
    pendientes = {i for i, m in estado.items() if m and m.group(1) != "hecha"}
    con_brief = {t for texto in briefs.values() for t in _TAREA.findall(texto.split("**Rastro", 1)[0])}
    nueva_portada, por_ficha, decisiones = migrar_portada(portada, {i: fichas[i] for i in pendientes}, con_brief)
    nuevos_briefs = migrar_briefs(briefs)
    cambiadas = {i: _con_agente_ninguno(fichas[i], frases) for i, frases in por_ficha.items()}
    informe = {"briefs": sum(1 for n in briefs if briefs[n] != nuevos_briefs[n]), "fichas": sorted(cambiadas),
               "decisiones": len(decisiones)}
    return nueva_portada, nuevos_briefs, cambiadas, informe


# ¤adpa
def _leer(carpeta: Path) -> dict[str, str]:
    return {p.stem: p.read_bytes().decode("utf-8") for p in sorted(carpeta.glob("*.md")) if p.stem.lower() != "readme"}


# ¤adpa
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--escribir", action="store_true", help="aplica la migración; sin él solo informa")
    args = ap.parse_args(argv)
    portada = PORTADA.read_bytes().decode("utf-8")
    briefs, fichas = _leer(DIR_BRIEFS), _leer(DIR_TAREAS)
    nueva, nuevos, cambiadas, informe = migrar(portada, briefs, fichas)
    hay = nueva != portada or nuevos != briefs or bool(cambiadas)
    if not hay:
        print("MIGRAR: el árbol ya está migrado; nada que cambiar.")
        return 0
    print(f"MIGRAR: {informe['briefs']} briefs con cabecera nueva, {len(informe['fichas'])} fichas con "
          f'agente = "ninguno" ({", ".join(informe["fichas"])}), {informe["decisiones"]} decisiones del propietario.')
    if not args.escribir:
        print("Sin --escribir: no se ha escrito nada.")
        return 0
    PORTADA.write_bytes(nueva.encode("utf-8"))
    for nombre, texto in nuevos.items():
        if texto != briefs[nombre]:
            (DIR_BRIEFS / f"{nombre}.md").write_bytes(texto.encode("utf-8"))
    for ident, texto in cambiadas.items():
        (DIR_TAREAS / f"{ident}.md").write_bytes(texto.encode("utf-8"))
    print("MIGRADO.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
