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

import difflib
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

RAIZ = Path(__file__).resolve().parent.parent
DIR_TAREAS = RAIZ / "governance" / "tareas"
TASKS_MD = RAIZ / "governance" / "artefactos" / "TASKS.md"
PRD_MD = RAIZ / "governance" / "artefactos" / "PRD.md"
EXENCIONES = DIR_TAREAS / "_exenciones_propiedad.txt"

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
    crea: tuple[str, ...] = ()      # ADPA-10: archivos que la ficha crea (sin «#ID»)
    siembra: tuple[str, ...] = ()   # ADPA-10: marcas «ruta#ID» que deja para fichas posteriores


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
            crea=tuple(datos.get("crea", ())), siembra=tuple(datos.get("siembra", ())),
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


def salas_del_prd(texto: str) -> set[str]:
    """Salas del catálogo del PRD de EVYDENTIA: solo la tabla del apartado 5.2."""
    t = texto.replace("\r\n", "\n")
    ini = t.find("### 5.2")
    if ini < 0:
        return set()
    salas: set[str] = set()
    en_tabla = False
    for linea in t[ini:].split("\n")[1:]:
        if linea.startswith("|"):
            en_tabla = True
            m = re.match(r"\|\s*`([a-z0-9_]+)`\s*\|", linea)
            if m:
                salas.add(m.group(1))
        elif en_tabla:
            break
    return salas


def validar(tareas: list[Tarea], salas: set[str] | None = None, *,
            arbol: set[str] | None = None, leer: Callable[[str], str] | None = None,
            exenciones: list[tuple[str, str, str]] | None = None, base: str = "HEAD",
            avisos: list[str] | None = None, texto_exenciones: str | None = None) -> list[str]:
    errores: list[str] = []
    if texto_exenciones is not None:  # CI-22
        errores += validar_secciones(texto_exenciones, tareas)
    vistos: set[str] = set()
    for t in tareas:
        if t.id in vistos:
            errores.append(f"{t.id}: id duplicado")
        vistos.add(t.id)
        if salas is not None:
            for sala in (s.strip() for s in t.sala.split(",")):
                if sala not in salas:
                    errores.append(f"{t.id}: la sala «{sala}» no existe en el catálogo del PRD (apartado 5.2)")
        if t.estado not in ESTADOS:
            errores.append(f"{t.id}: estado inválido «{t.estado}» (válidos: {', '.join(ESTADOS)})")
        if t.ola not in OLAS:
            errores.append(f"{t.id}: ola inválida «{t.ola}» (válidas: {', '.join(OLAS)})")
        if not t.propiedad:
            errores.append(f"{t.id}: debe declarar al menos un archivo de su propiedad")
        if not t.arbitro.strip():
            errores.append(f"{t.id}: debe declarar su árbitro")
        for entrada in t.propiedad:  # Aporte 129: «carpeta/» se compararía por texto y ocultaría choques
            if entrada.partition("#")[0].endswith("/"):
                errores.append(f"{t.id}: la propiedad «{entrada}» termina en «/»; use «carpeta/**» o archivos concretos")
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
    if arbol is not None:  # ADPA-10 · R-PROP-EXISTE
        hallazgos = validar_contra_arbol(tareas, arbol, leer or (lambda _r: ""), base)
        errores += aplicar_exenciones(hallazgos, exenciones or [])
        if avisos is not None:
            avisos += [h.mensaje for h in hallazgos if h.nivel == "aviso"]
    return errores


# --------------------------------------------------------------------------- R-PROP-EXISTE (ADPA-10)
# Cada entrada de propiedad existe en la base comparada, la crea la propia ficha («crea») o la
# crea y siembra una ficha ancestro («crea» + «siembra»). Diseño:
# governance/apoyo/DISENO_PROPIEDAD_CONTRA_ARBOL.md §2 (reglas 1 a 4) y §5 (fase 1).

@dataclass(frozen=True)
class Hallazgo:
    ficha: str
    entrada: str
    nivel: str      # «error» o «aviso» (fase 1: la creación implícita y el comodín sin base avisan)
    mensaje: str


