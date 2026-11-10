"""NEON-00 · Árbitro sin Neon.

`main` es solo EVYDENTIA: la palabra «neon» (sin distinguir mayúsculas) no puede aparecer en
el repositorio rastreado salvo en tres sitios, todos cerrados y que solo pueden decrecer:

1. la lista blanca `tests/sin_neon/permitidos.txt` (`archivo|motivo`; acepta globs);
2. las fichas de `governance/tareas/*.md` con estado `hecha` (la historia se conserva);
3. los pendientes `tests/sin_neon/pendientes/<ID>.txt` (`archivo:línea`), uno por ficha dueña
   de la limpieza. Cada dueña retira sus líneas al corregir.

Una mención en cualquier otro lugar deja la prueba en rojo. En las fichas de `governance/tareas/`
el identificador de ficha `NEON-NN` no cuenta como mención: es un nombre de tarea, no el proveedor.
Sin `import yaml`; no toca la red ni recursos de Neon.
"""
from __future__ import annotations

import fnmatch
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_LISTAS = RAIZ / "tests" / "sin_neon"
PERMITIDOS = DIR_LISTAS / "permitidos.txt"
DIR_PENDIENTES = DIR_LISTAS / "pendientes"

FICHAS_DUENAS = ("NEON-01", "NEON-02", "NEON-03", "NEON-04", "FIRMA-02")

# Recuento escrito en la prueba: las listas solo pueden decrecer. Al retirar líneas, la dueña
# baja el número aquí en el mismo PR; subirlo es justo el cambio que el árbitro impide.
MAX_PERMITIDOS = 22
MAX_PENDIENTES = {"NEON-01": 62, "NEON-02": 46, "NEON-03": 11, "NEON-04": 238, "FIRMA-02": 1}

PATRON = re.compile(r"neon", re.IGNORECASE)
ID_FICHA = re.compile(r"NEON-\d{2}", re.IGNORECASE)
PREFIJO_FICHAS = "governance/tareas/"


