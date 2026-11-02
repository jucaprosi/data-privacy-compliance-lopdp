# ¤¤qa-engineer
"""Un arnés por commit: el PR adopta el resultado del push solo si pasó y la rama está al día con su base."""
import importlib.util
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("corrida_cubierta", RAIZ / "scripts" / "corrida_cubierta.py")
cc = importlib.util.module_from_spec(_spec)
sys.modules["corrida_cubierta"] = cc
_spec.loader.exec_module(cc)

REPO = "jucaprosi/data-privacy-compliance-lopdp"
SHA = "b5b0348000000000000000000000000000000000"


def test_al_dia_es_que_la_base_sea_antecesora_de_la_cabeza():
    assert cc.al_dia("base", SHA, git=lambda args: 0 if args[:2] == ["merge-base", "--is-ancestor"] else 9)
    assert not cc.al_dia("base", SHA, git=lambda args: 1)


def test_el_resultado_del_arnes_distingue_pasado_pendiente_y_fallido():
    assert cc.resultado_del_arnes([{"name": "Arnés completo", "status": "completed", "conclusion": "success"},
                                   {"name": "Arnés por salas", "status": "completed", "conclusion": "skipped"}]) == "success"
    assert cc.resultado_del_arnes([{"name": "Arnés completo", "status": "in_progress", "conclusion": None},
                                   {"name": "Arnés por salas", "status": "completed", "conclusion": "skipped"}]) is None
    assert cc.resultado_del_arnes([{"name": "Alcance de la corrida", "status": "completed", "conclusion": "success"}]) is None
    assert cc.resultado_del_arnes([{"name": "Arnés completo", "status": "completed", "conclusion": "cancelled"},
                                   {"name": "Arnés por salas", "status": "completed", "conclusion": "skipped"}]) == "cancelled"
    assert cc.resultado_del_arnes([{"name": "Arnés completo", "status": "completed", "conclusion": "skipped"},
                                   {"name": "Arnés por salas", "status": "completed", "conclusion": "skipped"}]) == "sin arnés"


class _Api:
    """API falsa: la corrida 10 del push aparece tras `tarda` consultas y su arnés pasa tras `vueltas` más."""

    def __init__(self, tarda=0, vueltas=0, final="success"):
        self.tarda, self.vueltas, self.final = tarda, vueltas, final
        self.listados = self.jobs = 0

    def __call__(self, ruta):
        if "/workflows/" in ruta:
            self.listados += 1
            assert f"head_sha={SHA}" in ruta and "event=push" in ruta
            corridas = [{"id": 99, "head_branch": "dev/juan-carlos"}, {"id": 10, "head_branch": "dev/juan-carlos"}]
            return {"workflow_runs": corridas if self.listados > self.tarda else []}
        assert "/runs/10/jobs" in ruta
        self.jobs += 1
        estado = ("in_progress", None) if self.jobs <= self.vueltas else ("completed", self.final)
        return {"jobs": [{"name": "Arnés completo", "status": estado[0], "conclusion": estado[1]},
                         {"name": "Arnés por salas", "status": "completed", "conclusion": "skipped"}]}


def _decidir(api, base="base", git=lambda args: 0, reloj=lambda: 0, **extra):
    pausas = []
    corrida, motivo = cc.decidir(REPO, SHA, base, 99, api=api, git=git, dormir=pausas.append, reloj=reloj, **extra)
    return corrida, motivo, pausas


def test_el_pr_adopta_la_corrida_del_push_cuando_su_arnes_pasa():
    corrida, motivo, pausas = _decidir(_Api(vueltas=2))
    assert corrida == 10 and motivo.startswith("cubierta por la corrida 10") and len(pausas) == 2


def test_la_propia_corrida_no_cuenta_y_se_toma_la_mas_antigua():
    assert cc.corridas_push(REPO, SHA, 99, _Api())[0]["id"] == 10


def test_espera_a_que_aparezca_la_corrida_del_push():
    corrida, _, pausas = _decidir(_Api(tarda=2))
    assert corrida == 10 and len(pausas) == 2


def test_sin_push_sobre_el_commit_el_pr_corre_su_arnes():
    tiempos = iter([0, 0, 0, 500])
    corrida, motivo, _ = _decidir(_Api(tarda=99), reloj=lambda: next(tiempos), espera_aparicion_s=90)
    assert corrida is None and "ningún push" in motivo


def test_un_push_fallido_o_cancelado_no_cubre():
    corrida, motivo, _ = _decidir(_Api(final="failure"))
    assert corrida is None and "sin éxito (failure)" in motivo


def test_una_rama_detras_de_la_base_prueba_su_propia_fusion():
    corrida, motivo, pausas = _decidir(_Api(), git=lambda args: 1)
    assert corrida is None and "no está al día" in motivo and pausas == []


def test_fuera_de_un_pr_no_se_reutiliza():
    corrida, motivo, _ = _decidir(_Api(), base="")
    assert corrida is None and "sin base" in motivo


def test_el_limite_de_espera_devuelve_el_arnes_al_pr():
    tiempos = iter([0, 0, 0, 3000, 3000])
    corrida, motivo, _ = _decidir(_Api(vueltas=99), reloj=lambda: next(tiempos), limite_s=2400)
    assert corrida is None and "límite de espera" in motivo


def test_sin_api_el_pr_corre_su_arnes():
    def rota(ruta):
        raise subprocess.CalledProcessError(1, ["gh", "api", ruta])

    corrida, motivo, _ = _decidir(rota)
    assert corrida is None and "la API no respondió" in motivo


def test_el_workflow_reutiliza_el_push_y_la_compuerta_lo_acepta():
    flujo = (RAIZ / ".github" / "workflows" / "zero-regression-pipeline.yml").read_text(encoding="utf-8")
    assert "scripts/corrida_cubierta.py" in flujo and "cubierta: ${{ steps.cubierta.outputs.cubierta }}" in flujo
    assert flujo.count("needs.alcance.outputs.cubierta == ''") == 2
    assert "CUBIERTA: ${{ needs.alcance.outputs.cubierta }}" in flujo and 'if [ -n "$CUBIERTA" ]' in flujo
    assert flujo.count("actions: read") == 3
