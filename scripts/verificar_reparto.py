# -*- coding: utf-8 -*-
# ¤adpa
"""Árbitro del reparto en bloques: los briefs coinciden con las tasks y los bloques de una tanda no se pisan.

Función pura `revisar(briefs, tareas, indice)`: recibe el texto de `governance/apoyo/BRIEFS_POR_BLOQUE.md` y las tareas ya
cargadas, y devuelve la lista de hallazgos (vacía = reparto válido). No lee el disco más que en `main`.

Comprueba:
  R1  toda task no hecha aparece en un solo bloque o en «Sin agente»; una task hecha no aparece en ninguno.
  R2  la lista «Escribe» de un bloque es exactamente la unión de la `propiedad` de sus tasks.
  R3  dos bloques de una misma tanda no escriben el mismo archivo (salvo secciones reservadas distintas).
  R4  toda dependencia de una task está hecha, o va antes en su bloque, o cae en una tanda anterior.
  R5  (con --rama) los archivos del diff de una rama caben en la lista «Escribe» de su bloque.
  R6  la línea «Hecho si» de cada task del bloque es igual al `arbitro` de su ficha (sin faltar, sobrar ni diferir).
  R7  toda dependencia pendiente de las tasks del bloque, ajena al bloque, está citada en «Depende de» (citar de más avisa).
  R8  el título de cada task del «Objetivo» es el de su ficha y «Sala(s)» es la unión de las `sala` de sus tasks.

`--regenerar` reescribe en el sitio las líneas «Hecho si» desde el `arbitro` (lo ejecuta la coordinadora).
Los bloques sin «Contexto» ni «Hecho si» (los sintéticos de las pruebas) quedan fuera de R6 a R8.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BRIEFS = RAIZ / "governance" / "apoyo" / "BRIEFS_POR_BLOQUE.md"


# ¤adpa
def _cargar_indice():
    ruta = Path(__file__).resolve().parent / "generar_indice_tareas.py"
    spec = importlib.util.spec_from_file_location("generar_indice_tareas", ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["generar_indice_tareas"] = modulo  # las clases de datos lo exigen antes de ejecutar el módulo
    spec.loader.exec_module(modulo)
    return modulo


# ¤adpa
@dataclass
class Bloque:
    id: str
    tanda: int
    tareas: list[str] = field(default_factory=list)
    escribe: list[str] = field(default_factory=list)
    titulos: dict[str, str] = field(default_factory=dict)    # id -> título escrito en «Objetivo»
    hecho_si: dict[str, str] = field(default_factory=dict)   # id -> texto de su línea «Hecho si»
    con_hecho_si: bool = False
    salas: list[str] | None = None                            # None: el bloque no tiene «Contexto»
    depende: list[str] | None = None


_CABECERA = re.compile(r"(?m)^### (BL-\d+) · .+?\(tanda (\d+)\)\s*$")
_TAREA = re.compile(r"(?m)^\d+\. `([A-Za-z0-9-]+)`")
_RUTA = re.compile(r"(?m)^\s+- `([^`]+)`\s*$")
_TITULO = re.compile(r"(?m)^\d+\. `([A-Za-z0-9-]+)` — ([^\r\n]*)")
_HECHO = re.compile(r"(?m)^- `([A-Za-z0-9-]+)`: ([^\r\n]*)")
_CONTEXTO = re.compile(r"(?m)^\*\*Contexto\.\*\* Sala(?:\(s\))?:\s*(.*?)\.\s+Depende de:\s*([^\r\n]*?)"
                       r"(?:\.\s+Especificaciones:[^\r\n]*|\.?)\s*$")
_ID_CITADO = re.compile(r"`([A-Z]+-\d+[a-z]?)`")


# ¤adpa
def _norm(texto: str) -> str:
    return " ".join(texto.split())


# ¤adpa
def _nombres_de_sala(texto: str) -> list[str]:
    return re.findall(r"[A-Za-z_]\w*", texto)


# ¤adpa
def leer_bloques(briefs: str) -> list[Bloque]:
    marcas = list(_CABECERA.finditer(briefs))
    bloques: list[Bloque] = []
    for i, m in enumerate(marcas):
        fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(briefs)
        cuerpo = briefs[m.end():fin]
        cuerpo = re.split(r"(?m)^## ", cuerpo, maxsplit=1)[0]  # no arrastra la sección siguiente
        objetivo = cuerpo.split("**Objetivo**", 1)[-1].split("**Rastro", 1)[0]
        escribe = cuerpo.split("**Escribe**", 1)[-1].split("**No hagas", 1)[0] if "**Escribe**" in cuerpo else ""
        bloque = Bloque(m.group(1), int(m.group(2)), _TAREA.findall(objetivo), _RUTA.findall(escribe))
        bloque.titulos = {tid: _norm(t) for tid, t in _TITULO.findall(objetivo)}
        bloque.con_hecho_si = "**Hecho si**" in cuerpo
        if bloque.con_hecho_si:
            bloque.hecho_si = {tid: _norm(t) for tid, t in _HECHO.findall(cuerpo.split("**Hecho si**", 1)[1])}
        ctx = _CONTEXTO.search(cuerpo)
        if ctx:
            bloque.salas = _nombres_de_sala(ctx.group(1))
            bloque.depende = _ID_CITADO.findall(ctx.group(2))
        bloques.append(bloque)
    return bloques


# ¤adpa
def leer_sin_agente(briefs: str) -> list[str]:
    if "## Sin agente" not in briefs:
        return []
    seccion = briefs.split("## Sin agente", 1)[1]
    seccion = re.split(r"(?m)^## ", seccion, maxsplit=1)[0]
    return re.findall(r"`([A-Z]+-\d+[a-z]?)`", seccion)  # admite sufijos de letra (DEMO-03f)


# ¤adpa
def revisar(briefs: str, tareas: list, indice) -> list[str]:
    por_id = {t.id: t for t in tareas}
    bloques = leer_bloques(briefs)
    sin_agente = leer_sin_agente(briefs)
    hallazgos: list[str] = []

    ubicacion: dict[str, list[str]] = {}
    for b in bloques:
        for tid in b.tareas:
            ubicacion.setdefault(tid, []).append(b.id)
    for tid in sin_agente:
        ubicacion.setdefault(tid, []).append("Sin agente")

    for t in tareas:  # R1
        donde = ubicacion.get(t.id, [])
        if t.estado == "hecha" and donde:
            hallazgos.append(f"R1 {t.id}: está hecha y figura en {', '.join(donde)}")
        elif t.estado != "hecha" and len(donde) != 1:
            hallazgos.append(f"R1 {t.id}: debe figurar en un solo bloque y figura en {len(donde)}"
                             + (f" ({', '.join(donde)})" if donde else ""))
    for tid in ubicacion:
        if tid not in por_id:
            hallazgos.append(f"R1 {tid}: los briefs citan una task que no existe")

    for b in bloques:  # R2
        propiedad = {p for tid in b.tareas if tid in por_id for p in por_id[tid].propiedad}
        escribe = set(b.escribe)
        for falta in sorted(propiedad - escribe):
            hallazgos.append(f"R2 {b.id}: «{falta}» es propiedad de sus tasks y no está en «Escribe»")
        for sobra in sorted(escribe - propiedad):
            hallazgos.append(f"R2 {b.id}: «{sobra}» está en «Escribe» y no es propiedad de ninguna de sus tasks")

    for i, a in enumerate(bloques):  # R3
        for b in bloques[i + 1:]:
            if a.tanda != b.tanda:
                continue
            for pa in a.escribe:
                for pb in b.escribe:
                    if indice.propiedades_se_solapan(pa, pb):
                        hallazgos.append(f"R3 {a.id} y {b.id} (tanda {a.tanda}) escriben «{pa}» / «{pb}»")

    tanda_de = {tid: b.tanda for b in bloques for tid in b.tareas}  # R4
    for b in bloques:
        for pos, tid in enumerate(b.tareas):
            if tid not in por_id:
                continue
            for dep in por_id[tid].depende_de:
                if dep not in por_id or por_id[dep].estado == "hecha":
                    continue
                if dep in b.tareas[:pos] or tanda_de.get(dep, b.tanda) < b.tanda:
                    continue
                hallazgos.append(f"R4 {tid} ({b.id}, tanda {b.tanda}) depende de {dep}, que no va antes ni en una tanda anterior")
    hallazgos += revisar_copias(bloques, por_id)[0]  # R6 a R8
    return hallazgos


# ¤adpa
def revisar_copias(bloques: list[Bloque], por_id: dict) -> tuple[list[str], list[str]]:
    """R6, R7 y R8: lo que el bloque copia de sus fichas. Devuelve (hallazgos, avisos)."""
    hallazgos: list[str] = []
    avisos: list[str] = []
    for b in bloques:
        if not b.con_hecho_si and b.salas is None:
            continue
        tasks = [por_id[t] for t in b.tareas if t in por_id]
        if b.con_hecho_si:  # R6
            for t in tasks:
                actual = b.hecho_si.get(t.id)
                if actual is None:
                    hallazgos.append(f"R6 {b.id}: falta la línea «Hecho si» de {t.id}")
                elif actual != _norm(t.arbitro):
                    hallazgos.append(f"R6 {b.id}: «Hecho si» de {t.id} difiere del `arbitro` de su ficha")
            for tid in b.hecho_si:
                if tid not in b.tareas:
                    hallazgos.append(f"R6 {b.id}: «Hecho si» trae {tid}, que no está en el «Objetivo»")
        for t in tasks:  # R8, títulos
            if b.titulos and b.titulos.get(t.id) != _norm(t.titulo):
                hallazgos.append(f"R8 {b.id}: el título de {t.id} en «Objetivo» difiere del de su ficha")
        if b.salas is not None:  # R8, salas
            esperadas = {s for t in tasks for s in _nombres_de_sala(t.sala)}
            if set(b.salas) != esperadas:
                hallazgos.append(f"R8 {b.id}: «Sala(s)» es {sorted(set(b.salas))} y la unión de sus tasks es {sorted(esperadas)}")
        if b.depende is not None:  # R7
            necesarias = {d for t in tasks for d in t.depende_de
                          if d in por_id and por_id[d].estado != "hecha" and d not in b.tareas}
            for d in sorted(necesarias - set(b.depende)):
                hallazgos.append(f"R7 {b.id}: «Depende de» no cita {d}, pendiente y ajena al bloque")
            for d in sorted(set(b.depende) - necesarias):
                avisos.append(f"{b.id}: «Depende de» cita {d}, que ninguna task del bloque necesita ahora")
    return hallazgos, avisos


# ¤adpa
def regenerar(briefs: str, tareas: list) -> str:
    """Reescribe las líneas «Hecho si» de cada bloque desde el `arbitro` de sus fichas; conserva los saltos de línea."""
    por_id = {t.id: t for t in tareas}
    tasks_de = {b.id: [t for t in b.tareas if t in por_id] for b in leer_bloques(briefs.replace("\r\n", "\n"))}
    lineas = briefs.splitlines(keepends=True)
    salida: list[str] = []
    i = 0
    actual = None
    while i < len(lineas):
        linea = lineas[i]
        cab = _CABECERA.match(linea.rstrip("\r\n"))
        if cab:
            actual = cab.group(1)
        salida.append(linea)
        i += 1
        if actual and linea.startswith("**Hecho si**"):
            fin = i
            while fin < len(lineas) and not lineas[fin].startswith("#"):
                fin += 1
            salida += _regenerar_region(lineas[i:fin], tasks_de.get(actual, []), por_id,
                                        "\r\n" if linea.endswith("\r\n") else "\n")
            i = fin
    return "".join(salida)


# ¤adpa
def _regenerar_region(region: list[str], ids: list[str], por_id: dict, eol: str) -> list[str]:
    nuevas = {tid: f"- `{tid}`: {_norm(por_id[tid].arbitro)}{eol}" for tid in ids}
    puestas: set[str] = set()
    res: list[str] = []
    for linea in region:
        m = _HECHO.match(linea)
        if m:
            tid = m.group(1)
            if tid in nuevas and tid not in puestas:
                res.append(nuevas[tid])
                puestas.add(tid)
            continue  # sobra o repetida
        res.append(linea)
    faltan = [nuevas[t] for t in ids if t not in puestas]
    if faltan:
        pos = next((k for k, ln in enumerate(res) if ln.startswith("- `")), None)
        if pos is None:
            pos = next((k for k, ln in enumerate(res) if k > 0 and not ln.strip()), len(res))
        res[pos:pos] = faltan
    return res


# ¤adpa
def revisar_diff(archivos: list[str], bloque: Bloque, indice) -> list[str]:
    """R5: cada archivo del diff cae dentro de «Escribe»; lo que sobra es un archivo ajeno."""
    patrones = [e.partition("#")[0] for e in bloque.escribe]
    return [f"R5 {bloque.id}: «{a}» está fuera de su «Escribe»"
            for a in archivos if not any(indice.rutas_se_solapan(a, p) for p in patrones)]


# ¤adpa
def _archivos_del_diff(rama: str, base: str) -> list[str]:
    salida = subprocess.run(["git", "diff", "--name-only", f"{base}...{rama}"], cwd=RAIZ,
                            capture_output=True, text=True, check=True).stdout
    return [l.strip() for l in salida.splitlines() if l.strip()]


# ¤adpa
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rama", help="rama cuyo diff se comprueba contra «Escribe» (R5)")
    ap.add_argument("--bloque", help="bloque de la rama (BL-xx), obligatorio con --rama")
    ap.add_argument("--base", default="main")
    ap.add_argument("--regenerar", action="store_true",
                    help="reescribe las líneas «Hecho si» desde el `arbitro` de las fichas")
    args = ap.parse_args(argv)
    indice = _cargar_indice()
    tareas, errores = indice.cargar_tareas()
    if args.regenerar:
        crudo = BRIEFS.read_bytes().decode("utf-8")
        nuevo = regenerar(crudo, tareas)
        if nuevo != crudo:
            BRIEFS.write_bytes(nuevo.encode("utf-8"))
        print("REGENERADO: líneas «Hecho si» reescritas." if nuevo != crudo else "REGENERADO: sin cambios.")
    briefs = BRIEFS.read_text(encoding="utf-8")
    hallazgos = list(errores) + revisar(briefs, tareas, indice)
    if args.rama:
        bloque = next((b for b in leer_bloques(briefs) if b.id == args.bloque), None)
        if bloque is None:
            hallazgos.append(f"R5 el bloque «{args.bloque}» no existe en los briefs")
        else:
            hallazgos += revisar_diff(_archivos_del_diff(args.rama, args.base), bloque, indice)
    if hallazgos:
        print("REPARTO NO VÁLIDO:")
        for h in hallazgos:
            print(f"  - {h}")
        return 1
    bloques = leer_bloques(briefs)
    for a in revisar_copias(bloques, {t.id: t for t in tareas})[1]:
        print(f"  aviso: {a}")
    print(f"REPARTO OK: {len(bloques)} bloques, {len({b.tanda for b in bloques})} tandas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