def leer_menciones() -> list[tuple[str, int, str]]:
    """`git grep -n -i neon` sobre los archivos rastreados: (archivo, línea, texto)."""
    r = subprocess.run(
        ["git", "-c", "core.quotepath=false", "grep", "-n", "-i", "neon"],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert r.returncode in (0, 1), r.stderr
    salida = []
    for linea in r.stdout.splitlines():
        ruta, n, texto = linea.split(":", 2)
        salida.append((ruta, int(n), texto))
    return salida


def leer_permitidos(texto: str) -> list[tuple[str, str]]:
    filas = []
    for crudo in texto.splitlines():
        crudo = crudo.strip()
        if not crudo or crudo.startswith("#"):
            continue
        archivo, _, motivo = crudo.partition("|")
        filas.append((archivo.strip(), motivo.strip()))
    return filas


def leer_pendientes(texto: str) -> set[tuple[str, int]]:
    pares = set()
    for crudo in texto.splitlines():
        crudo = crudo.strip()
        if not crudo or crudo.startswith("#"):
            continue
        archivo, _, n = crudo.rpartition(":")
        pares.add((archivo, int(n)))
    return pares


def fichas_hechas() -> set[str]:
    spec = importlib.util.spec_from_file_location("_indice_tareas_neon00", RAIZ / "scripts" / "generar_indice_tareas.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_indice_tareas_neon00"] = mod  # los dataclasses lo exigen
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    tareas, _ = mod.cargar_tareas()
    return {f"{PREFIJO_FICHAS}{t.id}.md" for t in tareas if t.estado == "hecha"}


def _coincide(ruta: str, patron: str) -> bool:
    return ruta == patron or fnmatch.fnmatchcase(ruta, patron.replace("**", "*"))


def evaluar(menciones, permitidos, pendientes, hechas) -> list[str]:
    """Devuelve las menciones que ninguna lista cubre, como «archivo:línea: texto»."""
    patrones = [a for a, _ in permitidos]
    sueltas = []
    for ruta, n, texto in menciones:
        if ruta in hechas or any(_coincide(ruta, p) for p in patrones):
            continue
        if ruta.startswith(PREFIJO_FICHAS) and not PATRON.search(ID_FICHA.sub("", texto)):
            continue
        if any((ruta, n) in pares for pares in pendientes.values()):
            continue
        sueltas.append(f"{ruta}:{n}: {texto.strip()[:100]}")
    return sueltas


def problemas_de_listas(permitidos, pendientes_por_ficha, contiene, *,
                        max_permitidos: int | None = None,
                        max_pendientes: dict[str, int] | None = None) -> list[str]:
    """Errores estructurales: IDs desconocidos, recuentos que crecen y brief ya cumplido."""
    tope_p = MAX_PERMITIDOS if max_permitidos is None else max_permitidos
    topes = MAX_PENDIENTES if max_pendientes is None else max_pendientes
    errores = []
    for ficha in pendientes_por_ficha:
        if ficha not in FICHAS_DUENAS:
            errores.append(f"pendientes/{ficha}.txt: ID desconocido (válidos: {', '.join(FICHAS_DUENAS)})")
    if len(permitidos) > tope_p:
        errores.append(f"permitidos.txt crece: {len(permitidos)} > {tope_p}")
    for ficha, pares in pendientes_por_ficha.items():
        if len(pares) > topes.get(ficha, 0):
            errores.append(f"pendientes/{ficha}.txt crece: {len(pares)} > {topes.get(ficha, 0)}")
    for archivo, motivo in permitidos:
        if motivo.startswith("pendiente: brief") and not contiene(archivo):
            errores.append(f"{archivo}: ya no contiene «neon»; retire su línea «pendiente: brief» de permitidos.txt")
    return errores


def _cargar_listas():
    permitidos = leer_permitidos(PERMITIDOS.read_text(encoding="utf-8"))
    pendientes = {p.stem: leer_pendientes(p.read_text(encoding="utf-8"))
                  for p in sorted(DIR_PENDIENTES.glob("*.txt"))}
    return permitidos, pendientes


def _contiene(ruta: str) -> bool:
    p = RAIZ / ruta
    return p.is_file() and bool(PATRON.search(p.read_text(encoding="utf-8", errors="replace")))


def test_sin_menciones_fuera_de_las_listas():
    permitidos, pendientes = _cargar_listas()
    sueltas = evaluar(leer_menciones(), permitidos, pendientes, fichas_hechas())
    assert not sueltas, "Menciones a Neon fuera de las listas:\n" + "\n".join(sueltas[:40])


def test_listas_cerradas_y_sin_crecer():
    permitidos, pendientes = _cargar_listas()
    errores = problemas_de_listas(permitidos, pendientes, _contiene)
    assert not errores, "\n".join(errores)


# ---- Mutaciones M1 a M4 sobre datos simulados ----------------------------------------------

def test_m1_mencion_nueva_en_archivo_vigente_falla():
    base = [("app_core/x.py", 3, "# conecta a Neon")]
    assert evaluar(base, [], {}, set())
    assert not evaluar(base, [("app_core/x.py", "motivo")], {}, set())
    assert not evaluar(base, [], {"NEON-01": {("app_core/x.py", 3)}}, set())
    assert evaluar(base, [], {"NEON-01": {("app_core/x.py", 4)}}, set())


def test_m2_linea_nueva_en_permitidos_falla():
    errores = problemas_de_listas([("a.py", "m")] * (MAX_PERMITIDOS + 1), {}, lambda _: True)
    assert any("permitidos.txt crece" in e for e in errores)


def test_m3_pendientes_de_id_desconocido_falla():
    errores = problemas_de_listas([], {"OTRA": {("a.py", 1)}}, lambda _: True)
    assert any("ID desconocido" in e for e in errores)


def test_m4_brief_cumplido_sin_retirar_la_linea_falla():
    fila = [("verificadores/README.md", "pendiente: brief NEON-04")]
    errores = problemas_de_listas(fila, {}, lambda _: False, max_permitidos=99)
    assert any("ya no contiene" in e for e in errores)
    assert not problemas_de_listas(fila, {}, lambda _: True, max_permitidos=99)


def test_pendientes_que_crecen_fallan():
    errores = problemas_de_listas([], {"NEON-01": {("a", 1), ("b", 2)}}, lambda _: True,
                                  max_pendientes={"NEON-01": 1})
    assert any("crece" in e for e in errores)


def test_id_de_ficha_y_fichas_hechas_no_cuentan():
    ficha = [("governance/tareas/IA-08.md", 7, 'depende_de = ["NEON-02"]')]
    assert not evaluar(ficha, [], {}, set())
    proveedor = [("governance/tareas/IA-08.md", 7, "usa la base de Neon")]
    assert evaluar(proveedor, [], {}, set())
    assert not evaluar(proveedor, [], {}, {"governance/tareas/IA-08.md"})
    assert evaluar([("docs/x.md", 1, "NEON-02")], [], {}, set())