def tiene_marca(contenido: str, sid: str) -> bool:
    return f"=== {sid} ===" in contenido or f"--- INICIO {sid} ---" in contenido


def _directorios(arbol: set[str]) -> set[str]:
    dirs: set[str] = set()
    for r in arbol:
        partes = r.split("/")[:-1]
        for i in range(1, len(partes) + 1):
            dirs.add("/".join(partes[:i]))
    return dirs


def sugerir_ruta(f: str, arbol: set[str], dirs: set[str] | None = None) -> str | None:
    """Ruta real probable para «f», que no existe: directorio intermedio olvidado o nombre parecido."""
    dirs = _directorios(arbol) if dirs is None else dirs
    partes = f.split("/")
    k = len(partes) - 1
    while k > 0 and "/".join(partes[:k]) not in dirs:
        k -= 1
    if k < len(partes) - 1:  # falta al menos un directorio: buscarlo dentro del ancestro existente
        ancestro, falta, resto = "/".join(partes[:k]), partes[k], partes[k + 1:]
        pref = ancestro + "/" if ancestro else ""
        candidatos = sorted((d for d in dirs if d.startswith(pref) and d.rsplit("/", 1)[-1] == falta
                             and d != pref + falta), key=lambda d: (d.count("/"), d))
        for d in candidatos:
            propuesta = "/".join([d, *resto])
            if propuesta in arbol or "/".join([d, *resto[:-1]]) in dirs:
                return propuesta
    if len(partes) > 1 and "/".join(partes[:-1]) not in dirs:
        return None  # carpeta padre inexistente y sin directorio olvidado: sala nueva, solo aviso
    nombre = partes[-1]
    mismos = sorted(r for r in arbol if r.rsplit("/", 1)[-1] == nombre)
    for r in mismos:  # un directorio de más o de menos: «api/main.py» → «main.py»
        otras = r.split("/")
        corta, larga = (otras, partes) if len(otras) < len(partes) else (partes, otras)
        if len(larga) - len(corta) == 1 and any(larga[:i] + larga[i + 1:] == corta for i in range(len(larga) - 1)):
            return r
    cercanas = difflib.get_close_matches(f, mismos, n=1, cutoff=0.9)
    return cercanas[0] if cercanas else None


