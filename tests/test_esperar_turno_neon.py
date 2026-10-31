# ¤¤qa-engineer
"""Una corrida de CI a la vez por rama de Neon: espera por orden de llegada y nunca impide una verificación."""
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("esperar_turno_neon", RAIZ / "scripts" / "esperar_turno_neon.py")
etn = importlib.util.module_from_spec(_spec)
sys.modules["esperar_turno_neon"] = etn
_spec.loader.exec_module(etn)

REPO = "jucaprosi/data-privacy-compliance-lopdp"


@pytest.mark.parametrize("rama, persona", [
    ("dev/juan-carlos", "juan-carlos"),
    ("tarea/aleczandra/dpo-02", "aleczandra"),
    ("tarea/jose/firma-04", "jose"),
    ("main", "main"),
    ("feat/fe-24-tablero", "main"),
])
def test_la_rama_de_neon_sale_del_nombre_de_la_rama(rama, persona):
    assert etn.persona_de_rama(rama) == persona


def test_solo_cuentan_las_corridas_anteriores_de_la_misma_persona():
    corridas = [
        {"id": 30, "head_branch": "tarea/juan-carlos/x"},
        {"id": 10, "head_branch": "dev/juan-carlos"},
        {"id": 20, "head_branch": "tarea/jose/y"},
        {"id": 40, "head_branch": "tarea/juan-carlos/z"},
        {"id": 25, "head_branch": None},
    ]
    assert [c["id"] for c in etn.corridas_por_delante(corridas, 35, "juan-carlos")] == [10, 30]
    assert [c["id"] for c in etn.corridas_por_delante(corridas, 35, "main")] == [25]


def test_un_arnes_omitido_o_terminado_no_bloquea_y_uno_en_cola_si():
    terminado = [{"name": "Arnés por salas", "status": "completed"}, {"name": "Arnés completo", "status": "completed"}]
    en_cola = [{"name": "Arnés por salas", "status": "completed"}, {"name": "Arnés completo", "status": "queued"}]
    solo_compuerta = [{"name": "Arnés Físico Determinista", "status": "in_progress"}, {"name": "Playwright Frontend", "status": "in_progress"}]
    assert etn.arnes_pendiente(terminado) is False
    assert etn.arnes_pendiente(en_cola) is True
    assert etn.arnes_pendiente(solo_compuerta) is False


class _Api:
    """API falsa: la corrida 10 tiene su arnés en marcha durante `vueltas` consultas y luego termina."""

    def __init__(self, vueltas, corridas=None):
        self.vueltas, self.consultas = vueltas, 0
        self.corridas = corridas if corridas is not None else [{"id": 10, "head_branch": "dev/juan-carlos"}]

    def __call__(self, ruta):
        if "/workflows/" in ruta:
            return {"workflow_runs": self.corridas if "in_progress" in ruta else []}
        assert re.search(r"/runs/10/jobs", ruta)
        self.consultas += 1
        estado = "in_progress" if self.consultas <= self.vueltas else "completed"
        return {"jobs": [{"name": "Arnés completo", "status": estado}]}


def test_espera_hasta_que_termina_el_arnes_de_la_corrida_anterior():
    pausas = []
    resultado = etn.esperar(REPO, 35, "juan-carlos", api=_Api(2), dormir=pausas.append, reloj=lambda: 0, pausa_s=5)
    assert resultado == "turno libre" and pausas == [5, 5]


def test_otra_persona_no_espera():
    pausas = []
    assert etn.esperar(REPO, 35, "jose", api=_Api(2), dormir=pausas.append, reloj=lambda: 0) == "turno libre"
    assert pausas == []


def test_una_corrida_recien_encolada_sin_jobs_bloquea():
    class SinJobs(_Api):
        def __call__(self, ruta):
            if "/workflows/" in ruta:
                return {"workflow_runs": self.corridas if "queued" in ruta else []}
            self.consultas += 1
            return {"jobs": []} if self.consultas == 1 else {"jobs": [{"name": "Arnés por salas", "status": "completed"}]}

    pausas = []
    assert etn.esperar(REPO, 35, "juan-carlos", api=SinJobs(0), dormir=pausas.append, reloj=lambda: 0) == "turno libre"
    assert len(pausas) == 1


def test_el_limite_de_espera_sigue_adelante():
    tiempos = iter([0, 0, 100, 100, 3000, 3000, 3000])
    resultado = etn.esperar(REPO, 35, "juan-carlos", api=_Api(99), dormir=lambda s: None, reloj=lambda: next(tiempos), limite_s=2400)
    assert resultado.startswith("límite de espera agotado tras la corrida 10")


def test_sin_api_no_se_espera():
    def api_rota(ruta):
        raise subprocess.CalledProcessError(1, ["gh", "api", ruta])

    assert etn.esperar(REPO, 35, "juan-carlos", api=api_rota, dormir=lambda s: None).startswith("sin espera")


def test_el_workflow_serializa_los_arneses_de_neon_y_cancela_corridas_superadas():
    flujo = (RAIZ / ".github" / "workflows" / "zero-regression-pipeline.yml").read_text(encoding="utf-8")
    assert flujo.index("concurrency:") < flujo.index("jobs:")
    assert "cancel-in-progress: true" in flujo and "${{ github.head_ref || github.ref_name }}" in flujo
    assert flujo.count("scripts/esperar_turno_neon.py") == 2
    assert flujo.count("actions: read") == 3  # los dos arneses y el job de alcance leen corridas con gh api
    for persona in etn.PERSONAS:
        assert f"'{persona}'" in flujo, persona
    assert "*cancelled*" in flujo and "*failure*" in flujo
