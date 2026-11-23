# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤qa-engineer
# ¤arbitro
"""CI-37: minutos de GitHub Actions por fusión reducidos a la mitad sin perder árbitros (§5 de la especificación).

El workflow se lee como texto: PyYAML no es dependencia del proyecto y `tests/_lector_yaml.py` no admite las
anclas ni los bloques `>-` del workflow. `CI37_WORKFLOW` permite probar un workflow fuera del repositorio antes
de que el propietario lo aplique; sin ella se lee `.github/workflows/zero-regression-pipeline.yml`.
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
RUTA_FLUJO = Path(os.environ.get("CI37_WORKFLOW") or RAIZ / ".github" / "workflows" / "zero-regression-pipeline.yml")
FLUJO = RUTA_FLUJO.read_text(encoding="utf-8").replace("\r\n", "\n")
CHECKS_DEL_RULESET = {"Arnés Físico Determinista", "Playwright Frontend"}
REPO = "jucaprosi/data-privacy-compliance-lopdp"


def _cargar(nombre: str):
    spec = importlib.util.spec_from_file_location(nombre, RAIZ / "scripts" / f"{nombre}.py")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)
    return modulo


av = _cargar("arbol_verificado")
mm = _cargar("medir_minutos_ci")


# ---- Lectura del workflow como texto -----------------------------------------------------------------

# ¤arbitro
def jobs(flujo: str = FLUJO) -> dict[str, str]:
    """Texto de cada job, por su id, entre `jobs:` y el job siguiente."""
    cuerpo = flujo[re.search(r"(?m)^jobs:\s*$", flujo).end():]
    marcas = list(re.finditer(r"(?m)^  ([A-Za-z0-9_-]+):\s*$", cuerpo))
    return {m.group(1): cuerpo[m.end():(marcas[i + 1].start() if i + 1 < len(marcas) else len(cuerpo))]
            for i, m in enumerate(marcas)}


# ¤arbitro
def nombre_del_job(texto: str) -> str:
    return re.search(r"(?m)^    name:\s*(.+?)\s*$", texto).group(1)


# ¤arbitro
def pasos(texto_job: str, flujo: str = FLUJO) -> list[str]:
    """Texto de cada paso del job, sin comentarios y con los alias `*ancla` resueltos al paso anclado."""
    sin_comentarios = "\n".join(l for l in texto_job.splitlines() if not l.strip().startswith("#"))
    crudos = re.split(r"(?m)^      - ", sin_comentarios.split("    steps:", 1)[1])[1:]
    resueltos = []
    for paso in crudos:
        alias = re.fullmatch(r"\*([\w-]+)\s*", paso)
        if alias:
            anclado = re.search(rf"(?ms)^      - &{alias.group(1)}\n(.*?)(?=^      - |\Z)", flujo)
            paso = anclado.group(1) if anclado else ""
        resueltos.append(paso)
    return resueltos


def _job_por_nombre(nombre: str, flujo: str = FLUJO) -> str:
    return next(t for t in jobs(flujo).values() if nombre_del_job(t) == nombre)


# ¤arbitro
def nombres_de_jobs(flujo: str = FLUJO) -> list[str]:
    return [nombre_del_job(t) for t in jobs(flujo).values()]


# ¤arbitro
def test_dos_jobs_con_los_nombres_del_ruleset():
    nombres = nombres_de_jobs()
    assert len(nombres) == 2 and set(nombres) == CHECKS_DEL_RULESET, nombres


AGREGADOR = ("  zero-regression:\n    name: Agregador\n    needs: [arnes]\n    runs-on: ubuntu-latest\n"
             "    steps:\n      - name: Veredicto\n        run: exit 0\n")


# ¤arbitro
def test_m1_un_job_agregador_aparte_da_rojo():
    mutado = FLUJO.replace("\n  playwright:\n", "\n" + AGREGADOR + "\n  playwright:\n", 1)
    assert mutado != FLUJO
    nombres = nombres_de_jobs(mutado)
    assert not (len(nombres) == 2 and set(nombres) == CHECKS_DEL_RULESET)


# ---- comprobar: un arnés por árbol (R1) --------------------------------------------------------------

SHA_PUSH = "a" * 40
CABEZA_PR = "b" * 40
COMMIT_DE_PRUEBA = "c" * 40
ARBOL = "d" * 40


def _zip(registro: dict) -> bytes:
    memoria = io.BytesIO()
    with zipfile.ZipFile(memoria, "w") as archivo:
        archivo.writestr(av.ARCHIVO, json.dumps(registro))
    return memoria.getvalue()


def _api(registro: dict | None, prs: list | None = None, verdes: bool = True):
    def api(ruta: str):
        if ruta.startswith(f"repos/{REPO}/commits/{SHA_PUSH}/pulls"):
            return prs if prs is not None else [{"merged_at": "2026-11-22T00:00:00Z", "merge_commit_sha": SHA_PUSH,
                                                 "head": {"sha": CABEZA_PR}}]
        if "/runs?event=pull_request" in ruta:
            assert f"head_sha={CABEZA_PR}" in ruta
            corridas = [{"id": 10, "conclusion": "success", "created_at": "2026-11-21T00:00:00Z"},
                        {"id": 11, "conclusion": "success", "created_at": "2026-11-22T00:00:00Z"}]
            return {"workflow_runs": corridas if verdes else []}
        if ruta.endswith(f"runs/11/artifacts?name={av.ARTEFACTO}"):
            return {"artifacts": [] if registro is None else [{"id": 7, "name": av.ARTEFACTO, "expired": False}]}
        raise AssertionError(f"ruta inesperada: {ruta}")
    return api


def _descargar(registro: dict):
    def descargar(ruta: str) -> bytes:
        assert ruta == f"repos/{REPO}/actions/artifacts/7/zip"
        return _zip(registro)
    return descargar


def _comprobar(registro: dict | None, modo_push: str = "completo", arbol: str = ARBOL, **kw) -> str:
    return av.comprobar(SHA_PUSH, modo_push, REPO, arbol=arbol, api=_api(registro, **kw),
                        descargar=_descargar(registro or {}))


def _registro(modo: str = "completo", arbol: str = ARBOL, commit: str = COMMIT_DE_PRUEBA) -> dict:
    return {"arbol": arbol, "commit": commit, "modo": modo}


def _api_rota(ruta: str):
    raise RuntimeError("HTTP 502")


# ¤arbitro
@pytest.mark.parametrize("registro, modo_push, extra, esperado", [
    # Mismo árbol, PR en completo: cubierto por la última corrida verde del PR, aunque el commit sea otro.
    (_registro("completo"), "completo", {}, "11"),
    (_registro("completo"), "salas", {}, "11"),
    (_registro("salas"), "salas", {}, "11"),
    # m2: el commit coincide con el del push pero el árbol no: un comparador de commits daría «cubierto».
    (_registro("completo", arbol="e" * 40, commit=SHA_PUSH), "completo", {}, ""),
    (_registro("completo", arbol="e" * 40), "completo", {}, ""),
    (_registro("salas"), "completo", {}, ""),
    (None, "completo", {}, ""),
    (_registro("completo"), "completo", {"prs": []}, ""),
    (_registro("completo"), "completo", {"verdes": False}, ""),
], ids=["mismo-arbol-completo", "completo-cubre-salas", "salas-cubre-salas", "mismo-commit-otro-arbol",
        "otro-arbol", "salas-no-cubre-completo", "sin-artefacto", "pr-no-encontrado", "sin-corrida-verde"])
def test_comprobar_arbol(registro, modo_push, extra, esperado):
    assert _comprobar(registro, modo_push, **extra) == esperado


# ¤arbitro
def test_comprobar_arbol_ante_un_fallo_de_la_api_deja_correr_el_arnes():
    assert av.comprobar(SHA_PUSH, "completo", REPO, arbol=ARBOL, api=_api_rota, descargar=_api_rota) == ""


# ¤arbitro
def test_registrar_escribe_arbol_commit_y_modo(tmp_path):
    salida = tmp_path / "arbol.json"
    av.registrar(str(salida), "salas", COMMIT_DE_PRUEBA, ARBOL)
    assert json.loads(salida.read_text(encoding="utf-8")) == _registro("salas")
    with pytest.raises(ValueError):
        av.registrar(str(salida), "otro", COMMIT_DE_PRUEBA, ARBOL)


# ---- Ningún árbitro se pierde (R3) -------------------------------------------------------------------

# Pasos del workflow anterior, por la orden que los identifica, en el orden en que corren dentro del job.
# La migración va antes del humo: el humo arranca FastAPI contra la base migrada y CI-17 exige un solo paso.
ARBITROS_DEL_ARNES = (
    ("alcance", "scripts/verificar_alcance_pr.py"),
    ("seleccion", "scripts/seleccionar_pruebas.py"),
    ("comprobar", "scripts/arbol_verificado.py comprobar"),
    ("migracion", "alembic upgrade heads"),
    ("humo", "playwright.humo.config.ts"),
    ("bom y huellas", "scripts/verificar_bom_huellas.py"),
    ("arnes por salas", "pytest $PRUEBAS"),
    ("arnes completo", "pytest tests/ -v -n auto"),
    ("compilacion del frontend", "run: npm run build"),
    ("registrar", "scripts/arbol_verificado.py registrar"),
    ("veredicto", "name: Un arnes corrio y paso"),
)
ARBITROS_DE_PLAYWRIGHT = (
    ("seleccion", "scripts/seleccionar_pruebas.py"),
    ("comprobar", "scripts/arbol_verificado.py comprobar"),
    ("playwright", "npx playwright test $SPECS"),
)


# ¤arbitro
def fallos_de_arbitros(flujo: str) -> list[str]:
    fallos = []
    for nombre, arbitros in (("Arnés Físico Determinista", ARBITROS_DEL_ARNES),
                             ("Playwright Frontend", ARBITROS_DE_PLAYWRIGHT)):
        try:
            lista = pasos(_job_por_nombre(nombre, flujo), flujo)
        except StopIteration:
            return [f"falta el job {nombre}"]
        posiciones = []
        for arbitro, orden in arbitros:
            donde = [i for i, paso in enumerate(lista) if orden in paso]
            if not donde:
                fallos.append(f"{nombre}: falta el paso de {arbitro} ({orden})")
            else:
                posiciones.append(donde[-1] if arbitro == "compilacion del frontend" else donde[0])
        if posiciones != sorted(posiciones):
            fallos.append(f"{nombre}: los pasos no van en orden")
    arnes = pasos(_job_por_nombre("Arnés Físico Determinista", flujo), flujo)
    humo = [p for p in arnes if "playwright.humo.config.ts" in p]
    if humo and "if: github.event_name == 'pull_request'" not in humo[0]:
        fallos.append("el humo debe correr en todo PR")
    return fallos


# ¤arbitro
def test_ningun_arbitro_se_pierde():
    assert fallos_de_arbitros(FLUJO) == []


# ¤arbitro
@pytest.mark.parametrize("orden", [o for _, o in ARBITROS_DEL_ARNES + ARBITROS_DE_PLAYWRIGHT])
def test_m3_quitar_un_arbitro_da_rojo(orden):
    lineas = FLUJO.splitlines(keepends=True)
    mutado = "".join(l for l in lineas if orden not in l)
    assert mutado != FLUJO
    assert fallos_de_arbitros(mutado) != []


# ---- Caché (R4) --------------------------------------------------------------------------------------

# ¤arbitro
def fallos_de_cache(flujo: str) -> list[str]:
    fallos = []
    for id_job, texto in jobs(flujo).items():
        lista = pasos(texto, flujo)
        instala_requirements = any("pip install -r requirements" in p for p in lista)
        for paso in lista:
            if "uses: actions/setup-python" in paso and instala_requirements and "cache: pip" not in paso:
                fallos.append(f"{id_job}: setup-python sin cache: pip")
            if "uses: actions/setup-node" in paso and not (
                    "cache: npm" in paso and "cache-dependency-path: frontend/package-lock.json" in paso):
                fallos.append(f"{id_job}: setup-node sin cache: npm")
    return fallos


# ¤arbitro
def test_cache_en_todos_los_jobs():
    assert fallos_de_cache(FLUJO) == []
    assert "uses: actions/setup-node" in FLUJO and "pip install -r requirements" in FLUJO


# ¤arbitro
@pytest.mark.parametrize("linea", ["          cache: pip\n", "          cache: npm\n",
                                   "          cache-dependency-path: frontend/package-lock.json\n"])
def test_m4_quitar_una_cache_da_rojo(linea):
    assert linea in FLUJO
    assert fallos_de_cache(FLUJO.replace(linea, "", 1)) != []


# ---- Retiro (R5) -------------------------------------------------------------------------------------

# ¤arbitro
def test_sin_corrida_cubierta():
    assert not (RAIZ / "scripts" / "corrida_cubierta.py").exists()
    assert not (RAIZ / "tests" / "test_corrida_cubierta.py").exists()
    assert "corrida_cubierta" not in FLUJO
    assert not re.search(r"(?m)steps\.cubierta|outputs\.cubierta|^\s+cubierta:", FLUJO)
    assert "corrida_cubierta" not in (RAIZ / "tests" / "duraciones.json").read_text(encoding="utf-8")


# ---- Medición (R6) -----------------------------------------------------------------------------------

def _job(segundos: int) -> dict:
    return {"started_at": "2026-11-20T10:00:00Z",
            "completed_at": f"2026-11-20T10:{segundos // 60:02d}:{segundos % 60:02d}Z"}


# Cada corrida: 61 s (2 min), 30 s (1 min) y un job omitido (0 min). Sin redondear serían 91 s, 2 min.
JOBS_DE_CORRIDA = [_job(61), _job(30), {"started_at": "2026-11-20T10:00:00Z", "completed_at": "2026-11-20T10:00:00Z"}]


def _api_de_medicion(n_fusiones: int):
    prs = [{"number": i, "merged_at": "2026-11-20T12:00:00Z", "updated_at": "2026-11-20T12:00:00Z",
            "merge_commit_sha": f"m{i}", "head": {"sha": f"h{i}"}} for i in range(n_fusiones)]

    def api(ruta: str):
        if "/pulls?" in ruta:
            return prs if ruta.endswith("&page=1") else []
        if "/runs?event=" in ruta:
            return {"workflow_runs": [{"id": 1, "created_at": "2026-11-20T11:00:00Z"}]}
        if "/jobs?" in ruta:
            return {"total_count": len(JOBS_DE_CORRIDA), "jobs": JOBS_DE_CORRIDA}
        raise AssertionError(ruta)
    return api


# ¤arbitro
def test_medicion_redondea_por_job(capsys):
    assert mm.minutos_de_corrida(JOBS_DE_CORRIDA) == 3
    assert mm.main(["--desde", "2026-11-15", "--hasta", "2026-11-22"], api=_api_de_medicion(20)) == 0
    assert "fusiones=20 media=6.00 mediana=6.0 total=120" in capsys.readouterr().out
    assert mm.main(["--desde", "2026-11-15", "--hasta", "2026-11-22"], api=_api_de_medicion(19)) == 2
    assert mm.main(["--desde", "2026-11-21", "--hasta", "2026-11-22"], api=_api_de_medicion(20)) == 2
