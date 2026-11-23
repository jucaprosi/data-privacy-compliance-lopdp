# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤molde
# ¤arbitro
# Justificación: copia de LOPDP del molde de ZERAG (governance/molde/generar_indice_tareas.py, TICKET-270), adoptada en
#   GOB-05. Todo lo marcado «# ¤molde» es el molde sin cambios, salvo las líneas «LOPDP:», que dicen en qué difiere y
#   por qué. Al final, el bloque «LOPDP (GOB-05)» es lo que esta copia conserva y el molde no tiene. Lo que deba subir
#   al molde se pide como ticket de ZERAG: no se modifica el molde desde aquí.
"""Genera el índice de tareas de un proyecto gobernado y comprueba que el reparto de archivos sea disjunto.

Contrato
    Entrada : las tareas del disco, una por archivo ``governance/tareas/<ID>.md`` con una cabecera TOML entre dos
              líneas ``+++`` (id, titulo, ola, estado, sala, depende_de, propiedad, arbitro y, opcionales, crea y siembra). El alcance se deriva del
              disco: no se escribe a mano en ningún otro lugar.
    Salida  : un ``Informe`` con el índice, los pares en conflicto y la BASE COMPARADA (qué tareas y qué archivos se
              compararon). Nada se da por comparado sin constar aquí.
    Regla   : dos tareas que pueden ejecutarse a la vez (ninguna es ancestro de la otra por ``depende_de``) no pueden
              poseer el mismo ARCHIVO. La comparación es por archivo normalizado, nunca por prefijo ni por texto crudo.
              Una entrada con comodín (``**``, ``*``, ``?``, ``[...]``) posee todos los archivos que acepta: dos
              entradas se pisan si existe al menos una ruta que ambas aceptan (TICKET-283).
              Una entrada ``archivo#SECCION`` posee solo esa sección: dos tareas pueden compartir un archivo si cada
              una reserva una sección distinta. La CABECERA (lo anterior a la primera marca) es zona compartida de solo
              añadir que ninguna sección posee: los imports van ahí y las marcas después, sin ``# noqa: E402``; un import
              posterior a la primera marca avisa (``IMPORT_EN_SECCION``, TICKET-292) y el sobrante lo retira ruff (F401).
              En un archivo de configuración (YAML, TOML, JSON y ``CLAVE=valor``) la
              sección es la CLAVE DE PRIMER NIVEL (``config.yml#cache``) y no necesita marca: la lee el generador del
              archivo (TICKET-295). Si el archivo existe y no se puede analizar, la unidad es el archivo entero y la
              sección se ignora; dos tareas que tocan la misma clave siguen pisándose. Las tareas en estado ``hecha`` no se comparan, porque ya no pueden
              ejecutarse a la vez; la base dice cuántas quedaron fuera y siguen contando como ancestros.
    Medida  : ``Informe.medidas["tandas"]`` y ``--tandas`` dicen cuántas TANDAS salen del reparto declarado y cuántas
              saldrían con la propiedad reducida a archivos concretos (las entradas con comodín se ignoran). Una TANDA es
              un conjunto de tareas no hechas que pueden ejecutarse a la vez: ninguna es ancestro de otra por
              ``depende_de``, sus entradas no se pisan (``se_pisan``) y todas sus dependencias están hechas o en una tanda
              anterior. El reparto es codicioso y determinista: en cada ronda, las tareas listas se recorren por id y entra
              la que no se pisa con las ya elegidas. Solo mide: no hay umbral, ni tope de tareas por tanda, ni orden entre
              tareas más allá de ``depende_de``. El valor con archivos concretos es una cota alcanzada por ese algoritmo, no
              un mínimo demostrado (el óptimo es un problema de coloreo); se informa el menor de los dos recuentos, porque
              el reparto declarado sigue siendo válido al quitar comodines.
    Árbol   : con un repositorio de git, ``--verificar`` y ``--escribir`` comprueban además R-PROP-EXISTE (TICKET-277,
              fase 1) con ``validar_contra_arbol``: toda entrada de propiedad existe en ``git ls-tree -r HEAD``, o la crea la
              tarea (campo ``crea``) o una ancestro, y toda sección ``archivo#ID`` tiene la marca ``=== ID ===`` o la siembra
              una ancestro (campo ``siembra = ["ruta#ID"]``). Imprime «Base: HEAD <sha>, N tareas no hechas, M entradas».
              Sin árbol de git no se comprueba y lo dice por la salida de error; la salida estándar no cambia.
    Exención: ``governance/tareas/_exenciones_propiedad.txt`` (una línea ``ficha|entrada|motivo``) tapa un error de
              R-PROP-EXISTE de esa tarea y esa entrada, con un motivo obligatorio. Caduca cuando deja de tapar un error
              (TICKET-294). El generador nunca crea ni reescribe ese archivo (TICKET-300): es una declaración de su
              dueño. En modo árbitro (``--arbitro`` o ``ZERAG_ARBITRO=1``) la exención caducada es un error que la
              nombra; en modo local, un aviso. Ambos dicen qué línea retirar, y la retira el dueño del archivo.
              La lista solo decrece (TICKET-300): una exención cuya clave no está en la referencia publicada
              (``--referencia``, ``ZERAG_REFERENCIA_EXENCIONES`` o, sin ellas, ``origin/main``) es un error en modo
              árbitro y un aviso en modo local. Con exenciones, una referencia que no resuelve es un error en modo
              árbitro, también sin remoto, y un aviso por la salida de error en modo local.
    Rechazo : con errores no se escribe el índice. El conjunto vacío es un error y dice qué base se miró.

Punto de extensión
    Cada comprobación es una función ``Contexto -> list[Hallazgo]`` registrada con ``@comprobacion("nombre")``, o pasada
    a ``generar(raiz, comprobaciones=[...])``. Un ``Hallazgo`` con ``bloquea=True`` es un error y uno con
    ``bloquea=False`` es un aviso. ``Informe.medidas`` recoge lo que una comprobación solo mide. Una comprobación nueva
    se añade registrándola; el cargador, el índice y la salida no cambian.

Copia de LOPDP (GOB-05)
    La API pública es la de LOPDP (``cargar_tareas()``, ``validar()``, ``rutas_se_solapan``, ``salas_del_prd``...),
    construida sobre las funciones del molde. Además del molde comprueba el catálogo de salas del PRD (apartado 5.2),
    las olas, el campo ``agente`` (CI-31) y las secciones del archivo de exenciones (CI-22). El índice no se versiona:
    ``--escribir`` lo deja en ``governance/artefactos/_generado/`` (CI-29). Con 0 tareas no hechas es válido y con 0
    tareas cargadas da error (CI-35). Sin árbol de git es un error. ``--generar-exenciones`` sigue disponible
    (COORDINACION C.13 de ZERAG) y se niega si la lista ya existe.

Uso
    python scripts/generar_indice_tareas.py --verificar   # código 1 si hay errores o el índice está viejo
    python scripts/generar_indice_tareas.py --escribir    # genera el índice en _generado/; se niega si hay errores
    python scripts/generar_indice_tareas.py --estado      # imprime el estado de cada tarea
    python scripts/generar_indice_tareas.py --tandas      # imprime tandas declaradas frente al mínimo con archivos concretos

Requiere Python 3.11 o posterior (usa ``tomllib``).
"""


from __future__ import annotations

import argparse
import ast
import os
import json
import posixpath
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    tomllib = None  # type: ignore[assignment]

INICIO = "<!-- INDICE-TAREAS:INICIO (generado por scripts/generar_indice_tareas.py; no editar a mano) -->"
FIN = "<!-- INDICE-TAREAS:FIN -->"

ESTADOS = ("pendiente", "en_curso", "hecha", "bloqueada")
ESTADO_HECHA = "hecha"
CAMPOS = ("id", "titulo", "ola", "estado", "sala", "depende_de", "propiedad", "arbitro")
CAMPOS_OPCIONALES = ("crea", "siembra")  # TICKET-277: vacíos por defecto

# LOPDP: rutas, olas y agentes de esta copia. El molde recibe la raíz por ``main(--raiz)``; los consumidores de LOPDP
#   (scripts/verificar_reparto.py, scripts/verificar_alcance_pr.py y las pruebas) usan estas constantes.
RAIZ = Path(__file__).resolve().parent.parent
DIR_TAREAS = RAIZ / "governance" / "tareas"
TASKS_MD = RAIZ / "governance" / "artefactos" / "TASKS.md"
PRD_MD = RAIZ / "governance" / "artefactos" / "PRD.md"
INDICE_GENERADO = RAIZ / "governance" / "artefactos" / "_generado" / "INDICE_TAREAS.md"
OLAS = ("A", "B", "C", "D", "E", "indep", "backlog")
AGENTES = ("asignable", "ninguno")  # CI-31: «ninguno» = ficha sin brief, que no se asigna a un agente


