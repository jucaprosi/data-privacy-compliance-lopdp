# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa
"""Árbitro del reparto en tandas: las fichas de una misma tanda no se pisan y cada una va después de lo que necesita.

GOB-06: los briefs no se versionan; la tanda es el campo opcional `tanda = N` de la ficha (R2). Función pura
`revisar(tareas, indice)`: recibe las fichas ya cargadas y devuelve la lista de hallazgos (vacía = reparto válido).
No lee el disco más que en `main`.

Comprueba, sobre las fichas no hechas que llevan `tanda`:
  R3  dos fichas de una misma tanda no comparten ningún archivo de su `propiedad` (salvo secciones reservadas distintas).
  R4  cada `depende_de` está hecha o tiene una `tanda` menor.
  R5  (con --rama) los archivos del diff de una rama caben en la `propiedad` de su ficha (--bloque es su id).
      CI-33: admite la ficha propia (salvo que pase a hecha) y las secciones por sembrar que declara.

`--tandas` imprime la vista de tandas, calculada al leer el campo `tanda` de las fichas (no escribe nada).
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


# ¤adpa
def _cargar_indice():
    ruta = Path(__file__).resolve().parent / "generar_indice_tareas.py"
    spec = importlib.util.spec_from_file_location("generar_indice_tareas", ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["generar_indice_tareas"] = modulo  # las clases de datos lo exigen antes de ejecutar el módulo
    spec.loader.exec_module(modulo)
    return modulo


# ¤adpa
def _cargar_git_diff():
    """CI-26 R2: el lector común de rutas del diff (`scripts/_git_diff.py`), cargado como los módulos hermanos."""
    ruta = Path(__file__).resolve().parent / "_git_diff.py"
    spec = importlib.util.spec_from_file_location("_git_diff", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# ¤adpa
@dataclass
class Bloque:
    """Alcance de una rama para R5: sus fichas y los archivos que puede escribir (la `propiedad` de esas fichas)."""
    id: str
    tanda: int | None
    tareas: list[str] = field(default_factory=list)
    escribe: list[str] = field(default_factory=list)


# ¤adpa
def bloque_de_ficha(tarea) -> Bloque:
    """GOB-06: el alcance de una ficha es su propia `propiedad`; ya no hay brief del que leerlo."""
    return Bloque(tarea.id, tarea.tanda, [tarea.id], list(tarea.propiedad))


# ¤adpa
def planificadas(tareas: list) -> list:
    """Las fichas no hechas con `tanda` (R2), en orden de tanda e id."""
    return sorted((t for t in tareas if t.estado != "hecha" and t.tanda is not None), key=lambda t: (t.tanda, t.id))


# ¤adpa
def revisar(tareas: list, indice) -> list[str]:
    por_id = {t.id: t for t in tareas}
    vivas = planificadas(tareas)
    hallazgos: list[str] = []

    for i, a in enumerate(vivas):  # R3
        for b in vivas[i + 1:]:
            if a.tanda != b.tanda:
                continue
            for pa in a.propiedad:
                for pb in b.propiedad:
                    if indice.propiedades_se_solapan(pa, pb):
                        hallazgos.append(f"R3 {a.id} y {b.id} (tanda {a.tanda}) escriben «{pa}» / «{pb}»")

    for t in vivas:  # R4
        for dep in t.depende_de:
            if dep not in por_id or por_id[dep].estado == "hecha":
                continue
            tanda_dep = por_id[dep].tanda
            if tanda_dep is not None and tanda_dep < t.tanda:
                continue
            donde = "sin tanda" if tanda_dep is None else f"tanda {tanda_dep}"
            hallazgos.append(f"R4 {t.id} (tanda {t.tanda}) depende de {dep} ({donde}), que no está hecha ni va antes")
    return hallazgos


_MARCAS_DE_SECCION = (("=== {} ===", "=== fin {} ==="), ("--- INICIO {} ---", "--- FIN {} ---"))


# ¤adpa
def rango_de_seccion(contenido: str, sid: str) -> tuple[int, int] | None:
    """CI-33: líneas (desde 1, ambas incluidas) de la apertura y el cierre de la sección `sid`, o None si no hay marca.

    `tiene_marca` del índice decide si la sección existe; aquí solo se calcula el rango.
    """
    if not _indice().tiene_marca(contenido, sid):
        return None
    lineas = contenido.splitlines()
    for abre, cierra in _MARCAS_DE_SECCION:
        abre, cierra = abre.format(sid), cierra.format(sid)
        inicio = next((i for i, linea in enumerate(lineas, 1) if abre in linea), None)
        if inicio is None:
            continue
        fin = next((i for i, linea in enumerate(lineas[inicio:], inicio + 1) if cierra in linea), None)
        if fin is not None:
            return inicio, fin
    return None


# ¤adpa
def _indice():
    """El módulo del índice ya cargado, o se carga una vez."""
    return sys.modules.get("generar_indice_tareas") or _cargar_indice()


_ESTADO = re.compile(r'(?m)^estado\s*=\s*"([^"]*)"')


# ¤adpa
def _estado(ficha: str | None) -> str | None:
    m = _ESTADO.search(ficha or "")
    return m.group(1) if m else None


# ¤adpa
def _secciones_declaradas(ficha: str | None, ruta: str, ids: set[str], indice) -> list[str]:
    """CI-33 R3 (a): los ids del bloque que la ficha, leída en la rama, declara como `ruta#<ID>`."""
    if not ficha:
        return []
    try:
        propiedad = indice.leer_cabecera(ficha).get("propiedad", [])
    except Exception:  # ficha ilegible en la rama: no declara nada
        return []
    return [sid for r, _, sid in (str(p).partition("#") for p in propiedad) if r == ruta and sid in ids]


# ¤adpa
def revisar_diff(archivos: list[str], bloque: Bloque, indice, leer_rama=None, lineas_cambiadas=None,
                 leer_base=None) -> list[str]:
    """R5: cada archivo del diff cae dentro de «Escribe», con las excepciones de CI-33.

    R1: la ficha propia de cada tarea del bloque entra sin declararla. R2: TASKS.md no.
    R3: un archivo fuera de «Escribe» entra si la ficha propia leída en la rama (`leer_rama`) declara `ruta#<ID>`
    de una tarea del bloque, el archivo tiene esa sección y todas sus `lineas_cambiadas(ruta)` caen dentro.
    R4: la ficha propia no pasa a `hecha` en la rama (`leer_base` lee la ficha en la base).
    Sin `leer_rama` (diff solo de nombres) se aplican R1 y la regla de «Escribe».
    """
    patrones = [e.partition("#")[0] for e in bloque.escribe]
    fichas = {f"governance/tareas/{tid}.md": tid for tid in bloque.tareas}
    ids = set(bloque.tareas)
    hallazgos: list[str] = []
    for a in archivos:
        if a in fichas:
            en_base = _estado(leer_base(a)) if leer_base else None
            if leer_rama and _estado(leer_rama(a)) == "hecha" and en_base != "hecha":
                hallazgos.append(f"R5 {fichas[a]}: «{a}» pasa a hecha; el cierre lo hace el coordinador")
            continue
        if any(indice.rutas_se_solapan(a, p) for p in patrones):
            continue
        declaradas = [] if leer_rama is None else [
            sid for f in fichas for sid in _secciones_declaradas(leer_rama(f), a, ids, indice)]
        if not declaradas:
            hallazgos.append(f"R5 {bloque.id}: «{a}» está fuera de su «Escribe»")
            continue
        contenido = leer_rama(a) or ""
        rangos = {sid: rango_de_seccion(contenido, sid) for sid in declaradas}
        validos = {sid: r for sid, r in rangos.items() if r is not None}
        if not validos:
            hallazgos.append(f"R5 {bloque.id}: «{a}» no tiene la sección {', '.join(rangos)}")
            continue
        cambiadas = lineas_cambiadas(a) if lineas_cambiadas else []
        if any(not any(i <= n <= f for i, f in validos.values()) for n in cambiadas):
            hallazgos.append(f"R5 {bloque.id}: «{a}» cambia líneas fuera de la sección {', '.join(validos)}")
    return hallazgos


# ¤adpa
def _archivos_del_diff(rama: str, base: str) -> list[str]:
    return _cargar_git_diff().archivos_del_diff(base, rama, RAIZ)


# ¤adpa
def revisar_rama(rama: str, base: str, bloque: Bloque, indice) -> list[str]:
    """R5 sobre una rama real: el lector común da el diff, las líneas y el contenido de cada lado (CI-33)."""
    git = _cargar_git_diff()
    return revisar_diff(git.archivos_del_diff(base, rama, RAIZ), bloque, indice,
                        leer_rama=lambda ruta: git.contenido_en(rama, RAIZ, ruta),
                        lineas_cambiadas=lambda ruta: git.lineas_cambiadas(base, rama, RAIZ, ruta),
                        leer_base=lambda ruta: git.contenido_en(base, RAIZ, ruta))


# ¤adpa
def vista_de_tandas(tareas: list) -> list[str]:
    """Una línea por tanda, en orden, con las fichas no hechas que la llevan. Se calcula al leer; no se guarda."""
    por_tanda: dict[int, list[str]] = {}
    for t in planificadas(tareas):
        por_tanda.setdefault(t.tanda, []).append(t.id)
    return [f"Tanda {n}: {', '.join(ids)}" for n, ids in sorted(por_tanda.items())]


# ¤adpa
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rama", help="rama cuyo diff se comprueba contra la `propiedad` de su ficha (R5)")
    ap.add_argument("--bloque", help="id de la ficha de la rama, obligatorio con --rama")
    ap.add_argument("--base", default="main")
    ap.add_argument("--tandas", action="store_true", help="imprime la vista de tandas leída de las fichas (no escribe)")
    args = ap.parse_args(argv)
    indice = _cargar_indice()
    tareas, errores = indice.cargar_tareas()
    hallazgos = list(errores) + revisar(tareas, indice)
    if args.rama:
        ficha = next((t for t in tareas if t.id == args.bloque), None)
        if ficha is None:
            hallazgos.append(f"R5 la ficha «{args.bloque}» no existe")
        else:
            hallazgos += revisar_rama(args.rama, args.base, bloque_de_ficha(ficha), indice)
    if hallazgos:
        print("REPARTO NO VÁLIDO:")
        for h in hallazgos:
            print(f"  - {h}")
        return 1
    vivas = planificadas(tareas)
    if args.tandas:
        for linea in vista_de_tandas(tareas):
            print(linea)
    print(f"REPARTO OK: {len(vivas)} fichas planificadas, {len({t.tanda for t in vivas})} tandas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