def validar_contra_arbol(tareas: list[Tarea], arbol: set[str], leer: Callable[[str], str],
                         base: str = "HEAD") -> list[Hallazgo]:
    """Reglas 1 a 4 de R-PROP-EXISTE. «arbol» y «leer» se inyectan (en CI: git ls-tree de HEAD)."""
    vivas = [t for t in tareas if t.estado != "hecha"]
    if not vivas:
        return [Hallazgo("", "", "error", f"Base: {base}, 0 fichas no hechas: no hay nada que comparar")]
    por_id = {t.id: t for t in tareas}
    anc = _ancestros(tareas)
    dirs = _directorios(arbol)
    cache: dict[str, str] = {}
    h: list[Hallazgo] = []

    def contenido(f: str) -> str:
        if f not in cache:
            cache[f] = leer(f)
        return cache[f]

    def err(t: Tarea, e: str, msg: str, nivel: str = "error") -> None:
        h.append(Hallazgo(t.id, e, nivel, f"{t.id}: {msg}"))

    def no_existe(t: Tarea, e: str, f: str, sug: str | None, cola: str) -> None:
        extra = f"; ¿quiso decir «{sug}»?" if sug else ""
        err(t, e, f"«{f}» no existe en {base}{extra} {cola}")

    for t in vivas:
        ancestros = [por_id[a] for a in anc[t.id]]
        for e in t.propiedad:
            f, _, sid = e.partition("#")
            if _tiene_comodin(f):  # regla 2
                pref = _prefijo(f)
                pref = pref[: pref.rfind("/") + 1]
                creadas = [c for u in [t, *ancestros] for c in u.crea]
                if pref and pref.rstrip("/") not in dirs and not any(c.startswith(pref) for c in creadas):
                    err(t, e, f"el comodín «{f}» parte de «{pref}», que no existe en {base} ni lo crea "
                              "la ficha o una ancestro", "aviso")
                continue
            if f in arbol:  # regla 1a
                if sid and not tiene_marca(contenido(f), sid) and not any(e in u.siembra for u in ancestros):
                    err(t, e, f"«{f}» no tiene la marca «=== {sid} ===» en {base} ni la siembra una ancestro")
                continue
            creadora = next((u for u in ancestros if f in u.crea), None)  # regla 1b
            if sid:
                if creadora is None:
                    no_existe(t, e, f, sugerir_ruta(f, arbol, dirs),
                              "y ninguna ancestro lo declara en su «crea». Si lo crea otra ficha, "
                              "declárelo en su «crea» y «siembra» y dependa de ella.")
                elif e not in creadora.siembra:
                    err(t, e, f"{creadora.id} crea «{f}» pero no siembra «{e}»")
                continue
            if f in t.crea or creadora is not None:
                continue
            sug = sugerir_ruta(f, arbol, dirs)
            if sug:
                no_existe(t, e, f, sug, "Si la crea otra ficha, declárela en su «crea» y dependa de ella.")
            else:
                err(t, e, f"«{f}» no existe en {base}: creación implícita, declárela en «crea»", "aviso")

    creadoras: dict[str, list[str]] = {}
    for t in vivas:  # regla 3
        for c in t.crea:
            creadoras.setdefault(c, []).append(t.id)
            if "#" in c or c not in t.propiedad:
                err(t, c, f"«{c}» figura en «crea» y debe estar en su propiedad, sin «#ID»")
            if c in arbol and t.estado == "pendiente":  # en curso: su propio PR ya lo trae
                err(t, c, f"crea «{c}», que ya existe en {base}")
    for c, ids in creadoras.items():
        if len(ids) > 1:
            for tid in ids:
                h.append(Hallazgo(tid, c, "error", f"{tid}: «{c}» tiene varias creadoras: {', '.join(ids)}"))

    for u in vivas:  # regla 4
        for s in u.siembra:
            f, _, sid = s.partition("#")
            if not sid:
                err(u, s, f"«{s}» en «siembra» debe tener la forma «ruta#ID»")
                continue
            if f not in u.crea and f not in u.propiedad:
                err(u, s, f"siembra «{s}» pero no posee «{f}» entero (créelo o poséalo sin «#ID»)")
            if sid not in por_id or u.id not in anc[sid]:
                err(u, s, f"siembra «{s}» para {sid}, que no depende de {u.id}")
    return h


def leer_exenciones(texto: str) -> list[tuple[str, str, str]]:
    salida = []
    for linea in texto.replace("\r\n", "\n").split("\n"):
        if not linea.strip() or linea.lstrip().startswith("#"):
            continue
        ficha, entrada, motivo = (linea.split("|", 2) + ["", ""])[:3]
        salida.append((ficha.strip(), entrada.strip(), motivo.strip()))
    return salida


_MARCA = re.compile(r"^#\s*---\s*(INICIO|FIN)\s+(\S+)\s*---\s*$")