# --------------------------------------------------------------------------- tipos

@dataclass(frozen=True)
# ¤molde
class Tarea:
    id: str
    titulo: str
    ola: str
    estado: str
    sala: str
    depende_de: Tuple[str, ...]
    propiedad: Tuple[str, ...]
    arbitro: str
    archivo: str = ""
    crea: Tuple[str, ...] = ()
    siembra: Tuple[str, ...] = ()
    agente: str = "asignable"  # LOPDP (CI-31): «ninguno» = ficha sin brief; el molde no tiene briefs


@dataclass(frozen=True)
# ¤molde
class Hallazgo:
    codigo: str
    mensaje: str
    bloquea: bool = True
    ficha: str = ""    # TICKET-294: tarea y entrada a las que se refiere; solo con ellas un error se puede eximir
    entrada: str = ""


@dataclass(frozen=True)
# ¤molde
class Conflicto:
    a: str
    b: str
    archivo: str
    entrada_a: str
    entrada_b: str

    def texto(self) -> str:
        return (f"{self.a} y {self.b} pueden ejecutarse a la vez y ambas poseen «{self.archivo}» "
                f"({self.a}: «{self.entrada_a}»; {self.b}: «{self.entrada_b}»)")


@dataclass
# ¤molde
class Base:
    """Lo que realmente se miró: sin esto, un «sin conflictos» no dice sobre qué."""
    directorio: str = ""
    archivos_de_tareas: List[str] = field(default_factory=list)
    ids: List[str] = field(default_factory=list)
    hechas_fuera: List[str] = field(default_factory=list)  # ids de tareas `hecha` que no entran en la comparación
    archivos_comparados: List[str] = field(default_factory=list)

    def resumen(self) -> str:
        lineas = [f"Base comparada: {len(self.ids)} tareas en {self.directorio}",
                  f"  tareas: {', '.join(self.ids) or '(ninguna)'}",
                  f"  hechas fuera de la comparación: {len(self.hechas_fuera)}"
                  + (f" ({', '.join(self.hechas_fuera)})" if self.hechas_fuera else ""),
                  f"  archivos comparados ({len(self.archivos_comparados)}): {', '.join(self.archivos_comparados) or '(ninguno)'}"]
        return "\n".join(lineas)


@dataclass
# ¤molde
class Informe:
    tareas: List[Tarea]
    indice: str
    conflictos: List[Conflicto]
    base: Base
    errores: List[str]
    avisos: List[str]
    medidas: Dict[str, object]

    @property
    def ok(self) -> bool:
        return not self.errores


# --------------------------------------------------------------------------- lectura

# ¤molde
def leer_cabecera(texto: str) -> dict:
    if tomllib is None:
        raise RuntimeError("se requiere Python 3.11 o posterior (módulo tomllib)")
    lineas = texto.replace("\r\n", "\n").split("\n")
    if not lineas or lineas[0].strip() != "+++":
        raise ValueError("falta la cabecera '+++' al inicio")
    try:
        fin = lineas.index("+++", 1)
    except ValueError:
        raise ValueError("la cabecera no se cierra con '+++'") from None
    return tomllib.loads("\n".join(lineas[1:fin]))


# ¤molde
def _es_especificacion(ruta: Path) -> bool:
    nombre = ruta.name.lower()
    return not (nombre == "readme.md" or nombre.startswith("plantilla"))


# ¤molde
def _lista_de_textos(valor: object) -> Optional[Tuple[str, ...]]:
    if isinstance(valor, list) and all(isinstance(x, str) for x in valor):
        return tuple(valor)
    return None


# ¤molde
def cargar_tareas(directorio: Path = DIR_TAREAS) -> Tuple[List[Tarea], List[str]]:
    """Devuelve (tareas, errores).

    LOPDP: con directorio por defecto, sin la lista de archivos leídos (que solo usa ``Base`` en ``generar``) y con el
    campo ``agente`` (CI-31). Cinco consumidores de LOPDP llaman ``cargar_tareas()`` y esperan dos valores.
    """
    tareas: List[Tarea] = []
    errores: List[str] = []
    if not directorio.is_dir():
        return tareas, errores
    for ruta in sorted(directorio.glob("*.md")):
        if not _es_especificacion(ruta):
            continue
        try:
            datos = leer_cabecera(ruta.read_text(encoding="utf-8"))
        except Exception as exc:  # cabecera ilegible: se informa y se sigue con las demás
            errores.append(f"{ruta.name}: {exc}")
            continue
        faltan = [c for c in CAMPOS if c not in datos]
        if faltan:
            errores.append(f"{ruta.name}: faltan campos {faltan}")
            continue
        depende, propiedad = _lista_de_textos(datos["depende_de"]), _lista_de_textos(datos["propiedad"])
        if depende is None or propiedad is None:
            errores.append(f"{ruta.name}: «depende_de» y «propiedad» deben ser listas de texto")
            continue
        opcionales = {c: _lista_de_textos(datos.get(c, [])) for c in CAMPOS_OPCIONALES}
        malos = [c for c, v in opcionales.items() if v is None]
        if malos:
            errores.append(f"{ruta.name}: {', '.join(f'«{c}»' for c in malos)} debe ser una lista de texto")
            continue
        tarea = Tarea(id=str(datos["id"]), titulo=str(datos["titulo"]), ola=str(datos["ola"]),
                      estado=str(datos["estado"]), sala=str(datos["sala"]), depende_de=depende,
                      propiedad=propiedad, arbitro=str(datos["arbitro"]), archivo=ruta.name,
                      crea=opcionales["crea"], siembra=opcionales["siembra"],
                      agente=str(datos.get("agente", "asignable")))  # LOPDP (CI-31)
        if ruta.stem != tarea.id:
            errores.append(f"{ruta.name}: el nombre del archivo debe ser {tarea.id}.md")
        if tarea.agente not in AGENTES:  # LOPDP (CI-31)
            errores.append(f"{ruta.name}: agente «{tarea.agente}» no es uno de {list(AGENTES)}")
        tareas.append(tarea)
    return tareas, errores


# --------------------------------------------------------------------------- grafo

# ¤molde
def _ciclos(tareas: List[Tarea]) -> List[str]:
    por_id = {t.id: t for t in tareas}
    estado: Dict[str, int] = {}
    ciclos: List[str] = []

    def visitar(tid: str, camino: List[str]) -> None:
        estado[tid] = 1
        for d in por_id[tid].depende_de:
            if d not in por_id:
                continue
            if estado.get(d) == 1:
                ciclos.append(" -> ".join(camino + [tid, d]))
            elif d not in estado:
                visitar(d, camino + [tid])
        estado[tid] = 2

    for t in tareas:
        if t.id not in estado:
            visitar(t.id, [])
    return ciclos


# ¤molde
def _ancestros(tareas: List[Tarea]) -> Dict[str, frozenset]:
    """Cierre transitivo de depende_de. Exige un grafo sin ciclos ni dependencias inexistentes."""
    por_id = {t.id: t for t in tareas}
    memo: Dict[str, frozenset] = {}

    def recorrer(tid: str) -> frozenset:
        if tid not in memo:
            acumulado: set = set()
            for d in por_id[tid].depende_de:
                acumulado |= {d} | recorrer(d)
            memo[tid] = frozenset(acumulado)
        return memo[tid]

    return {t.id: recorrer(t.id) for t in tareas}


