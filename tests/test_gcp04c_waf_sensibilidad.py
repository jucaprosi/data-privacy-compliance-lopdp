# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""GCP-04c · Cloud Armor con sensibilidad 1 en SQLi y XSS, sin exclusiones de firmas.

`¤seguridad` `¤arbitro` — contrato: governance/especificaciones/GCP-04c.md
"""
from __future__ import annotations

from pathlib import Path

from tests._lector_yaml import leer_yaml

RAIZ = Path(__file__).resolve().parents[1]
BALANCEADOR = RAIZ / "governance/operaciones/cloud_load_balancer.yaml"

# R2: las expresiones que el propietario aplicó en la nube (PROPIETARIO_WAF_SENSIBILIDAD_1.md).
EXPRESIONES = {
    1000: "evaluatePreconfiguredWaf('sqli-v33-stable', {'sensitivity': 1})",
    1001: "evaluatePreconfiguredWaf('xss-v33-stable', {'sensitivity': 1})",
}


def _regla(prioridad: int) -> dict:
    reglas = [r for r in leer_yaml(BALANCEADOR.read_text(encoding="utf-8"))["politica_cloud_armor"]["reglas"]
              if r["prioridad"] == prioridad]
    assert len(reglas) == 1, f"la regla {prioridad} debe aparecer una sola vez en evydentia-waf"
    return reglas[0]


def test_regla_1000_sensibilidad_1():
    regla = _regla(1000)
    assert regla["expresion"] == EXPRESIONES[1000], "R1: la regla 1000 usa sqli-v33-stable con sensibilidad 1"
    assert regla["accion"] == "deny(403)"


def test_regla_1001_sensibilidad_1():
    regla = _regla(1001)
    assert regla["expresion"] == EXPRESIONES[1001], "R1: la regla 1001 usa xss-v33-stable con sensibilidad 1"
    assert regla["accion"] == "deny(403)"


def test_sin_exclusiones_de_firmas():
    for prioridad in EXPRESIONES:
        assert "opt_out_rule_ids" not in _regla(prioridad)["expresion"], f"R1: la regla {prioridad} no excluye firmas"