# ¤arbitro
def validar_secciones(texto: str, tareas: list[Tarea]) -> list[str]:
    """CI-22: secciones «# --- INICIO X --- / # --- FIN X ---» del archivo de exenciones.

    1. pares completos y sin cruzarse; 2. el ID existe; 3. dentro de la sección de X solo hay líneas
    «X|»; 4. si X tiene sección, ninguna línea «X|» queda fuera; 5. la sección de una ficha hecha no
    está vacía (el Tech Lead borra el par al cerrarla).
    """
    estados = {t.id: t.estado for t in tareas}
    errores: list[str] = []
    abierta: str | None = None
    secciones: dict[str, int] = {}  # ID -> líneas dentro
    fuera: list[tuple[int, str]] = []
    for n, linea in enumerate(texto.replace("\r\n", "\n").split("\n"), 1):
        marca = _MARCA.match(linea.strip())
        if marca:
            tipo, sid = marca.groups()
            if tipo == "INICIO":
                if abierta is not None:
                    errores.append(f"exenciones l.{n}: INICIO {sid} dentro de la sección {abierta} sin cerrar")
                if sid in secciones:
                    errores.append(f"exenciones l.{n}: la sección {sid} está repetida")
                if sid not in estados:
                    errores.append(f"exenciones l.{n}: la sección {sid} no corresponde a ninguna ficha")
                abierta = sid
                secciones.setdefault(sid, 0)
            elif abierta != sid:
                errores.append(f"exenciones l.{n}: FIN {sid} sin su INICIO"
                               + (f" (está abierta {abierta})" if abierta else ""))
            else:
                abierta = None
            continue
        if not linea.strip() or linea.lstrip().startswith("#"):
            continue
        ficha = linea.split("|", 1)[0].strip()
        if abierta is None:
            fuera.append((n, ficha))
        elif ficha != abierta:
            errores.append(f"exenciones l.{n}: línea de {ficha} dentro de la sección {abierta}")
        else:
            secciones[abierta] += 1
    if abierta is not None:
        errores.append(f"exenciones: la sección {abierta} no tiene FIN")
    for n, ficha in fuera:
        if ficha in secciones:
            errores.append(f"exenciones l.{n}: línea de {ficha} fuera de su sección")
    for sid, lineas in secciones.items():
        if lineas == 0 and estados.get(sid) == "hecha":
            errores.append(f"exenciones: la sección de {sid} está vacía y la ficha está hecha; "
                           "borre su par de marcas")
    return errores


def aplicar_exenciones(hallazgos: Iterable[Hallazgo], exenciones: list[tuple[str, str, str]]) -> list[str]:
    """Quita los errores exentos. La lista solo decrece: falla la exención que no tapa ningún error."""
    errores_h = [x for x in hallazgos if x.nivel == "error"]
    claves = {(f, e) for f, e, _ in exenciones}
    vivos = {(x.ficha, x.entrada) for x in errores_h}
    salida = [x.mensaje for x in errores_h if (x.ficha, x.entrada) not in claves]
    for f, e, _ in exenciones:
        if (f, e) not in vivos:
            salida.append(f"la exención «{f}|{e}» ya no tapa ningún error (resuelta o nueva); "
                          "retírela de governance/tareas/_exenciones_propiedad.txt")
    return salida


def exenciones_nuevas(antes: list[tuple[str, str, str]], despues: list[tuple[str, str, str]]) -> list[str]:
    """La lista solo decrece: toda clave de «despues» tiene que estar en «antes»."""
    previas = {(f, e) for f, e, _ in antes}
    return [f"exención nueva no permitida: «{f}|{e}»; la lista solo puede decrecer"
            for f, e, _ in despues if (f, e) not in previas]


def arbol_git(raiz: Path = RAIZ, rev: str = "HEAD") -> tuple[set[str], Callable[[str], str], str]:
    sha = subprocess.run(["git", "rev-parse", "--short", rev], cwd=raiz, capture_output=True,
                         text=True, check=True).stdout.strip()
    salida = subprocess.run(["git", "ls-tree", "-r", "-z", "--name-only", rev], cwd=raiz,
                            capture_output=True, check=True).stdout.decode("utf-8")
    arbol = {r for r in salida.split("\0") if r}

    def leer(ruta: str) -> str:
        r = subprocess.run(["git", "show", f"{rev}:{ruta}"], cwd=raiz, capture_output=True)
        return r.stdout.decode("utf-8", errors="replace") if r.returncode == 0 else ""

    return arbol, leer, f"{rev} {sha}"


