# ¤ci-cd ¤arbitro
"""CI-16 · Ninguna prueba de interfaz queda fuera de todos los proyectos del CI.

En CI, `frontend/playwright.config.ts` define dos proyectos: `produccion` corre todo salvo
`SOLO_DESARROLLO`; `desarrollo` corre solo `SOLO_DESARROLLO`. Una especificación que se salta en
`produccion` (`test.skip(x.project.name === "produccion", ...)`) y no está en `SOLO_DESARROLLO` no
corre en ningún proyecto: se pudre sin aviso (BIB-115, PR #417: eran 16, y tres ya fallaban).

Predicado: ∀ s ∈ specs : salta_en_produccion(s) ⟹ s ∈ SOLO_DESARROLLO ∨ s ∈ EXCEPCIONES vigentes.

Excepción con caducidad: vale mientras su tarea no esté `hecha` en `governance/tareas/<ID>.md`.
Si la tarea está hecha y el archivo sigue fuera, la prueba falla: la excepción no se olvida.

Sin navegador: lee la configuración y las especificaciones como texto.

Mutación documentada (también automatizada abajo, sobre copias temporales):
- quitar una entrada de `SOLO_DESARROLLO` hace fallar `test_ninguna_especificacion_queda_sin_proyecto`
  y el mensaje nombra ese archivo;
- una excepción cuya tarea está `hecha` caduca y hace fallar la prueba (con una excepción sintética).
"""
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = RAIZ / "frontend" / "playwright.config.ts"
PRUEBAS = RAIZ / "frontend" / "tests"
TAREAS = RAIZ / "governance" / "tareas"
FUERA = ("integracion", "humo")  # tienen su propia configuración (playwright.integracion / .humo)

# {especificación relativa a frontend/tests: tarea que la arregla}. Vacío desde el cierre de BIB-401 (2026-11-13).
EXCEPCIONES: dict[str, str] = {}

SALTA_EN_PRODUCCION = re.compile(r"""test\.skip\(\s*\w+\.project\.name\s*===\s*["']produccion["']""")


def patrones_solo_desarrollo(config: Path = CONFIG) -> list[str]:
    texto = config.read_text(encoding="utf-8")
    bloque = re.search(r"const SOLO_DESARROLLO\s*=\s*\[(.*?)\];", texto, flags=re.S)
    assert bloque, "No se encontró `const SOLO_DESARROLLO = [...]` en playwright.config.ts"
    return re.findall(r"""["']([^"']+)["']""", bloque.group(1))


def _glob_a_regex(patron: str) -> re.Pattern:
    """Glob de Playwright (minimatch) a regex sobre la ruta con «/»: `**/` = cualquier prefijo."""
    partes = []
    i = 0
    while i < len(patron):
        if patron.startswith("**/", i):
            partes.append(r"(?:.*/)?")
            i += 3
        elif patron.startswith("**", i):
            partes.append(r".*")
            i += 2
        elif patron[i] == "*":
            partes.append(r"[^/]*")
            i += 1
        elif patron[i] == "?":
            partes.append(r"[^/]")
            i += 1
        else:
            partes.append(re.escape(patron[i]))
            i += 1
    return re.compile(r"(?:^|.*/)" + "".join(partes) + r"$")


def coincide(relativa: str, patrones: list[str]) -> bool:
    ruta = f"frontend/tests/{relativa}"
    return any(_glob_a_regex(p).match(ruta) for p in patrones)


def especificaciones_que_saltan_en_produccion(pruebas: Path = PRUEBAS) -> dict[str, int]:
    """{ruta relativa a frontend/tests: línea del primer `test.skip` de producción}."""
    encontradas = {}
    for archivo in sorted(pruebas.rglob("*.spec.ts")):
        relativa = archivo.relative_to(pruebas).as_posix()
        if relativa.split("/")[0] in FUERA:
            continue
        for numero, linea in enumerate(archivo.read_text(encoding="utf-8").splitlines(), start=1):
            if SALTA_EN_PRODUCCION.search(linea):
                encontradas[relativa] = numero
                break
    return encontradas


def estado_de_tarea(tarea: str, tareas: Path = TAREAS) -> str:
    ficha = (tareas / f"{tarea}.md").read_text(encoding="utf-8")
    estado = re.search(r'^estado\s*=\s*"([^"]+)"', ficha, flags=re.M)
    assert estado, f"governance/tareas/{tarea}.md no declara `estado`"
    return estado.group(1)