# ¤molde
def validar_estructura(tareas: List[Tarea]) -> List[str]:
    errores: List[str] = []
    vistos: set = set()
    ids = {t.id for t in tareas}
    for t in tareas:
        if t.id in vistos:
            errores.append(f"{t.id}: id duplicado")
        vistos.add(t.id)
        if t.estado not in ESTADOS:
            errores.append(f"{t.id}: estado inválido «{t.estado}» (válidos: {', '.join(ESTADOS)})")
        for campo in ("titulo", "ola", "sala", "arbitro"):
            if not getattr(t, campo).strip():
                errores.append(f"{t.id}: el campo «{campo}» no puede estar vacío")
        if not t.propiedad:
            errores.append(f"{t.id}: debe declarar al menos un archivo de su propiedad")
        for entrada in t.propiedad:
            ruta = entrada.partition("#")[0].strip().replace("\\", "/")
            if not ruta:
                errores.append(f"{t.id}: la propiedad «{entrada}» no nombra ningún archivo")
            elif ruta.startswith("/") or ruta.startswith("../") or ":" in ruta.split("/")[0]:
                errores.append(f"{t.id}: la propiedad «{entrada}» sale del proyecto; use una ruta relativa")
            elif ruta.endswith("/"):
                # TICKET-273: una carpeta no se compara con los archivos de dentro; dejarla pasar oculta choques.
                # LOPDP: «termina en «/»» lo fija tests/test_indice_tareas.py (Aporte 129); ticket para ZERAG
                errores.append(f"{t.id}: la propiedad «{entrada}» termina en «/»: es una carpeta; declare «carpeta/**» o archivos concretos")
        for d in t.depende_de:
            if d == t.id:
                errores.append(f"{t.id}: depende de sí misma")
            elif d not in ids:
                errores.append(f"{t.id}: depende de «{d}», que no existe")
    errores += [f"ciclo de dependencias: {c}" for c in _ciclos(tareas)]
    return errores


# --------------------------------------------------------------------------- propiedad por archivo

# ¤molde
def normalizar_archivo(ruta: str) -> str:
    """Identidad de un archivo: separador único, sin './' ni '//' y sin distinguir mayúsculas.

    Se ignoran las mayúsculas para no dejar pasar ``Core/X.py`` frente a ``core/x.py`` en un disco que no las
    distingue; el costo es un posible aviso de más, nunca un choque oculto.
    """
    r = ruta.strip().replace("\\", "/")
    return posixpath.normpath(r).casefold() if r else r


# ¤molde
def separar_entrada(entrada: str) -> Tuple[str, str]:
    """«archivo#SECCION» -> (archivo normalizado, sección); la sección distingue mayúsculas."""
    archivo, _, seccion = entrada.partition("#")
    return normalizar_archivo(archivo), seccion.strip()


# --------------------------------------------------------------------------- lenguaje de una entrada (TICKET-283)
#
# Una entrada es un patrón de ruta. Se traduce a una secuencia de pasos: un paso fijo acepta exactamente un carácter de
# un conjunto; un paso repetible acepta cero o más. Cada conjunto es una lista de intervalos de puntos de código.
# Dos entradas se pisan si sus lenguajes se cortan: hay un camino que termina a la vez en las dos secuencias.

_MAXIMO = 0x10FFFF
_BARRA = ord("/")
_CUALQUIERA = ((0, _MAXIMO),)
_SIN_BARRA = ((0, _BARRA - 1), (_BARRA + 1, _MAXIMO))


# ¤molde
def _pasos(patron: str) -> List[Tuple[bool, Tuple[Tuple[int, int], ...]]]:
    """(repetible, intervalos) por paso: ``**`` cruza carpetas; ``*``, ``?`` y ``[...]`` no cruzan la barra."""
    pasos, i = [], 0
    while i < len(patron):
        if patron.startswith("**", i):
            pasos.append((True, _CUALQUIERA))
            i += 2
        elif patron[i] == "*":
            pasos.append((True, _SIN_BARRA))
            i += 1
        elif patron[i] == "?":
            pasos.append((False, _SIN_BARRA))
            i += 1
        elif patron[i] == "[" and "]" in patron[i + 1:]:
            j = patron.index("]", i + 1)
            clase, intervalos, k = patron[i + 1:j], [], 0
            while k < len(clase):
                if k + 2 < len(clase) and clase[k + 1] == "-":
                    intervalos.append((ord(clase[k]), ord(clase[k + 2])))
                    k += 3
                else:
                    intervalos.append((ord(clase[k]), ord(clase[k])))
                    k += 1
            pasos.append((False, tuple(intervalos)))
            i = j + 1
        else:
            pasos.append((False, ((ord(patron[i]), ord(patron[i])),)))
            i += 1
    return pasos


# ¤molde
def _se_cortan(a: Tuple[Tuple[int, int], ...], b: Tuple[Tuple[int, int], ...]) -> bool:
    return any(max(x0, y0) <= min(x1, y1) for x0, x1 in a for y0, y1 in b)


# ¤molde
def lenguajes_se_cortan(patron_a: str, patron_b: str) -> bool:
    """¿Existe una ruta que aceptan los dos patrones? Recorrido exacto del producto de sus autómatas."""
    pa, pb = _pasos(patron_a), _pasos(patron_b)
    pendientes, vistos = [(0, 0)], set()
    while pendientes:
        i, j = pendientes.pop()
        if (i, j) in vistos:
            continue
        vistos.add((i, j))
        if i == len(pa) and j == len(pb):
            return True
        if i < len(pa) and pa[i][0]:
            pendientes.append((i + 1, j))
        if j < len(pb) and pb[j][0]:
            pendientes.append((i, j + 1))
        if i < len(pa) and j < len(pb) and _se_cortan(pa[i][1], pb[j][1]):
            pendientes.append((i if pa[i][0] else i + 1, j if pb[j][0] else j + 1))
    return False


# ¤molde
def mismo_archivo(entrada_a: str, entrada_b: str) -> bool:
    """¿Comparten las dos entradas algún archivo? Para dos rutas concretas es la igualdad del archivo normalizado."""
    return lenguajes_se_cortan(separar_entrada(entrada_a)[0], separar_entrada(entrada_b)[0])


# ¤molde
def se_pisan(entrada_a: str, entrada_b: str, enteros: frozenset = frozenset()) -> bool:
    """Dos entradas se pisan si son el mismo archivo, salvo que ambas reserven secciones distintas.

    ``enteros`` son los archivos (normalizados) cuya sección se ignora porque no se pudo analizar (TICKET-295).
    """
    if not mismo_archivo(entrada_a, entrada_b):
        return False
    (archivo_a, seccion_a), (archivo_b, seccion_b) = separar_entrada(entrada_a), separar_entrada(entrada_b)
    if archivo_a in enteros or archivo_b in enteros:
        return True
    return not (seccion_a and seccion_b and seccion_a != seccion_b)


# --------------------------------------------------------------------------- claves de configuración (TICKET-295)
#
# Un archivo de configuración no lleva marcas ``=== ID ===``: su unidad de propiedad es la clave de primer nivel.
# ``claves_de_configuracion`` devuelve esas claves, o None si el formato no se reconoce o el texto no se puede analizar.
# El analizador de YAML es deliberadamente conservador (sin dependencias): solo acepta un mapeo en la raíz y devuelve None
# ante un documento múltiple, una lista o un valor de flujo en la raíz, o una línea de raíz que no sea ``clave:``; en esos
# casos el archivo se posee entero.

_CLAVE_YAML = re.compile(r"""^(?P<k>[A-Za-z0-9_][\w.\-]*|"[^"]+"|'[^']+')\s*:(\s|$)""")
_CLAVE_ENV = re.compile(r"^(?:export\s+)?(?P<k>[A-Za-z_][A-Za-z0-9_.]*)\s*=")


# ¤molde
def es_configuracion(ruta: str) -> bool:
    nombre = posixpath.basename(ruta.strip().replace("\\", "/")).casefold()
    return nombre.endswith((".yaml", ".yml", ".toml", ".json", ".env")) or nombre.startswith(".env")


# ¤molde
def claves_de_configuracion(ruta: str, texto: str) -> Optional[frozenset]:
    """Claves de primer nivel de ``texto`` según la extensión de ``ruta``; None si no se pueden determinar."""
    nombre = posixpath.basename(ruta.strip().replace("\\", "/")).casefold()
    texto = texto.lstrip("\ufeff")
    try:
        if nombre.endswith(".json"):
            datos = json.loads(texto)
            return frozenset(datos) if isinstance(datos, dict) else None
        if nombre.endswith(".toml"):
            if tomllib is None:
                return None
            return frozenset(tomllib.loads(texto))
    except ValueError:  # JSONDecodeError y TOMLDecodeError son ValueError
        return None
    claves: List[str] = []
    for linea in texto.replace("\r\n", "\n").split("\n"):
        if not linea.strip() or linea.lstrip().startswith("#"):
            continue
        if nombre.endswith((".yaml", ".yml")):
            if linea[0] in " \t":
                continue  # sangrado: pertenece a la clave de arriba
            m = _CLAVE_YAML.match(linea)
            if m is None:  # «---», «- x», «[a]», «{a}», un escalar suelto...
                return None
            claves.append(m.group("k").strip("\"'"))
        else:
            m = _CLAVE_ENV.match(linea)
            if m is None:
                return None
            claves.append(m.group("k"))
    if not claves or len(claves) != len(set(claves)):
        return None  # vacío o con claves repetidas: no hay unidad fiable
    return frozenset(claves)


