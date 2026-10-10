"""Valida las especificaciones de tareas y genera el índice de TASKS.md.

Fuente de verdad: una especificación por tarea en governance/tareas/<ID>.md, con una
cabecera TOML entre dos líneas '+++'. El índice de governance/artefactos/TASKS.md se
GENERA desde ellas (entre dos marcas) y solo contiene lo estable (id, título, ola, sala y
dependencias): el ESTADO vive únicamente en la especificación de cada tarea, de modo que
cambiarlo no obliga a editar ningún archivo común. La independencia entre tareas se
COMPRUEBA en lugar de afirmarse:

* ids únicos, dependencias existentes y sin ciclos;
* dos tareas que pueden ejecutarse a la vez (ninguna es ancestro de la otra) no pueden
  poseer el mismo archivo. Una entrada «archivo#SECCION» posee solo esa sección reservada
  del archivo, de modo que varias tareas compartan una compuerta sin pisarse.

Uso:
    python scripts/generar_indice_tareas.py --verificar   # código 1 si hay errores o índice viejo
    python scripts/generar_indice_tareas.py --escribir    # regenera el índice en TASKS.md
    python scripts/generar_indice_tareas.py --estado      # imprime el estado de cada tarea
"""
from __future__ import annotations

import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_TAREAS = RAIZ / "governance" / "tareas"
TASKS_MD = RAIZ / "governance" / "artefactos" / "TASKS.md"

INICIO = "<!-- INDICE-TAREAS:INICIO (generado por scripts/generar_indice_tareas.py; no editar a mano) -->"
FIN = "<!-- INDICE-TAREAS:FIN -->"

ESTADOS = ("pendiente", "en_curso", "hecha", "bloqueada")
OLAS = ("A", "B", "C", "D", "E", "indep", "backlog")
CAMPOS = ("id", "titulo", "ola", "estado", "sala", "depende_de", "propiedad", "arbitro")


@dataclass(frozen=True)
class Tarea:
    id: str
    titulo: str
    ola: str
    estado: str
    sala: str
    depende_de: tuple[str, ...]
    propiedad: tuple[str, ...]
    arbitro: str
    archivo: str = ""


# --------------------------------------------------------------------------- lectura

def leer_cabecera(texto: str) -> dict:
    lineas = texto.replace("\r\n", "\n").split("\n")
    if not lineas or lineas[0].strip() != "+++":
        raise ValueError("falta la cabecera '+++' al inicio")
    try:
        fin = lineas.index("+++", 1)
    except ValueError:
        raise ValueError("la cabecera no se cierra con '+++'") from None
    return tomllib.loads("\n".join(lineas[1:fin]))


def cargar_tareas(directorio: Path = DIR_TAREAS) -> tuple[list[Tarea], list[str]]:
    tareas: list[Tarea] = []
    errores: list[str] = []
    for ruta in sorted(directorio.glob("*.md")):
        if ruta.name.lower() == "readme.md":
            continue
        try:
            datos = leer_cabecera(ruta.read_text(encoding="utf-8"))
        except Exception as exc:  # cabecera ilegible: se informa, no se aborta
            errores.append(f"{ruta.name}: {exc}")
            continue
        faltan = [c for c in CAMPOS if c not in datos]
        if faltan:
            errores.append(f"{ruta.name}: faltan campos {faltan}")
            continue
        tareas.append(Tarea(
            id=str(datos["id"]), titulo=str(datos["titulo"]), ola=str(datos["ola"]),
            estado=str(datos["estado"]), sala=str(datos["sala"]),
            depende_de=tuple(datos["depende_de"]), propiedad=tuple(datos["propiedad"]),
            arbitro=str(datos["arbitro"]), archivo=ruta.name,
        ))
        if ruta.stem != datos["id"]:
            errores.append(f"{ruta.name}: el nombre del archivo debe ser {datos['id']}.md")
    return tareas, errores


