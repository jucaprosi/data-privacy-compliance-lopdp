# ¤diagnostico-scoring
"""La escala de madurez tiene un solo contrato: el árbitro y el motor del servidor lo cumplen."""
import copy
import importlib.util
import sys
from pathlib import Path

import pytest

from features.diagnostico.domain import models
from features.diagnostico.services import dimensiones_sgpdp as motor

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("verificar_escala_madurez", RAIZ / "scripts" / "verificar_escala_madurez.py")
vem = importlib.util.module_from_spec(_spec)
sys.modules["verificar_escala_madurez"] = vem
_spec.loader.exec_module(vem)

CONTRATO = vem.cargar()


def test_el_arbitro_pasa_sobre_el_repositorio():
    assert vem.revisar(CONTRATO) == []


def test_contrato_sin_escala_completa_falla():
    roto = copy.deepcopy(CONTRATO)
    roto["nivel_asignado"].pop()
    assert any(h.startswith("E1") for h in vem.revisar_contrato(roto))


def test_rangos_con_hueco_fallan():
    roto = copy.deepcopy(CONTRATO)
    roto["nivel_asignado"][1]["rango"] = [41, 59]
    assert any("contiguos" in h for h in vem.revisar_contrato(roto))


def test_contrato_distinto_del_archivo_falla():
    pytest.importorskip("openpyxl")
    ruta = vem.archivo_fuente(CONTRATO)
    if ruta is None:
        pytest.skip("el archivo de assessment no está en este entorno")
    roto = copy.deepcopy(CONTRATO)
    roto["reglas"]["riesgo_critico_desde"] = 16
    roto["dimensiones"][0]["peso"] = 0.2
    hallazgos = vem.revisar_fuente(roto, ruta)
    assert any("umbral 16" in h for h in hallazgos) and any("D01" in h for h in hallazgos)


def test_consumidor_nuevo_de_un_campo_retirado_falla():
    c = {"consumidores_pendientes": {}, "lectura_historica": {}}
    assert vem.revisar_vocabulario(c, {"features/roadmap/x.py": ["score_ponderado"]}) == [
        "E4: features/roadmap/x.py usa «score_ponderado», retirado de la escala; use el contrato vigente"
    ]


def test_anotado_con_su_tarea_se_tolera_y_otro_termino_no():
    c = {"consumidores_pendientes": {"a.py": {"tarea": "DIAG-08", "terminos": ["nivel_ajustado"]}}, "lectura_historica": {}}
    assert vem.revisar_vocabulario(c, {"a.py": ["nivel_ajustado"]}) == []
    assert len(vem.revisar_vocabulario(c, {"a.py": ["nivel_ajustado", "score_ponderado"]})) == 1


def test_la_lista_de_pendientes_solo_encoge():
    c = {"consumidores_pendientes": {"a.py": {"tarea": "DIAG-08", "terminos": ["nivel_ajustado"]}}, "lectura_historica": {}}
    assert "ya no usa" in vem.revisar_vocabulario(c, {})[0]
    assert vem.podar(c, {})["consumidores_pendientes"] == {}
    assert vem.podar({**c, "consumidores_pendientes": {}}, {"b.py": ["x"]})["consumidores_pendientes"] == {}


def test_lectura_historica_autorizada():
    c = {"consumidores_pendientes": {}, "lectura_historica": {"a.py": "resultados sellados"}}
    assert vem.revisar_vocabulario(c, {"a.py": ["nivel_madurez"]}) == []


def test_doctrina_con_la_escala_vieja_falla(tmp_path):
    for relativo in vem.DOCTRINA:
        (tmp_path / relativo).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / relativo).write_text("Escala vigente\n", encoding="utf-8")
    assert vem.revisar_doctrina(tmp_path) == []
    (tmp_path / vem.DOCTRINA[0]).write_text("Índice de Madurez SPDP (0 a 3)\n", encoding="utf-8")
    assert vem.revisar_doctrina(tmp_path) == [f"E5: {vem.DOCTRINA[0]}:1 conserva la escala 0 a 3"]


def test_motor_cumple_rangos_umbrales_y_dimensiones():
    r = CONTRATO["reglas"]
    assert [(d.id, d.nombre, d.peso) for d in motor.DIMENSIONES_SGPDP] == [
        (d["id"], d["nombre"], d["peso"]) for d in CONTRATO["dimensiones"]
    ]
    assert [n.nivel for n in map(motor.nivel_desde_score, (0, 40, 60, 75, 90))] == [1, 2, 3, 4, 5]
    for n in CONTRATO["nivel_asignado"]:
        assert motor.nivel_desde_score(n["rango"][0]).nivel == n["nivel"]
        assert motor.nivel_desde_score(n["rango"][1]).nivel == n["nivel"]
    assert motor.UMBRAL_RIESGO_CRITICO == r["riesgo_critico_desde"]
    assert motor.UMBRAL_RIESGO_ALTO == r["riesgo_alto_desde"]
    assert motor.CRITICIDAD_BLOQUEANTE == r["criticidad_bloqueante"]
    assert motor.UMBRAL_DEGRADACION_ESTRUCTURAL == r["efectivo_degradado_bajo"]
    assert motor.NIVEL_TOPE_BRECHA_ESTRUCTURAL == r["tope_por_bloqueante"]
    assert motor.CRITICIDAD_EVIDENCIA_EXIGIBLE == r["criticidad_evidencia_exigible"]
    assert motor.UMBRAL_EVIDENCIA_EXIGIBLE == r["evidencia_exigible"]
    assert motor.NIVEL_TOPE_EVIDENCIA_INSUFICIENTE == r["tope_por_evidencia_insuficiente"]
    assert motor.COBERTURA_MINIMA_EMISION == r["cobertura_minima"]


def test_constantes_del_dominio_cumplen_el_contrato():
    if not hasattr(models, "NIVELES_ASIGNADOS"):
        pytest.skip("llegan con DIAG-08")
    assert models.NIVELES_ASIGNADOS == {n["nivel"]: (n["nombre"], n["criterio"]) for n in CONTRATO["nivel_asignado"]}
    assert models.NIVELES_EVIDENCIA == {n["nivel"]: n["nombre"] for n in CONTRATO["nivel_evidencia"]}
    assert models.ESCALA_SELLADA == CONTRATO["version"]