# ¤molde
def archivos_enteros(raiz: Path, tareas: List[Tarea]) -> frozenset:
    """Archivos de configuración con entrada ``#clave`` que existen en ``raiz`` y no se pueden analizar.

    Un archivo que aún no existe (lo crea una tarea) no está aquí: sus claves son las que declaran las tareas.
    """
    enteros: set = set()
    for t in tareas:
        if t.estado == ESTADO_HECHA:
            continue
        for entrada in t.propiedad:
            archivo, seccion = separar_entrada(entrada)
            if not seccion or archivo in enteros or not es_configuracion(archivo) or es_comodin(entrada):
                continue
            ruta = raiz / entrada.partition("#")[0].strip().replace("\\", "/")
            try:
                texto = ruta.read_text(encoding="utf-8")
            except FileNotFoundError:
                continue
            except (OSError, UnicodeDecodeError):
                enteros.add(archivo)
                continue
            if claves_de_configuracion(archivo, texto) is None:
                enteros.add(archivo)
    return frozenset(enteros)


# ¤molde
def tareas_en_paralelo(a: Tarea, b: Tarea, ancestros: Dict[str, frozenset]) -> bool:
    return b.id not in ancestros[a.id] and a.id not in ancestros[b.id]


# ¤molde
def encontrar_conflictos(tareas: List[Tarea], ancestros: Dict[str, frozenset],
                         enteros: frozenset = frozenset()) -> Tuple[List[Conflicto], Base]:
    """Compara por pares las tareas no hechas que pueden ejecutarse a la vez.

    Una tarea `hecha` ya no puede ejecutarse: no entra en la comparación (y consta en ``Base.hechas_fuera``), pero
    sigue siendo ancestro de las que dependen de ella, porque ``ancestros`` se calcula sobre todas las tareas.

    Hay una sola definición de «mismo archivo» (``mismo_archivo``) y se aplica a cada par de entradas. El costo es
    cuadrático en el número de tareas; para cientos de tareas son decenas de miles de comparaciones de texto.
    """
    base = Base(ids=[t.id for t in tareas], hechas_fuera=sorted(t.id for t in tareas if t.estado == ESTADO_HECHA))
    comparados: set = set()
    entradas_de: Dict[str, List[str]] = {}
    for t in tareas:
        entradas_de[t.id] = []
        if t.estado == ESTADO_HECHA:
            continue
        for entrada in t.propiedad:
            entradas_de[t.id].append(entrada)
            comparados.add(separar_entrada(entrada)[0])
    base.archivos_comparados = sorted(comparados)

    conflictos: List[Conflicto] = []
    ordenadas = sorted(tareas, key=lambda t: t.id)
    for i, a in enumerate(ordenadas):
        for b in ordenadas[i + 1:]:
            if not tareas_en_paralelo(a, b, ancestros):
                continue
            vistos: set = set()
            for entrada_a in entradas_de[a.id]:
                for entrada_b in entradas_de[b.id]:
                    archivo = separar_entrada(entrada_a)[0]
                    if se_pisan(entrada_a, entrada_b, enteros) and archivo not in vistos:
                        vistos.add(archivo)
                        conflictos.append(Conflicto(a.id, b.id, archivo, entrada_a, entrada_b))
    return conflictos, base


# --------------------------------------------------------------------------- tandas (TICKET-274)

# ¤molde
def es_comodin(entrada: str) -> bool:
    """¿La parte de archivo de la entrada lleva ``*``, ``?`` o una clase ``[...]`` cerrada?"""
    archivo = entrada.partition("#")[0]
    return "*" in archivo or "?" in archivo or ("[" in archivo and "]" in archivo[archivo.index("[") + 1:])


# ¤molde
def calcular_tandas(tareas: List[Tarea], solo_concretos: bool = False,
                    enteros: frozenset = frozenset()) -> List[List[str]]:
    """Reparte las tareas no hechas en tandas (ver «Medida» en el docstring del módulo); ids ordenados dentro de cada una.

    Con ``solo_concretos`` se descartan las entradas con comodín: una tarea sin entradas concretas no se pisa con nadie.
    No depende del orden de ``tareas``: las ids se ordenan antes de recorrerse.
    """
    hechas = {t.id for t in tareas if t.estado == ESTADO_HECHA}
    pendientes = {t.id: t for t in tareas if t.estado != ESTADO_HECHA}
    entradas = {i: [e for e in t.propiedad if not (solo_concretos and es_comodin(e))] for i, t in pendientes.items()}
    tandas: List[List[str]] = []
    while pendientes:
        listas = sorted(i for i, t in pendientes.items() if all(d in hechas for d in t.depende_de))
        if not listas:  # solo con ciclos o dependencias inexistentes, que validar_estructura ya rechaza
            break
        tanda: List[str] = []
        for i in listas:
            if not any(se_pisan(a, b, enteros) for j in tanda for a in entradas[i] for b in entradas[j]):
                tanda.append(i)
        tandas.append(tanda)
        hechas.update(tanda)
        for i in tanda:
            del pendientes[i]
    return tandas


# ¤molde
def medir_tandas(tareas: List[Tarea], enteros: frozenset = frozenset()) -> Dict[str, object]:
    declaradas = calcular_tandas(tareas, enteros=enteros)
    concretas = calcular_tandas(tareas, solo_concretos=True, enteros=enteros)
    minimo = min(len(declaradas), len(concretas))
    return {"declaradas": len(declaradas), "minimo_con_archivos_concretos": minimo,
            "perdidas_por_comodines": len(declaradas) - minimo,
            "entradas_con_comodin": sum(1 for t in tareas if t.estado != ESTADO_HECHA for e in t.propiedad if es_comodin(e)),
            "reparto_declarado": declaradas, "reparto_con_archivos_concretos": concretas}


# ¤molde
def texto_tandas(medida: Dict[str, object]) -> str:
    return (f"Tandas: {medida['declaradas']} con el reparto declarado; mínimo con archivos concretos: "
            f"{medida['minimo_con_archivos_concretos']} (perdidas por comodines: {medida['perdidas_por_comodines']}; "
            f"entradas con comodín: {medida['entradas_con_comodin']}).")


# --------------------------------------------------------------------------- propiedad contra el árbol (TICKET-277)
#
# R-PROP-EXISTE: toda entrada de propiedad de una tarea no hecha debe existir en el árbol del commit, o ser creada por la
# propia tarea o por una ancestro, y toda sección ``archivo#ID`` debe estar sembrada. El árbol y la lectura de archivos se
# inyectan: el árbitro no toca el disco ni git; ``leer_arbol_git`` y ``leer_archivo_git`` son el único lugar que los toca.

_MAXIMO_SUGERENCIAS = 3


# ¤molde
def tiene_marca(texto: str, id_: str) -> bool:
    """¿El texto lleva la marca de la sección ``id_``: ``=== ID ===`` o la forma heredada ``--- INICIO ID ---``?"""
    return f"=== {id_} ===" in texto or f"--- INICIO {id_} ---" in texto


_MARCA_SECCION = re.compile(r"^[ \t]*#[ \t]*(?:=== \S+ ===|--- INICIO \S+ ---)", re.MULTILINE)


# ¤molde
def imports_dentro_de_secciones(texto: str) -> List[int]:
    """Líneas de los ``import`` de módulo que quedan después de la primera marca de sección (TICKET-292).

    La CABECERA, todo lo anterior a la primera marca, es zona compartida de solo añadir: ninguna sección la posee, así
    que los imports viven ahí (PEP 8, ruff E402) y las marcas van después, como comentarios. Quien retire un import que
    ya nadie usa no lo decide la propiedad sino ruff (F401; F821 si falta uno). Devuelve [] si no hay marcas o el texto
    no se puede analizar como Python.
    """
    marca = _MARCA_SECCION.search(texto)
    if marca is None:
        return []
    primera = texto.count("\n", 0, marca.start()) + 1
    try:
        arbol = ast.parse(texto)
    except (SyntaxError, ValueError):
        return []
    return [n.lineno for n in arbol.body if isinstance(n, (ast.Import, ast.ImportFrom)) and n.lineno > primera]