# --------------------------------------------------------------------------- solapamiento

_COMODINES = "*?["


def _tiene_comodin(ruta: str) -> bool:
    return any(c in ruta for c in _COMODINES)


def _prefijo(ruta: str) -> str:
    posiciones = [ruta.index(c) for c in _COMODINES if c in ruta]
    return ruta[: min(posiciones)] if posiciones else ruta


def _sufijo(ruta: str) -> str:
    posiciones = [ruta.rindex(c) for c in _COMODINES if c in ruta]
    return ruta[max(posiciones) + 1:] if posiciones else ruta


def _regex(glob: str) -> re.Pattern[str]:
    salida, i = [], 0
    while i < len(glob):
        if glob[i:i + 2] == "**":
            salida.append(".*")
            i += 2
            continue
        c = glob[i]
        salida.append("[^/]*" if c == "*" else "[^/]" if c == "?" else re.escape(c))
        i += 1
    return re.compile("^" + "".join(salida) + "$")


def rutas_se_solapan(a: str, b: str) -> bool:
    """¿Pueden dos patrones de ruta designar un mismo archivo? Conservador entre dos comodines."""
    ca, cb = _tiene_comodin(a), _tiene_comodin(b)
    if not ca and not cb:
        return a == b
    if not ca:
        return bool(_regex(b).match(a))
    if not cb:
        return bool(_regex(a).match(b))
    pa, pb, sa, sb = _prefijo(a), _prefijo(b), _sufijo(a), _sufijo(b)
    return (pa.startswith(pb) or pb.startswith(pa)) and (sa.endswith(sb) or sb.endswith(sa))


def propiedades_se_solapan(p: str, q: str) -> bool:
    """Compara dos entradas de «propiedad», que pueden llevar una sección reservada tras '#'."""
    fa, _, sa = p.partition("#")
    fb, _, sb = q.partition("#")
    if not rutas_se_solapan(fa, fb):
        return False
    return not (fa == fb and sa and sb and sa != sb)


# --------------------------------------------------------------------------- validación

def _ancestros(tareas: list[Tarea]) -> dict[str, set[str]]:
    por_id = {t.id: t for t in tareas}
    memo: dict[str, set[str]] = {}

    def recorrer(tid: str, visitando: frozenset[str]) -> set[str]:
        if tid in memo:
            return memo[tid]
        acumulado: set[str] = set()
        for d in por_id[tid].depende_de:
            if d in por_id and d not in visitando:
                acumulado |= {d} | recorrer(d, visitando | {tid})
        memo[tid] = acumulado
        return acumulado

    return {t.id: recorrer(t.id, frozenset()) for t in tareas}


def _ciclos(tareas: list[Tarea]) -> list[str]:
    por_id = {t.id: t for t in tareas}
    estado: dict[str, int] = {}
    ciclos: list[str] = []

    def visitar(tid: str, camino: list[str]) -> None:
        estado[tid] = 1
        for d in por_id[tid].depende_de:
            if d not in por_id:
                continue
            if estado.get(d) == 1:
                ciclos.append(" → ".join(camino + [tid, d]))
            elif d not in estado:
                visitar(d, camino + [tid])
        estado[tid] = 2

    for t in tareas:
        if t.id not in estado:
            visitar(t.id, [])
    return ciclos