def sin_proyecto(config: Path = CONFIG, pruebas: Path = PRUEBAS, tareas: Path = TAREAS,
                 excepciones: dict[str, str] = EXCEPCIONES) -> list[str]:
    """Especificaciones que no correrían en ningún proyecto del CI, con lo que hay que añadir."""
    patrones = patrones_solo_desarrollo(config)
    faltan = []
    for relativa, linea in especificaciones_que_saltan_en_produccion(pruebas).items():
        if coincide(relativa, patrones):
            continue
        tarea = excepciones.get(relativa)
        if tarea and estado_de_tarea(tarea, tareas) != "hecha":
            continue
        motivo = f" (la excepción de {tarea} caducó: la tarea está hecha)" if tarea else ""
        faltan.append(f'frontend/tests/{relativa}:{linea} se salta en «produccion» y no está en '
                      f'SOLO_DESARROLLO{motivo}. Añade "**/{relativa}" a SOLO_DESARROLLO en '
                      f'frontend/playwright.config.ts.')
    return faltan


# ----------------------------------------------------------------------------- árbitro

def test_ninguna_especificacion_queda_sin_proyecto():
    faltan = sin_proyecto()
    assert not faltan, "\n".join(faltan)


def test_el_inventario_ve_las_especificaciones_de_biblioteca():
    saltan = especificaciones_que_saltan_en_produccion()
    assert len(saltan) >= 17, sorted(saltan)
    assert "biblioteca/descarga.spec.ts" in saltan and "biblioteca/plantillas-cuenta.spec.ts" in saltan
    assert not any(r.split("/")[0] in FUERA for r in saltan)


def test_las_excepciones_son_pocas_y_apuntan_a_tareas_reales():
    assert len(EXCEPCIONES) <= 1, EXCEPCIONES
    for relativa, tarea in EXCEPCIONES.items():
        assert (PRUEBAS / relativa).is_file(), relativa
        # Mientras la excepción vale, el archivo no está en SOLO_DESARROLLO (si lo estuviera, sobra).
        if estado_de_tarea(tarea) != "hecha":
            assert not coincide(relativa, patrones_solo_desarrollo()), f"{relativa}: quita la excepción"


@pytest.mark.parametrize(("patron", "ruta", "esperado"), [
    ("**/biblioteca/ficha.spec.ts", "biblioteca/ficha.spec.ts", True),
    ("**/tamano/ficha.spec.ts", "biblioteca/ficha.spec.ts", False),
    ("**/biblioteca/*.spec.ts", "biblioteca/descarga.spec.ts", True),
    ("**/biblioteca/acceso.spec.ts", "biblioteca/acceso.spec.ts.bak", False),
])
def test_los_patrones_se_leen_como_playwright(patron, ruta, esperado):
    assert coincide(ruta, [patron]) is esperado


# ----------------------------------------------------------------------------- mutaciones

def _copia(tmp_path: Path, config: str | None = None, estado_bib401: str | None = None) -> tuple[Path, Path]:
    config_copia = tmp_path / "playwright.config.ts"
    config_copia.write_text(config if config is not None else CONFIG.read_text(encoding="utf-8"), encoding="utf-8")
    tareas = tmp_path / "tareas"
    tareas.mkdir()
    ficha = (TAREAS / "BIB-401.md").read_text(encoding="utf-8")
    if estado_bib401:
        ficha = re.sub(r'^estado\s*=\s*"[^"]+"', f'estado = "{estado_bib401}"', ficha, count=1, flags=re.M)
    (tareas / "BIB-401.md").write_text(ficha, encoding="utf-8")
    return config_copia, tareas


def test_mutacion_quitar_una_entrada_falla_y_nombra_el_archivo(tmp_path):
    original = CONFIG.read_text(encoding="utf-8")
    entrada = '  "**/biblioteca/descarga.spec.ts",\n'
    assert entrada in original.replace("\r\n", "\n")
    config, tareas = _copia(tmp_path, config=original.replace("\r\n", "\n").replace(entrada, ""))
    faltan = sin_proyecto(config=config, tareas=tareas)
    assert len(faltan) == 1 and faltan[0].startswith("frontend/tests/biblioteca/descarga.spec.ts:"), faltan
    assert '"**/biblioteca/descarga.spec.ts"' in faltan[0]


def test_mutacion_bib401_hecha_hace_caducar_la_excepcion(tmp_path):
    original = CONFIG.read_text(encoding="utf-8").replace("\r\n", "\n")
    entrada = '  "**/biblioteca/plantillas-cuenta.spec.ts",\n'
    assert entrada in original
    sintetica = {"biblioteca/plantillas-cuenta.spec.ts": "BIB-401"}
    config, tareas = _copia(tmp_path, config=original.replace(entrada, ""), estado_bib401="en_curso")
    assert sin_proyecto(config=config, tareas=tareas, excepciones=sintetica) == []
    (tmp_path / "hecha").mkdir()
    config, tareas = _copia(tmp_path / "hecha", config=original.replace(entrada, ""), estado_bib401="hecha")
    faltan = sin_proyecto(config=config, tareas=tareas, excepciones=sintetica)
    assert len(faltan) == 1 and "plantillas-cuenta.spec.ts" in faltan[0] and "caducó" in faltan[0], faltan