# ¤molde
def _ancestros_tolerantes(tareas: List[Tarea]) -> Dict[str, frozenset]:
    """Cierre transitivo de ``depende_de`` que ignora lo inexistente y no se cuelga con ciclos."""
    por_id = {t.id: t for t in tareas}
    cierre: Dict[str, frozenset] = {}
    for t in tareas:
        vistos: set = set()
        pendientes = list(t.depende_de)
        while pendientes:
            d = pendientes.pop()
            if d in vistos or d not in por_id:
                continue
            vistos.add(d)
            pendientes.extend(por_id[d].depende_de)
        cierre[t.id] = frozenset(vistos)
    return cierre


# ¤molde
def sugerir_ruta(ruta: str, arbol: Dict[str, str]) -> Tuple[List[str], bool]:
    """Rutas existentes que el autor quiso decir. Devuelve (sugerencias, fuerte).

    ``arbol`` es {ruta normalizada: ruta real}. Primero se busca el ancestro existente más cercano de ``ruta`` y se
    reconstruye el segmento que falta: es fuerte si el resto completo aparece bajo ese ancestro (``a/pantallas/i.tsx`` ->
    ``a/layout/pantallas/i.tsx``). Si no, se buscan nombres con el mismo nombre base (bajo el ancestro y luego en todo el
    árbol); esa sugerencia es débil porque un nombre común no prueba que la ruta estuviera equivocada.
    """
    segmentos = ruta.split("/")
    existentes = {r.rpartition("/")[0] for r in arbol}
    carpetas = set()
    for c in existentes:
        while c:
            carpetas.add(c)
            c = c.rpartition("/")[0]
    base, resto = "", segmentos
    for n in range(len(segmentos) - 1, 0, -1):
        if "/".join(segmentos[:n]) in carpetas:
            base, resto = "/".join(segmentos[:n]), segmentos[n:]
            break
    prefijo = base + "/" if base else ""
    salas = {_sala_de_ruta(r) for r in arbol}
    sala_existe = _sala_de_ruta(ruta) in salas
    for corte in range(len(resto)):
        sufijo = "/".join(resto[corte:])
        solo_nombre = "/" not in sufijo and sala_existe  # TICKET-293: con la sala ya existente, un nombre base suelto solo cuenta dentro de ella
        encontradas = sorted(arbol[r] for r in arbol if r.startswith(prefijo) and (r == prefijo + sufijo or r.endswith("/" + sufijo))
                             and (not solo_nombre or _sala_de_ruta(r) == _sala_de_ruta(ruta)))
        if encontradas:
            return encontradas[:_MAXIMO_SUGERENCIAS], bool(base) and corte == 0
    nombre, sala = segmentos[-1], _sala_de_ruta(ruta)
    return sorted(real for r, real in arbol.items() if r.rpartition("/")[2] == nombre and (not sala_existe or _sala_de_ruta(r) == sala))[:_MAXIMO_SUGERENCIAS], False


# ¤molde
def _sala_de_ruta(ruta: str) -> str:
    """Sala de una ruta: ``features/<sala>`` si cuelga de ``features/``; si no, su primera carpeta (vacía si está en la raíz).

    TICKET-293: un nombre base común (``a.py``) no prueba que dos archivos de salas distintas sean el mismo.
    """
    segmentos = ruta.split("/")[:-1]
    if segmentos[:1] == ["features"]:
        return "/".join(segmentos[:2])
    return segmentos[0] if segmentos else ""


# ¤molde
def _prefijo_fijo(entrada: str) -> str:
    """Carpeta fija de un comodín: lo que precede al primer carácter especial, cortado en la última barra."""
    archivo = normalizar_archivo(entrada.partition("#")[0])
    for i, c in enumerate(archivo):
        if c in "*?[":
            return archivo[:i].rpartition("/")[0]
    return archivo.rpartition("/")[0]


# ¤molde
def validar_contra_arbol(tareas: List[Tarea], arbol: Iterable[str], leer: Callable[[str], Optional[str]],
                         base: str = "") -> List[Hallazgo]:
    """R-PROP-EXISTE, fase 1. ``arbol`` son las rutas del commit y ``leer(ruta)`` su texto (None si no se puede leer).

    Fallan: el caso 1 sin marca ni siembra, el caso 2 con ``#ID`` sin creadora, las rutas con sugerencia y los ``crea`` y
    ``siembra`` incoherentes. Solo avisan: la creación implícita y los comodines sin base. ``base`` es el texto que
    identifica el árbol y va en el error del conjunto vacío.
    """
    rutas = {normalizar_archivo(r): r for r in arbol}
    no_hechas = sorted((t for t in tareas if t.estado != ESTADO_HECHA), key=lambda t: t.id)
    # LOPDP (CI-35, #943): 0 tareas cargadas es un fallo del lector y sigue en rojo; 0 tareas no hechas es un estado
    #   legítimo y no hay nada que comparar. El molde da error en los dos casos: ticket para ZERAG.
    if not tareas:
        return [Hallazgo("SIN_TAREAS", f"Base: {base or 'base sin identificar'}, 0 fichas cargadas: el lector de fichas no devolvió ninguna")]
    if not no_hechas:
        return []
    por_id = {t.id: t for t in tareas}
    ancestros = _ancestros_tolerantes(tareas)
    hallazgos: List[Hallazgo] = []
    lecturas: Dict[str, Optional[str]] = {}
    avisados: set = set()

    def error(codigo: str, mensaje: str, ficha: str = "", entrada: str = "") -> None:
        hallazgos.append(Hallazgo(codigo, mensaje, ficha=ficha, entrada=entrada))

    def aviso(codigo: str, mensaje: str) -> None:
        hallazgos.append(Hallazgo(codigo, mensaje, bloquea=False))

    creadoras: Dict[str, List[str]] = {}
    for t in no_hechas:
        for c in t.crea:
            creadoras.setdefault(normalizar_archivo(c), []).append(t.id)

    # regla 4: crea
    for t in no_hechas:
        propias = {separar_entrada(e) for e in t.propiedad}
        for c in t.crea:
            f = normalizar_archivo(c)
            if es_comodin(c):
                error("CREA_INCOHERENTE", f"{t.id}: «crea» no admite comodines («{c}»)", t.id, c)
            if f in rutas and t.estado == "pendiente":  # LOPDP: en curso, su propio PR ya trae el archivo; ticket para ZERAG
                error("CREA_YA_EXISTE", f"{t.id}: «crea» declara «{c}», que ya existe en el árbol", t.id, c)
            if len(creadoras[f]) > 1 and creadoras[f][0] == t.id:
                error("CREA_DOBLE", f"«{c}» tiene más de una creadora: {', '.join(sorted(set(creadoras[f])))}", t.id, c)
            if (f, "") not in propias:
                error("CREA_INCOHERENTE", f"{t.id}: «crea» declara «{c}», que no figura en su propiedad sin «#ID»", t.id, c)

    # regla 5: siembra
    for t in no_hechas:
        for s in t.siembra:
            archivo, _, id_ = s.partition("#")
            f, id_ = normalizar_archivo(archivo), id_.strip()
            if not f or not id_:
                error("SIEMBRA_INCOHERENTE", f"{t.id}: «siembra» exige «ruta#ID» y se declaró «{s}»", t.id, s)
                continue
            if not any(separar_entrada(e)[1] == "" and lenguajes_se_cortan(separar_entrada(e)[0], f) for e in t.propiedad):
                error("SIEMBRA_INCOHERENTE", f"{t.id}: «siembra» «{s}» exige poseer «{archivo}» entero y no lo posee", t.id, s)
            if id_ not in por_id:
                error("SIEMBRA_INCOHERENTE", f"{t.id}: «siembra» «{s}» nombra una tarea que no existe", t.id, s)
            elif t.id not in ancestros[id_]:
                error("SIEMBRA_INCOHERENTE", f"{t.id}: «siembra» «{s}» exige que {id_} dependa transitivamente de {t.id}", t.id, s)

    def siembra_de_ancestro(t: Tarea, f: str, id_: str) -> bool:
        return any((f, id_) in {(normalizar_archivo(a.partition("#")[0]), a.partition("#")[2].strip()) for a in por_id[u].siembra}
                   for u in ancestros[t.id])

    def crea_ancestro(t: Tarea, f: str) -> bool:
        return any(normalizar_archivo(c) == f for u in ancestros[t.id] for c in por_id[u].crea)

    # reglas 1 a 3: cada entrada
    for t in no_hechas:
        propias_crea = {normalizar_archivo(c) for c in t.crea}
        for e in t.propiedad:
            f, seccion = separar_entrada(e)
            if es_comodin(e):
                carpeta = _prefijo_fijo(e)
                creadas = propias_crea | {normalizar_archivo(c) for u in ancestros[t.id] for c in por_id[u].crea}
                existe = not carpeta or any(r.startswith(carpeta + "/") for r in rutas) or any(c.startswith(carpeta + "/") for c in creadas)
                if not existe:
                    aviso("COMODIN_SIN_BASE", f"{t.id}: el comodín «{e}» no tiene base: la carpeta «{carpeta}» no existe en el árbol ni la crea ella o una ancestro")
                continue
            if f in rutas:
                if not seccion:
                    continue
                if f not in lecturas:
                    lecturas[f] = leer(rutas[f])
                texto = lecturas[f]
                if es_configuracion(f) and texto is not None:
                    continue  # TICKET-295: la sección es una clave de primer nivel (o el archivo entero si no se analiza)
                if texto is None:
                    error("PROP_ILEGIBLE", f"{t.id}: no se pudo leer «{rutas[f]}» para comprobar la marca de «{seccion}»", t.id, e)
                elif not (tiene_marca(texto, seccion) or siembra_de_ancestro(t, f, seccion)):
                    error("PROP_SIN_MARCA", f"{t.id}: «{e}» no tiene la marca «=== {seccion} ===» en el archivo ni una ancestro que la siembre", t.id, e)
                elif f.endswith(".py") and f not in avisados:
                    fuera = imports_dentro_de_secciones(texto)
                    if fuera:
                        avisados.add(f)
                        aviso("IMPORT_EN_SECCION", f"«{rutas[f]}»: import en las líneas {', '.join(map(str, fuera[:5]))}, después de la primera marca de sección; "
                              "la cabecera anterior a las marcas es zona compartida de solo añadir: súbalos allí (TICKET-292)")
                continue
            if (f in propias_crea and not seccion) or (crea_ancestro(t, f) and (not seccion or siembra_de_ancestro(t, f, seccion))):
                continue
            otras = sorted({u.id for u in no_hechas if u.id != t.id and f in (set(map(normalizar_archivo, u.crea)) | {
                separar_entrada(p)[0] for p in u.propiedad if not es_comodin(p) and not separar_entrada(p)[1]})})
            if otras:  # TICKET-293: otra tarea abierta declara la ruta; no se sugiere un archivo parecido
                quien = ", ".join(otras)
                if seccion:
                    error("PROP_SIN_CREADORA", f"{t.id}: «{e}» no existe en el árbol; la declara {quien}: si la crea, {t.id} debe depender de ella y la creadora sembrar «{seccion}»", t.id, e)
                else:
                    aviso("CREACION_IMPLICITA", f"{t.id}: «{e}» no existe en el árbol; la declara {quien} (si la crea, {t.id} debe depender de ella)")
                continue
            sugerencias, fuerte = sugerir_ruta(f, rutas)
            pista = f" ¿quiso decir {' o '.join(sugerencias)}?" if sugerencias else ""
            if sugerencias and (fuerte or seccion):
                error("PROP_RUTA_INEXISTENTE", f"{t.id}: «{e}» no existe en el árbol.{pista}", t.id, e)
            elif seccion:
                error("PROP_SIN_CREADORA", f"{t.id}: «{e}» no existe en el árbol y ninguna creadora ancestro la crea y siembra «{seccion}»", t.id, e)
            else:
                aviso("CREACION_IMPLICITA", f"{t.id}: «{e}» no existe y ninguna tarea declara «crea»; se toma como creación implícita.{pista}")
    return hallazgos


