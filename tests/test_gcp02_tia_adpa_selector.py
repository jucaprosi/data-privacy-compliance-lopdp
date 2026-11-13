# ¤cloud-run-perf ¤adpa ¤arbitro
"""GCP-02: el selector TIA es determinista, conservador y nunca omite lo innegociable.

Mutaciones documentadas (también automatizadas abajo sobre copias en memoria):
- un cambio que debería disparar un grupo de pruebas y el selector lo omite (se le quita una prueba de la sala
  tocada) hace fallar `test_mutacion_omitir_pruebas_de_la_sala_se_detecta`;
- quitar `test_alembic_una_cabeza` o `test_sin_sql_interpolado` del piso de la matriz hace fallar
  `test_mutacion_un_piso_sin_alembic_se_detecta` y `test_el_piso_lleva_lo_innegociable`;
- tratar `app_core/db/` como una sala hace fallar `test_tia_cambio_nucleo_activa_suite_completa`.
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest

from app_core.cloud import tia_adpa_selector as tia

RAIZ = Path(__file__).resolve().parents[1]
MATRIZ = tia.cargar_matriz(RAIZ / "governance" / "operaciones" / "ci_tia_matrix.json")
INNEGOCIABLES = (
    "tests/test_alembic_una_cabeza.py",
    "tests/test_sin_sql_interpolado.py",
    "tests/test_adpa_bulkhead.py",
    "tests/test_adpa_dependencias.py",
    "tests/test_arnes_local.py",
    "tests/test_entorno_arnes.py",
    "tests/test_ci16_pruebas_sin_proyecto.py",
    "tests/test_ci21_sin_import_yaml.py",
    "tests/test_ci22_exenciones_secciones.py",
)


@pytest.fixture(scope="module")
def arbol():
    arbol = tia.analizar_arbol(RAIZ)
    assert arbol is not None, "falta scripts/seleccionar_pruebas.py"
    return arbol


def _impacto(arbol, *archivos, **kw):
    return tia.calcular_impacto_adpa(list(archivos), arbol=arbol, **kw)


# --- Aceptación (especificación GCP-02 §5) ----------------------------------------------------------

def test_tia_cambio_aislado_sala_omite_frontend(arbol):
    impacto = _impacto(arbol, "features/conservacion/conservacion_service.py")
    assert impacto.modo == tia.SALAS
    # La prueba de CON-01 se exige solo cuando existe en el árbol (ADPA-09 crea la sala; CON-01 la llena después).
    if (RAIZ / "tests/test_con01_conservacion.py").is_file():
        assert "tests/test_con01_conservacion.py" in impacto.archivos_pytest
    assert impacto.requiere_frontend_build is False
    assert impacto.playwright_shards == 0
    assert impacto.salas_afectadas == ["conservacion"]
    # Ninguna prueba exclusiva de otra sala entra: solo la sala, el piso, el núcleo y lo declarado.
    permitidas = {p.ruta for p in arbol.pruebas if p.es_nucleo} | set(tia._piso(RAIZ, MATRIZ)[0])
    permitidas.add("tests/test_con01_conservacion.py")  # permitida si existe; no se exige
    assert set(impacto.archivos_pytest) <= permitidas


def test_tia_cambio_nucleo_activa_suite_completa(arbol):
    for archivo in ("app_core/db/session.py", "alembic/versions/20261101_x.py", "alembic/env.py"):
        impacto = _impacto(arbol, archivo)
        assert impacto.es_completo, archivo
        assert impacto.archivos_pytest == ["tests"]
        assert impacto.requiere_frontend_build is True
        assert any("transversal (R3)" in m for m in impacto.motivos)
    # Un archivo transversal gana aunque llegue junto a un cambio de sala.
    assert _impacto(arbol, "features/rat/rat_service.py", "app_core/db/session.py").es_completo


# --- Lo que nunca se omite --------------------------------------------------------------------------

def _faltan_innegociables(matriz: dict) -> list[str]:
    piso = matriz["piso_siempre"]
    faltan = [p for p in ("tests/test_alembic_una_cabeza.py", "tests/test_sin_sql_interpolado.py") if p not in piso]
    if not any(p.startswith("tests/test_adpa") and "*" in p for p in piso):
        faltan.append("tests/test_adpa*.py")
    if not any(p.startswith("tests/test_arnes") for p in piso):
        faltan.append("tests/test_arnes*.py")
    return faltan


def test_el_piso_lleva_lo_innegociable():
    assert _faltan_innegociables(MATRIZ) == []


def test_el_piso_existe_en_el_arbol():
    existentes, faltan = tia._piso(RAIZ, MATRIZ)
    assert faltan == []
    for prueba in INNEGOCIABLES:
        assert prueba in existentes, prueba


@pytest.mark.parametrize("archivo", [
    "features/rat/rat_service.py",
    "features/conservacion/conservacion_service.py",
    "app_core/pasillo/diagnostico.py",
    "frontend/tests/rat/rat.spec.ts",
    "governance/operaciones/ENTORNO_DE_PRUEBAS.md",
    "tests/test_gcp02_tia_adpa_selector.py",
])
def test_un_diff_acotado_siempre_lleva_el_piso_y_el_nucleo(arbol, archivo):
    impacto = _impacto(arbol, archivo)
    assert impacto.modo == tia.SALAS, impacto.motivos
    for prueba in INNEGOCIABLES:
        assert prueba in impacto.archivos_pytest, prueba
    assert {p.ruta for p in arbol.pruebas if p.es_nucleo} <= set(impacto.archivos_pytest)


def test_mutacion_un_piso_sin_alembic_se_detecta():
    mutada = copy.deepcopy(MATRIZ)
    mutada["piso_siempre"].remove("tests/test_alembic_una_cabeza.py")
    assert _faltan_innegociables(mutada) == ["tests/test_alembic_una_cabeza.py"]
    mutada["piso_siempre"] = [p for p in mutada["piso_siempre"] if not p.startswith("tests/test_adpa")]
    assert "tests/test_adpa*.py" in _faltan_innegociables(mutada)


def test_si_falta_una_prueba_del_piso_corre_todo(arbol):
    mutada = copy.deepcopy(MATRIZ)
    mutada["piso_siempre"].append("tests/test_que_no_existe.py")
    impacto = _impacto(arbol, "features/rat/rat_service.py", matriz=mutada)
    assert impacto.es_completo and any("falta una prueba del piso" in m for m in impacto.motivos)


# --- Conservador: nunca menos que el selector actual del CI -----------------------------------------

def test_nunca_elige_menos_que_el_selector_del_ci_para_un_cambio_de_sala(arbol):
    base = arbol.base
    for sala in arbol.salas_reales:
        archivo = f"features/{sala}/{sala}_service.py"
        actual = set(base.seleccionar([archivo], RAIZ, arbol.pruebas).pruebas)
        nuevo = set(_impacto(arbol, archivo).archivos_pytest)
        assert actual <= nuevo, (sala, sorted(actual - nuevo))


def _esperadas_de_la_sala(arbol, sala):
    alcanzadas = {sala} | arbol.base.cierre_dependientes(arbol.usada_por, sala)
    return {p.ruta for p in arbol.pruebas if p.salas & alcanzadas}


def test_cada_sala_selecciona_sus_pruebas_y_las_de_sus_dependientes(arbol):
    for sala in ("rat", "roadmap", "organizacion"):
        impacto = _impacto(arbol, f"features/{sala}/{sala}_service.py")
        assert _esperadas_de_la_sala(arbol, sala) <= set(impacto.archivos_pytest)
        assert sala in impacto.salas_afectadas


def _cubre(esperadas: set[str], elegidas) -> bool:
    return esperadas <= set(elegidas)


def test_mutacion_omitir_pruebas_de_la_sala_se_detecta(arbol):
    impacto = _impacto(arbol, "features/rat/rat_service.py")
    esperadas = _esperadas_de_la_sala(arbol, "rat")
    assert _cubre(esperadas, impacto.archivos_pytest)
    mutilada = set(impacto.archivos_pytest) - {sorted(esperadas)[0]}
    assert not _cubre(esperadas, mutilada), "un selector que omite una prueba de la sala debe quedar en rojo"


# --- R2: pasillo central ----------------------------------------------------------------------------

def test_un_cambio_en_el_pasillo_lleva_la_sala_sus_dependientes_y_sus_duenas(arbol):
    impacto = _impacto(arbol, "app_core/pasillo/diagnostico.py")
    assert impacto.modo == tia.SALAS, impacto.motivos
    assert "diagnostico" in impacto.salas_afectadas
    assert _esperadas_de_la_sala(arbol, "diagnostico") <= set(impacto.archivos_pytest)
    assert impacto.requiere_frontend_build is False


def test_un_pasillo_sin_sala_corre_todo(arbol):
    assert _impacto(arbol, "app_core/pasillo/go_vault_worker.py").es_completo
    assert _impacto(arbol, "app_core/pasillo/__init__.py").es_completo


# --- Todo lo desconocido corre todo -----------------------------------------------------------------

@pytest.mark.parametrize("archivo", [
    "main.py", "requirements.txt", "Dockerfile", ".github/workflows/zero-regression-pipeline.yml",
    "api/routers/rat.py", "app_core/security.py", "scripts/verificar_alcance_pr.py", "tests/conftest.py",
    "features/sala_que_no_existe/x.py", "../fuera.py", "/etc/passwd", "C:/Windows/x.py",
])
def test_un_archivo_no_reconocido_corre_todo(arbol, archivo):
    assert _impacto(arbol, archivo).es_completo


def test_sin_cambios_corre_todo(arbol):
    assert _impacto(arbol).es_completo
    assert _impacto(arbol, "", "  ").es_completo


def test_sin_el_selector_base_corre_todo(tmp_path):
    (tmp_path / "governance" / "operaciones").mkdir(parents=True)
    impacto = tia.calcular_impacto_adpa(["features/rat/x.py"], raiz=tmp_path, matriz=MATRIZ)
    assert impacto.es_completo and "falta scripts/seleccionar_pruebas.py" in impacto.motivos


def test_con_la_matriz_ilegible_corre_todo(tmp_path):
    assert tia.calcular_impacto_adpa(["features/rat/x.py"], raiz=tmp_path).es_completo


# --- Frontend y shards ------------------------------------------------------------------------------

def test_un_cambio_en_un_shard_de_playwright_compila_y_corre_ese_shard(arbol):
    impacto = _impacto(arbol, "frontend/tests/rat/rat.spec.ts")
    assert impacto.modo == tia.SALAS
    assert impacto.requiere_frontend_build is True
    assert impacto.playwright_shards == 1


def test_un_cambio_general_del_frontend_corre_todos_los_shards(arbol):
    impacto = _impacto(arbol, "frontend/src/app/layout.tsx")
    carpetas = tia._carpetas_de_playwright(RAIZ, MATRIZ["playwright"]["fuera"])
    assert impacto.requiere_frontend_build is True
    assert impacto.playwright_shards == len(carpetas) > 5


def test_un_contrato_de_sala_que_ve_el_cliente_compila_su_shard_y_los_de_sus_dependientes(arbol):
    impacto = _impacto(arbol, "features/roadmap/domain/modelos.py")
    carpetas = tia._carpetas_de_playwright(RAIZ, MATRIZ["playwright"]["fuera"])
    assert impacto.modo == tia.SALAS
    assert impacto.requiere_frontend_build is True
    assert 1 <= impacto.playwright_shards <= len(carpetas)


def test_una_sala_sin_shard_declarado_corre_todos_los_shards(arbol):
    impacto = _impacto(arbol, "features/notificaciones/domain/modelos.py")
    carpetas = tia._carpetas_de_playwright(RAIZ, MATRIZ["playwright"]["fuera"])
    assert impacto.requiere_frontend_build is True
    assert impacto.playwright_shards == len(carpetas)


def test_las_pruebas_de_la_zona_frontend_entran_con_un_cambio_del_frontend(arbol):
    impacto = _impacto(arbol, "frontend/tests/rat/rat.spec.ts")
    de_zona = {p.ruta for p in arbol.pruebas if "frontend" in p.texto}
    assert de_zona <= set(impacto.archivos_pytest)


# --- Determinismo y forma ---------------------------------------------------------------------------

def test_el_orden_y_los_duplicados_no_cambian_el_resultado(arbol):
    a = _impacto(arbol, "features/rat/rat_service.py", "features/roadmap/roadmap_service.py")
    b = _impacto(arbol, "features/roadmap/roadmap_service.py", "./features/rat/rat_service.py", "features/rat/rat_service.py")
    assert a == b
    assert a.archivos_pytest == sorted(a.archivos_pytest) and a.salas_afectadas == sorted(a.salas_afectadas)


def test_la_matriz_es_json_sin_secretos_ni_rutas_absolutas():
    texto = (RAIZ / "governance" / "operaciones" / "ci_tia_matrix.json").read_text(encoding="utf-8")
    assert json.loads(texto)["version"] == 1
    assert not re.search(r"[A-Za-z]:[\\/]|postgres(ql)?://|BEGIN [A-Z ]*PRIVATE KEY", texto)


# --- Coherencia de la matriz ------------------------------------------------------------------------

def test_las_carpetas_de_playwright_de_la_matriz_existen_y_sus_salas_tambien(arbol):
    carpetas = tia._carpetas_de_playwright(RAIZ, MATRIZ["playwright"]["fuera"])
    for sala, carpeta in MATRIZ["playwright"]["sala_a_carpeta"].items():
        assert sala in arbol.salas_reales, sala
        assert carpeta in carpetas, carpeta


def test_los_contratos_del_cliente_compilan_como_patrones():
    for patron in MATRIZ["contratos_cliente"]:
        assert tia._glob_a_regex(patron).match(patron.replace("**", "a/b").replace("*", "x"))


def test_una_sala_pendiente_caduca_cuando_aparece(arbol):
    """Como la excepción de CI-16: la entrada vale mientras la sala y su prueba no existan."""
    for sala, entrada in MATRIZ["pendientes"].items():
        assert sala not in arbol.salas_reales, f"{sala} ya existe: pásala fuera de «pendientes» ({entrada['tarea']})"
        for prueba in entrada["pruebas"]:
            assert not (RAIZ / prueba).exists(), f"{prueba} ya existe: quita la entrada de «pendientes»"
            assert re.fullmatch(r"tests/test_[a-z0-9_]+\.py", prueba)


def test_el_cli_imprime_json_y_sin_lista_corre_todo(capsys):
    assert tia.main([]) == 0
    assert json.loads(capsys.readouterr().out)["modo"] == tia.COMPLETO