def exenciones_en(raiz: Path, rev: str) -> list[tuple[str, str, str]] | None:
    """Lista de exenciones en otra revisión (p. ej. origin/main), o None si no está."""
    rel = EXENCIONES.relative_to(RAIZ).as_posix()
    r = subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=raiz, capture_output=True)
    return leer_exenciones(r.stdout.decode("utf-8")) if r.returncode == 0 else None


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


def generar_exenciones(tareas: list[Tarea], arbol: set[str], leer: Callable[[str], str], base: str) -> int:
    """Medición única de la fase 1. Se niega a reescribir la lista: solo puede decrecer a mano."""
    if EXENCIONES.exists():
        print("ERROR: la lista de exenciones ya existe; solo puede decrecer y no se regenera")
        return 1
    hallazgos = [x for x in validar_contra_arbol(tareas, arbol, leer, base) if x.nivel == "error"]
    def motivo(m: str) -> str:
        for clave, texto in (("quiso decir", "ruta equivocada: " + m.split("¿quiso decir ", 1)[-1].split("?")[0]),
                             ("no tiene la marca", "sección sin marca ni siembra de una ancestro"),
                             ("ninguna ancestro", "sección en un archivo que no existe y que no crea ninguna ancestro"),
                             ("no siembra", "la creadora no siembra la sección"),
                             ("ya existe", "«crea» de un archivo que ya existe"),
                             ("varias creadoras", "varias creadoras"),
                             ("siembra «", "«siembra» incoherente")):
            if clave in m:
                return texto
        return m.split(": ", 1)[-1].replace("|", "/")

    filas = sorted({f"{x.ficha}|{x.entrada}|{motivo(x.mensaje)}" for x in hallazgos})
    lineas = [f"# Exenciones de R-PROP-EXISTE (ADPA-10), medidas una sola vez sobre {base}.",
              "# Formato: ficha|entrada|motivo. Solo puede decrecer: corrija la ficha y retire su línea.",
              *filas]
    EXENCIONES.write_text("\n".join(lineas) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(filas)} exenciones escritas en {EXENCIONES.name}")
    return 0


def main(argv: list[str]) -> int:
    tareas, errores = cargar_tareas()
    salas = salas_del_prd(PRD_MD.read_text(encoding="utf-8"))
    if not salas:
        errores.append("el PRD no declara su catálogo de salas (apartado 5.2)")
    try:
        arbol, leer, base = arbol_git()
    except (OSError, subprocess.CalledProcessError) as exc:
        errores.append(f"no se pudo leer el árbol de HEAD con git: {exc}")
        arbol, leer, base = None, None, "HEAD"
    if "--generar-exenciones" in argv:
        return generar_exenciones(tareas, arbol or set(), leer or (lambda _r: ""), base)
    exenciones = leer_exenciones(EXENCIONES.read_text(encoding="utf-8")) if EXENCIONES.exists() else []
    previas = exenciones_en(RAIZ, "origin/main") if arbol is not None else None
    if previas is not None:
        errores += exenciones_nuevas(previas, exenciones)
    avisos: list[str] = []
    errores += validar(tareas, salas or None, arbol=arbol, leer=leer, exenciones=exenciones,
                       base=base, avisos=avisos,
                       texto_exenciones=EXENCIONES.read_text(encoding="utf-8") if EXENCIONES.exists() else None)
    if arbol is not None:
        vivas = [t for t in tareas if t.estado != "hecha"]
        print(f"Base: {base}, {len(vivas)} fichas no hechas, {sum(len(t.propiedad) for t in vivas)} entradas"
              f" ({len(exenciones)} exenciones, {len(avisos)} avisos de fase 1)")
        if "--avisos" in argv:
            for a in avisos:
                print("AVISO:", a)
    if "--estado" in argv:
        print(resumen_estado(tareas))
        return 1 if errores else 0
    with open(TASKS_MD, encoding="utf-8", newline="") as f:
        texto = f.read()
    indice = generar_indice(tareas)
    if "--escribir" in argv and not errores:
        nuevo = aplicar_indice(texto, indice)
        with open(TASKS_MD, "w", encoding="utf-8", newline="") as f:
            f.write(nuevo)
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