# ¤molde
def _git(raiz: Path, *argumentos: str) -> bytes:
    resultado = subprocess.run(["git", "-C", str(raiz), *argumentos], capture_output=True)
    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr.decode("utf-8", "replace").strip() or f"git {argumentos[0]} falló")
    return resultado.stdout


# ¤molde
def leer_arbol_git(raiz: Path) -> Tuple[Optional[Tuple[str, List[str]]], str]:
    """((sha de HEAD, rutas de ``git ls-tree -r --name-only HEAD``), "") o (None, motivo) si no hay árbol utilizable.

    Solo vale si ``raiz`` es la raíz del repositorio: una carpeta dentro de un repositorio ajeno no tiene su árbol.
    """
    try:
        superior = _git(raiz, "rev-parse", "--show-toplevel").decode("utf-8").strip()
        if not os.path.samefile(superior, raiz):
            return None, f"{raiz} no es la raíz de un repositorio de git"
        sha = _git(raiz, "rev-parse", "--short", "HEAD").decode("utf-8").strip()
        salida = _git(raiz, "ls-tree", "-r", "--name-only", "-z", "HEAD")
    except (OSError, RuntimeError, UnicodeDecodeError) as exc:
        return None, str(exc)
    return (sha, [r for r in salida.decode("utf-8").split("\0") if r]), ""


# ¤molde
def leer_archivo_git(raiz: Path, ruta: str) -> Optional[str]:
    """Texto de ``ruta`` en HEAD, o None si no se pudo leer."""
    try:
        return _git(raiz, "show", f"HEAD:{ruta}").decode("utf-8")
    except (OSError, RuntimeError, UnicodeDecodeError):
        return None


# --------------------------------------------------------------------------- exenciones con caducidad (TICKET-294)
#
# Una exención tapa un error de R-PROP-EXISTE medido, no una regla: la clave es (ficha, entrada). Deja de ser válida en
# cuanto el error desaparece. La retirada la decide el árbol (el mismo HEAD con que se valida) y su registro es el commit
# que borra la línea; por eso el modo árbitro no escribe y falla, y el modo local retira y lo lista.

ARCHIVO_EXENCIONES = "_exenciones_propiedad.txt"
REFERENCIA_EXENCIONES = "origin/main"  # TICKET-300: la lista publicada con la que se compara; solo puede decrecer
VARIABLE_REFERENCIA = "ZERAG_REFERENCIA_EXENCIONES"  # equivale a --referencia; la opción prevalece


@dataclass(frozen=True)
# ¤molde
class Exencion:
    ficha: str
    entrada: str
    motivo: str
    linea: int  # número de línea (desde 1) en el archivo

    @property
    def clave(self) -> Tuple[str, str]:
        return self.ficha, self.entrada

    def texto(self) -> str:
        return f"{self.ficha}|{self.entrada}"


# ¤molde
def ruta_exenciones(raiz: Path) -> Path:
    return raiz / "governance" / "tareas" / ARCHIVO_EXENCIONES


# ¤molde
def leer_exenciones(texto: str) -> Tuple[List[Exencion], List[str]]:
    """(exenciones, errores) de un archivo ``ficha|entrada|motivo``; se ignoran las líneas vacías y los ``#``.

    El motivo es obligatorio y una clave no puede repetirse: una exención sin motivo no dice qué se aceptó.
    """
    exenciones: List[Exencion] = []
    errores: List[str] = []
    vistas: Dict[Tuple[str, str], int] = {}
    for n, linea in enumerate(texto.lstrip("\ufeff").replace("\r\n", "\n").split("\n"), start=1):
        if not linea.strip() or linea.lstrip().startswith("#"):
            continue
        partes = [p.strip() for p in linea.split("|", 2)]
        if len(partes) != 3 or not all(partes):
            errores.append(f"exenciones l.{n}: se esperaba «ficha|entrada|motivo» con los tres campos no vacíos")
            continue
        e = Exencion(partes[0], partes[1], partes[2], n)
        if e.clave in vistas:
            errores.append(f"exenciones l.{n}: «{e.texto()}» repetida (ya está en la l.{vistas[e.clave]})")
            continue
        vistas[e.clave] = n
        exenciones.append(e)
    return exenciones, errores


# ¤molde
def aplicar_exenciones(hallazgos: List[Hallazgo], exenciones: List[Exencion]) -> Tuple[List[Hallazgo], List[Exencion], List[Exencion]]:
    """(hallazgos que siguen, exenciones que tapan un error, exenciones caducadas).

    Solo un error con ficha y entrada se puede eximir; los avisos y los errores sin clave pasan intactos. Una exención
    que no tapa ningún error está caducada, sea porque se resolvió o porque nunca coincidió con uno.
    """
    claves = {e.clave for e in exenciones}
    vivos = {(h.ficha, h.entrada) for h in hallazgos if h.bloquea and h.ficha and h.entrada}
    siguen = [h for h in hallazgos if not (h.bloquea and (h.ficha, h.entrada) in claves)]
    return siguen, [e for e in exenciones if e.clave in vivos], [e for e in exenciones if e.clave not in vivos]


