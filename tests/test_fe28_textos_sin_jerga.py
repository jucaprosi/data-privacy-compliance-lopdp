# ¤¤qa-engineer
# ¤frontend-ide ¤arbitro
"""FE-28: textos de interfaz sin jerga técnica, sin navegador (governance/tareas/FE-28.md, árbitro 2 a 4).

Busca en `frontend/src/**/*.tsx` el texto de JSX, los atributos `title`, `aria-label`, `placeholder`,
`alt` y `label`, y las cadenas que son hijas directas de JSX. Cubre las vistas que el recorrido de
`frontend/tests/textos/sin-jerga.spec.ts` no abre. Comparte con él la carpeta de excepciones.

`src/app/harness-roadmap/` queda fuera: es el arnés de pruebas de Roadmap, que solo existe fuera de
producción y no es interfaz del producto (`src/lib/auth/modo.ts`).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SRC = RAIZ / "frontend" / "src"
EXCEPCIONES = RAIZ / "frontend" / "tests" / "textos" / "excepciones"
FUERA = (SRC / "app" / "harness-roadmap",)

TERMINOS = ("adpa.view", "Zustand", "useAuditStore", "FastAPI", "endpoint", "Store:", "tenant-",
            "Invariante", "timebox", "Poka-Yoke", "SoD", "INV_", "Mutación")
JERGA = re.compile(r"adpa\.view|Zustand|useAuditStore|FastAPI|endpoint|Store:|tenant-|Invariante|timebox|"
                   r"Poka-Yoke|\bSoD\b|INV_|Mutaci[oó]n", re.IGNORECASE)

# Líneas de cada archivo de excepciones hoy: solo pueden bajar. Cada ficha dueña borra el suyo.
TOPE_EXCEPCIONES = {"FE-27.txt": 3, "TER-01.txt": 1, "DIAG-15.txt": 2}

_COMENTARIO = re.compile(r"\{/\*.*?\*/\}|/\*.*?\*/|(?<![:\"'`\\])//[^\n]*", re.S)
_TEXTO_JSX = re.compile(r"(?<=>)([^<>{}]+)(?=[<{])|(?<=\})([^<>{}]+)(?=<)")
_NO_ES_TEXTO = re.compile(r"[;=]|&&|\|\||\breturn\b|\bconst\b|\bif\b")
_ATRIBUTO = re.compile(r"\b(?:title|aria-label|placeholder|alt|label)="
                       r"(?:\"([^\"]*)\"|'([^']*)'|\{\s*[\"'`]([^\"'`]*)[\"'`]\s*\})")
_LITERAL = re.compile(r"\"((?:[^\"\\\n]|\\.)*)\"|'((?:[^'\\\n]|\\.)*)'|`((?:[^`\\]|\\.)*)`")
_HIJO = re.compile(r">\s*\{|\}\s*\{")
_CLASE = re.compile(r"className=\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|className=\"[^\"]*\"")
_INTERPOLACION = re.compile(r"\$\{[^{}]*\}")


def _cierre(codigo: str, inicio: int) -> int:
    nivel = 0
    for j in range(inicio, len(codigo)):
        nivel += codigo[j] == "{"
        nivel -= codigo[j] == "}"
        if nivel == 0:
            return j
    return len(codigo)


def fragmentos(codigo: str) -> list[tuple[int, str]]:
    """(línea, texto) de lo que el componente muestra o anuncia, sin comentarios ni código."""
    codigo = _COMENTARIO.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), codigo)

    def linea(pos: int) -> int:
        return codigo.count("\n", 0, pos) + 1

    hallados = []
    for m in _TEXTO_JSX.finditer(codigo):
        texto = m.group(1) or m.group(2)
        if texto.strip() and not _NO_ES_TEXTO.search(texto):
            hallados.append((linea(m.start()), texto))
    for m in _ATRIBUTO.finditer(codigo):
        hallados.append((linea(m.start()), next(g for g in m.groups() if g is not None)))
    for m in _HIJO.finditer(codigo):
        inicio = m.end() - 1
        expresion = _CLASE.sub("", codigo[inicio:_cierre(codigo, inicio) + 1])
        if "<" in expresion:  # lleva JSX dentro: lo cubren las búsquedas anteriores
            continue
        for lit in _LITERAL.finditer(expresion):
            hallados.append((linea(inicio), next(g for g in lit.groups() if g is not None)))
    return [(n, " ".join(_INTERPOLACION.sub("*", t).split())) for n, t in hallados]


def leer_excepciones() -> list[re.Pattern]:
    patrones = []
    for archivo in sorted(EXCEPCIONES.glob("*.txt")):
        for linea in archivo.read_text(encoding="utf-8").splitlines():
            if linea.strip() and not linea.startswith("#"):
                cadena = linea.split(" → ", 1)[1].strip()
                patrones.append(re.compile("^" + re.escape(cadena).replace(r"\*", ".*") + "$"))
    return patrones


def con_jerga(codigo: str, excepciones: list[re.Pattern]) -> list[str]:
    return [f"{n}: {t}" for n, t in fragmentos(codigo)
            if JERGA.search(t) and not any(e.match(t) for e in excepciones)]


def _componentes() -> list[Path]:
    return sorted(p for p in SRC.rglob("*.tsx") if not any(f in p.parents for f in FUERA))


# 2 · Prueba estática: ningún componente muestra jerga fuera de las excepciones.
def test_ningun_componente_muestra_jerga():
    excepciones = leer_excepciones()
    hallazgos = [f"{p.relative_to(RAIZ).as_posix()}:{h}"
                 for p in _componentes() for h in con_jerga(p.read_text(encoding="utf-8"), excepciones)]
    assert not hallazgos, "jerga técnica en la interfaz (corríjala o anótela en su excepción):\n" + "\n".join(hallazgos)


# 3 · Una prueba por término del filtro.
@pytest.mark.parametrize("termino", TERMINOS)
def test_el_filtro_detecta_cada_termino(termino):
    assert con_jerga(f"<span>Texto con {termino} dentro</span>", [])
    assert con_jerga(f'<button title="Texto con {termino}" />', [])
    assert con_jerga(f'<i aria-label="{termino} aquí" />', [])
    assert con_jerga(f'<p>{{"Cadena con {termino}"}}</p>', [])


def test_el_filtro_no_mira_el_codigo_ni_los_comentarios():
    codigo = ('import { useAuditStore } from "@/store/useAuditStore";\n'
              "// Zustand state\n"
              "const { timeboxRestante } = useAuditStore();\n"
              '<div className="tenant-x">{/* FastAPI */}<span>{formato(timeboxRestante)}</span></div>\n')
    assert con_jerga(codigo, []) == []


def test_la_excepcion_debe_coincidir_con_el_texto_entero():
    excepciones = [re.compile(r"^timebox$"), re.compile(r"^.*\.adpa\.view$")]
    assert con_jerga("<span>timebox</span><p>{`${vista}.adpa.view`}</p>", excepciones) == []
    assert con_jerga("<span>Queda un timebox</span>", excepciones) == ["1: Queda un timebox"]


def test_las_cadenas_corregidas_ya_no_estan():
    texto = "\n".join(p.read_text(encoding="utf-8") for p in _componentes())
    for cadena in ("Cargando solicitudes desde FastAPI", "Mutación Zustand", "motor Zustand", "Invariante SoD",
                   "endpoints del motor", "INV_LOPDP_DPO_INDEPENDENCE", "Timebox:"):
        assert cadena not in texto, cadena


# 4 · La carpeta de excepciones es exclusiva y solo decrece.
def test_la_carpeta_de_excepciones_solo_tiene_las_fichas_duenas():
    presentes = {p.name for p in EXCEPCIONES.iterdir()}
    assert presentes <= set(TOPE_EXCEPCIONES), f"archivo de excepciones no previsto: {sorted(presentes - set(TOPE_EXCEPCIONES))}"


@pytest.mark.parametrize("archivo", sorted(TOPE_EXCEPCIONES))
def test_ninguna_excepcion_crece(archivo):
    ruta = EXCEPCIONES / archivo
    if not ruta.exists():
        return  # la ficha dueña ya corrigió sus textos y lo borró
    lineas = [l for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    assert len(lineas) <= TOPE_EXCEPCIONES[archivo]
    assert all(" → " in l for l in lineas), "formato: «vista → cadena»"