def validar(tareas: list[Tarea]) -> list[str]:
    errores: list[str] = []
    vistos: set[str] = set()
    for t in tareas:
        if t.id in vistos:
            errores.append(f"{t.id}: id duplicado")
        vistos.add(t.id)
        if t.estado not in ESTADOS:
            errores.append(f"{t.id}: estado inválido «{t.estado}» (válidos: {', '.join(ESTADOS)})")
        if t.ola not in OLAS:
            errores.append(f"{t.id}: ola inválida «{t.ola}» (válidas: {', '.join(OLAS)})")
        if not t.propiedad:
            errores.append(f"{t.id}: debe declarar al menos un archivo de su propiedad")
        if not t.arbitro.strip():
            errores.append(f"{t.id}: debe declarar su árbitro")
        for d in t.depende_de:
            if d not in {x.id for x in tareas}:
                errores.append(f"{t.id}: depende de «{d}», que no existe")
    errores += [f"ciclo de dependencias: {c}" for c in _ciclos(tareas)]
    if errores:
        return errores

    ancestros = _ancestros(tareas)
    for i, a in enumerate(tareas):
        for b in tareas[i + 1:]:
            if b.id in ancestros[a.id] or a.id in ancestros[b.id]:
                continue  # una espera a la otra: pueden compartir archivos
            for pa in a.propiedad:
                for pb in b.propiedad:
                    if propiedades_se_solapan(pa, pb):
                        errores.append(f"{a.id} y {b.id} pueden ejecutarse a la vez y ambas poseen «{pa}» / «{pb}»")
    return errores


# --------------------------------------------------------------------------- índice

def generar_indice(tareas: list[Tarea]) -> str:
    orden = {o: i for i, o in enumerate(OLAS)}
    ordenadas = sorted(tareas, key=lambda t: (orden.get(t.ola, 99), t.id))
    filas = ["| ID | Tarea | Ola | Sala | Depende de |", "| :--- | :--- | :--- | :--- | :--- |"]
    for t in ordenadas:
        filas.append(
            f"| [{t.id}](../tareas/{t.id}.md) | {t.titulo} | {t.ola} | `{t.sala}` | "
            f"{', '.join(t.depende_de) or '—'} |"
        )
    cabecera = (f"**{len(ordenadas)} tareas.** El estado de cada una está en su especificación "
                "(`python scripts/generar_indice_tareas.py --estado`).")
    return "\n".join([INICIO, cabecera, "", *filas, FIN])


def resumen_estado(tareas: list[Tarea]) -> str:
    orden = {o: i for i, o in enumerate(OLAS)}
    lineas = [f"{t.ola:8} {t.id:8} {t.estado:10} {t.titulo}" for t in
              sorted(tareas, key=lambda t: (orden.get(t.ola, 99), t.id))]
    cuentas = ", ".join(f"{sum(1 for t in tareas if t.estado == e)} {e}" for e in ESTADOS
                        if any(t.estado == e for t in tareas))
    return "\n".join([*lineas, "", f"{len(tareas)} tareas: {cuentas}"])


def extraer_indice(texto: str) -> str | None:
    t = texto.replace("\r\n", "\n")
    if INICIO not in t or FIN not in t:
        return None
    return t[t.index(INICIO): t.index(FIN) + len(FIN)]


def aplicar_indice(texto: str, indice: str) -> str:
    fin_linea = "\r\n" if "\r\n" in texto else "\n"
    t = texto.replace("\r\n", "\n")
    actual = extraer_indice(t)
    if actual is None:
        raise ValueError("TASKS.md no tiene las marcas del índice")
    return t.replace(actual, indice, 1).replace("\n", fin_linea)


def main(argv: list[str]) -> int:
    tareas, errores = cargar_tareas()
    errores += validar(tareas)
    if "--estado" in argv:
        print(resumen_estado(tareas))
        return 1 if errores else 0
    with open(TASKS_MD, encoding="utf-8", newline="") as f:
        texto = f.read()
    indice = generar_indice(tareas)
    if "--escribir" in argv and not errores:
        with open(TASKS_MD, "w", encoding="utf-8", newline="") as f:
            f.write(aplicar_indice(texto, indice))
        print(f"Índice regenerado: {len(tareas)} tareas.")
        return 0
    if extraer_indice(texto) != indice:
        errores.append("el índice de TASKS.md está desactualizado: ejecute --escribir")
    for e in errores:
        print("ERROR:", e)
    if not errores:
        print(f"OK: {len(tareas)} tareas, independencia verificada.")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