# ¤molde
def exenciones_nuevas(actuales: Iterable[Exencion], publicadas: Iterable[Exencion]) -> List[Exencion]:
    """Las exenciones de ``actuales`` cuya clave (ficha, entrada) no está en ``publicadas``; el motivo no cuenta."""
    previas = {e.clave for e in publicadas}
    return [e for e in actuales if e.clave not in previas]


# ¤molde
def leer_exenciones_publicadas(raiz: Path, referencia: str = REFERENCIA_EXENCIONES) -> Tuple[Optional[str], str]:
    """(texto del archivo de exenciones en ``referencia``, "") o (None, motivo) si la referencia no existe.

    Una referencia que existe pero no tiene el archivo devuelve "": ninguna exención estaba publicada.
    """
    try:
        _git(raiz, "rev-parse", "--verify", "--quiet", f"{referencia}^{{commit}}")
    except (OSError, RuntimeError) as exc:
        return None, str(exc) or f"{referencia} no existe"
    ruta = ruta_exenciones(raiz).relative_to(raiz).as_posix()
    try:
        return _git(raiz, "show", f"{referencia}:{ruta}").decode("utf-8"), ""
    except (OSError, RuntimeError, UnicodeDecodeError):
        return "", ""


# ¤molde
def tramitar_exenciones(raiz: Path, informe: Informe, hallazgos: List[Hallazgo], arbitro: bool,
                        referencia: str = REFERENCIA_EXENCIONES) -> List[Hallazgo]:
    """Aplica las exenciones de ``raiz`` a los hallazgos del árbol y devuelve los que siguen en pie.

    El generador nunca escribe el archivo de exenciones, en ningún modo (TICKET-300): es una declaración de su dueño,
    como las tareas. Una exención caducada o que no está en ``referencia`` es un error en modo árbitro y un aviso en modo
    local, y la salida dice qué línea retirar. Con exenciones, una ``referencia`` que no resuelve es un error en modo
    árbitro y un aviso por la salida de error en modo local. Un archivo de exenciones mal formado es un error.
    """
    ruta = ruta_exenciones(raiz)
    try:
        with open(ruta, encoding="utf-8", newline="") as f:
            texto = f.read()
    except FileNotFoundError:
        return hallazgos
    except (OSError, UnicodeDecodeError) as exc:
        informe.errores.append(f"[exenciones] no se pudo leer {ARCHIVO_EXENCIONES}: {exc}")
        return hallazgos
    exenciones, errores = leer_exenciones(texto)
    if errores:
        informe.errores += [f"[exenciones] {e}" for e in errores]
        return hallazgos
    destino = informe.errores if arbitro else informe.avisos
    archivo = f"governance/tareas/{ARCHIVO_EXENCIONES}"
    if exenciones:
        publicado, motivo = leer_exenciones_publicadas(raiz, referencia)
        if publicado is None and arbitro:
            informe.errores.append(f"[exenciones] la referencia publicada «{referencia}» no resuelve ({motivo}): en modo "
                                   f"árbitro no se puede comprobar que la lista solo decrece; pase la base de la "
                                   f"integración con --referencia <rev> o ZERAG_REFERENCIA_EXENCIONES")
        elif publicado is None:
            print(f"AVISO: sin referencia {referencia} ({motivo}): no se comprobó que la lista de exenciones "
                  f"solo decrezca (TICKET-300).", file=sys.stderr)
        else:
            consecuencia = ("la lista solo decrece; corrija la ficha o retire la línea" if arbitro
                            else "el modo árbitro la rechazará (la lista solo decrece)")
            destino += [f"[exenciones] la exención «{e.texto()}» (l.{e.linea}) no está en {referencia}: {consecuencia}"
                        for e in exenciones_nuevas(exenciones, leer_exenciones(publicado)[0])]
    siguen, vigentes, caducadas = aplicar_exenciones(hallazgos, exenciones)
    informe.medidas["exenciones"] = {"vigentes": [e.texto() for e in vigentes], "caducadas": [e.texto() for e in caducadas]}
    destino += [f"[exenciones] la exención «{e.texto()}» (l.{e.linea}) ya no tapa ningún error: retire la línea "
                f"{e.linea} de {archivo} (motivo: {e.motivo}); el generador no escribe ese archivo" for e in caducadas]
    if vigentes:
        print(f"Exenciones vigentes: {len(vigentes)}.")
    return siguen


# --------------------------------------------------------------------------- índice

# ¤molde
def generar_indice(tareas: List[Tarea]) -> str:
    """Solo lo estable: el ESTADO vive únicamente en la especificación de cada tarea."""
    ordenadas = sorted(tareas, key=lambda t: (t.ola, t.id))
    filas = ["| ID | Tarea | Ola | Sala | Depende de |", "| :--- | :--- | :--- | :--- | :--- |"]
    for t in ordenadas:
        filas.append(f"| [{t.id}](../tareas/{t.id}.md) | {t.titulo} | {t.ola} | `{t.sala}` | "
                     f"{', '.join(t.depende_de) or '—'} |")
    cabecera = (f"**{len(ordenadas)} tareas.** El estado de cada una está en su especificación "
                "(`python scripts/generar_indice_tareas.py --estado`).")
    return "\n".join([INICIO, cabecera, "", *filas, FIN])


# ¤molde
def resumen_estado(tareas: List[Tarea]) -> str:
    lineas = [f"{t.ola:8} {t.id:10} {t.estado:10} {t.titulo}" for t in sorted(tareas, key=lambda t: (t.ola, t.id))]
    cuentas = ", ".join(f"{sum(1 for t in tareas if t.estado == e)} {e}" for e in ESTADOS if any(t.estado == e for t in tareas))
    return "\n".join([*lineas, "", f"{len(tareas)} tareas: {cuentas or 'ninguna'}"])


# ¤molde
def extraer_indice(texto: str) -> Optional[str]:
    t = texto.replace("\r\n", "\n")
    if INICIO not in t or FIN not in t:
        return None
    return t[t.index(INICIO): t.index(FIN) + len(FIN)]


# ¤molde
def aplicar_indice(texto: str, indice: str) -> str:
    fin_linea = "\r\n" if "\r\n" in texto else "\n"
    t = texto.replace("\r\n", "\n")
    actual = extraer_indice(t)
    if actual is None:
        raise ValueError("TASKS.md no tiene las marcas del índice")
    return t.replace(actual, indice, 1).replace("\n", fin_linea)


# =========================================================================== LOPDP (GOB-05)
# Lo que la copia de LOPDP conserva y el molde no tiene. Cada bloque dice por qué. Lo que deba subir al molde se pide
# como ticket de ZERAG (descripción del PR de GOB-05); no se copia código de LOPDP hacia ZERAG.

EXENCIONES = ruta_exenciones(RAIZ)


def rutas_se_solapan(a: str, b: str) -> bool:
    """Nombre de LOPDP de ``mismo_archivo``: lo usan scripts/verificar_reparto.py y scripts/verificar_alcance_pr.py."""
    return mismo_archivo(a, b)


def propiedades_se_solapan(p: str, q: str) -> bool:
    """Nombre de LOPDP de ``se_pisan``: lo usa scripts/verificar_reparto.py."""
    return se_pisan(p, q)


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


def validar(tareas: List[Tarea], salas: Optional[set] = None, *, arbol: Optional[Iterable[str]] = None,
            leer: Optional[Callable[[str], Optional[str]]] = None, base: str = "HEAD",
            avisos: Optional[List[str]] = None, texto_exenciones: Optional[str] = None,
            raiz: Optional[Path] = None, arbitro: bool = False, referencia: str = REFERENCIA_EXENCIONES) -> List[str]:
    """API de LOPDP sobre el molde; la usan las pruebas y ``main``. Devuelve los errores y suma los avisos a ``avisos``.

    1. Estructura: ``validar_estructura`` del molde, el catálogo de salas del PRD, las olas y, con ``texto_exenciones``,
       las secciones del archivo de exenciones (CI-22). Con errores aquí no se sigue.
    2. Propiedad exclusiva: ``encontrar_conflictos`` del molde, con las claves de configuración de ``raiz`` (TICKET-295).
    3. Con ``arbol``: R-PROP-EXISTE (``validar_contra_arbol``) y, con ``raiz``, sus exenciones (``tramitar_exenciones``:
       una caducada o nueva frente a ``referencia`` avisa en local y falla en modo árbitro; el archivo no se escribe).
    """
    errores: List[str] = []
    if texto_exenciones is not None:  # CI-22
        errores += validar_secciones(texto_exenciones, tareas)
    errores += validar_estructura(tareas)
    for t in tareas:
        if salas is not None:
            for sala in (s.strip() for s in t.sala.split(",")):
                if sala not in salas:
                    errores.append(f"{t.id}: la sala «{sala}» no existe en el catálogo del PRD (apartado 5.2)")
        if t.ola not in OLAS:
            errores.append(f"{t.id}: ola inválida «{t.ola}» (válidas: {', '.join(OLAS)})")
    if errores:
        return errores
    conflictos, _ = encontrar_conflictos(tareas, _ancestros(tareas), archivos_enteros(raiz or RAIZ, tareas))
    errores += [c.texto() for c in conflictos]
    if arbol is None:
        return errores
    hallazgos = validar_contra_arbol(tareas, arbol, leer or (lambda _r: ""), base)
    propios: List[str] = []
    if raiz is not None:
        informe = Informe(tareas=tareas, indice="", conflictos=[], base=Base(), errores=[], avisos=[], medidas={})
        hallazgos = tramitar_exenciones(raiz, informe, hallazgos, arbitro, referencia)
        errores += informe.errores
        propios += informe.avisos
    for h in hallazgos:
        (errores if h.bloquea else propios).append(f"[propiedad_existe] {h.mensaje}")
    if avisos is not None:
        avisos += propios
    return errores


def modo_arbitro(bandera: bool, entorno: Dict[str, str]) -> bool:
    """Modo árbitro del molde: ``--arbitro`` o ``ZERAG_ARBITRO=1``."""
    return bandera or entorno.get("ZERAG_ARBITRO") == "1"


_MOTIVOS = {"PROP_RUTA_INEXISTENTE": "ruta equivocada", "PROP_SIN_MARCA": "sección sin marca ni siembra de una ancestro",
            "PROP_SIN_CREADORA": "sección en un archivo que no existe y que no crea ninguna ancestro",
            "PROP_ILEGIBLE": "archivo ilegible", "CREA_YA_EXISTE": "«crea» de un archivo que ya existe",
            "CREA_DOBLE": "varias creadoras", "CREA_INCOHERENTE": "«crea» incoherente",
            "SIEMBRA_INCOHERENTE": "«siembra» incoherente"}


def generar_exenciones(tareas: List[Tarea], arbol: Iterable[str], leer: Callable[[str], Optional[str]], base: str) -> int:
    """Medición única de la fase 1 (COORDINACION C.13 de ZERAG). Se niega si la lista existe: solo decrece a mano."""
    if EXENCIONES.exists():
        print("ERROR: la lista de exenciones ya existe; solo puede decrecer y no se regenera")
        return 1
    hallazgos = [h for h in validar_contra_arbol(tareas, arbol, leer, base) if h.bloquea and h.ficha and h.entrada]
    filas = sorted({f"{h.ficha}|{h.entrada}|{_MOTIVOS.get(h.codigo, h.codigo)}" for h in hallazgos})
    lineas = [f"# Exenciones de R-PROP-EXISTE (ADPA-10), medidas una sola vez sobre {base}.",
              "# Formato: ficha|entrada|motivo. Solo puede decrecer: corrija la ficha y retire su línea.",
              *filas]
    EXENCIONES.write_text("\n".join(lineas) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(filas)} exenciones escritas en {EXENCIONES.name}")
    return 0


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Valida las fichas de tareas y genera su índice (copia de LOPDP del molde).")
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--verificar", action="store_true",
                      help="comprueba fichas e índice (por defecto); no escribe nada: sin --arbitro las exenciones "
                           "caducadas o nuevas solo avisan y dicen qué línea retirar")
    modo.add_argument("--escribir", action="store_true", help="genera el índice en governance/artefactos/_generado/ (CI-29)")
    modo.add_argument("--estado", action="store_true", help="imprime el estado de cada tarea")
    modo.add_argument("--tandas", action="store_true", help="imprime las tandas declaradas y el mínimo con archivos concretos")
    modo.add_argument("--generar-exenciones", action="store_true",
                      help="medición única de la fase 1 (COORDINACION C.13 de ZERAG); se niega si la lista ya existe")
    parser.add_argument("--avisos", action="store_true", help="imprime también los avisos de fase 1 de R-PROP-EXISTE")
    parser.add_argument("--arbitro", action="store_true",
                        help="modo árbitro, el de la integración: no escribe nada; una exención caducada o que no está en "
                             "la referencia, o una referencia que no resuelve, es un error (también con ZERAG_ARBITRO=1)")
    parser.add_argument("--referencia", metavar="REV",
                        help=f"revisión publicada con la que se compara la lista de exenciones (por defecto "
                             f"{VARIABLE_REFERENCIA} o, sin ella, {REFERENCIA_EXENCIONES})")
    args = parser.parse_args(argv)
    arbitro = modo_arbitro(args.arbitro, dict(os.environ))
    referencia = args.referencia or os.environ.get(VARIABLE_REFERENCIA) or REFERENCIA_EXENCIONES

    tareas, errores = cargar_tareas()
    salas = salas_del_prd(PRD_MD.read_text(encoding="utf-8"))
    if not salas:
        errores.append("el PRD no declara su catálogo de salas (apartado 5.2)")
    leido, motivo = leer_arbol_git(RAIZ)
    if leido is None:  # LOPDP: sin árbol de git es un error; el molde solo avisa por la salida de error
        errores.append(f"no se pudo leer el árbol de HEAD con git: {motivo}")
        arbol, base = None, "HEAD"
    else:
        arbol, base = set(leido[1]), f"HEAD {leido[0]}"

    def leer(ruta: str) -> Optional[str]:
        return leer_archivo_git(RAIZ, ruta)

    if args.generar_exenciones:
        if arbol is None:
            for e in errores:
                print("ERROR:", e)
            return 1
        return generar_exenciones(tareas, arbol, leer, base)
    texto_exenciones = EXENCIONES.read_text(encoding="utf-8") if EXENCIONES.exists() else None
    avisos: List[str] = []
    errores += validar(tareas, salas or None, arbol=arbol, leer=leer, base=base, avisos=avisos,
                       texto_exenciones=texto_exenciones, raiz=RAIZ, arbitro=arbitro, referencia=referencia)
    if arbol is not None:
        vivas = [t for t in tareas if t.estado != ESTADO_HECHA]
        exenciones = len(leer_exenciones(texto_exenciones)[0]) if texto_exenciones else 0
        de_exenciones = [a for a in avisos if a.startswith("[exenciones]")]
        print(f"Base: {base}, {len(vivas)} fichas no hechas, {sum(len(t.propiedad) for t in vivas)} entradas"
              f" ({exenciones} exenciones, {len(avisos) - len(de_exenciones)} avisos de fase 1)")
        for a in avisos:  # las de exenciones siempre: dicen qué línea retirar
            if args.avisos or a in de_exenciones:
                print("AVISO:", a)
    if args.tandas:
        print(texto_tandas(medir_tandas(tareas, archivos_enteros(RAIZ, tareas))) if not errores
              else "Tandas: no medidas porque hay errores.")
        for e in errores:
            print("ERROR:", e)
        return 1 if errores else 0
    if args.estado:
        print(resumen_estado(tareas))
        return 1 if errores else 0
    indice = generar_indice(tareas).replace("](../tareas/", "](../../tareas/")
    cuerpo = "# Índice de tareas (generado, no versionado)\n\n" + indice + "\n"
    if args.escribir and not errores:
        INDICE_GENERADO.parent.mkdir(parents=True, exist_ok=True)
        with open(INDICE_GENERADO, "w", encoding="utf-8", newline="\n") as f:
            f.write(cuerpo)
        print(f"Índice generado en {INDICE_GENERADO.relative_to(RAIZ)}: {len(tareas)} tareas.")
        return 0
    with open(TASKS_MD, encoding="utf-8", newline="") as f:
        if INICIO in f.read():
            errores.append("TASKS.md versiona el índice de tareas: se genera con --escribir en _generado/ (CI-29)")
    if INDICE_GENERADO.exists():
        with open(INDICE_GENERADO, encoding="utf-8", newline="") as f:
            if f.read() != cuerpo:
                errores.append("el índice generado está desactualizado: ejecute --escribir")
    for e in errores:
        print("ERROR:", e)
    if not errores:
        print(f"OK: {len(tareas)} tareas, independencia verificada.")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
