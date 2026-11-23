# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""GCP-04b · Exclusión de la firma 942421 en Cloud Armor y registro permanente del balanceador.

`¤seguridad` `¤arbitro` — contrato: governance/especificaciones/GCP-04b.md
"""
from __future__ import annotations

import re
from pathlib import Path

from tests._lector_yaml import leer_yaml

RAIZ = Path(__file__).resolve().parents[1]
BALANCEADOR = RAIZ / "governance/operaciones/cloud_load_balancer.yaml"
ESPECIFICACION = RAIZ / "governance/especificaciones/GCP-04b.md"

# R4: la expresión que la nube tiene aplicada (leída por el CTO el 2026-11-22 con `rules describe 1000`).
EXPRESION_NUBE_1000 = (
    "evaluatePreconfiguredWaf('sqli-v33-stable', {'sensitivity': 4, "
    "'opt_out_rule_ids': ['owasp-crs-v030301-id942421-sqli']})"
)
EXPRESION_1001 = "evaluatePreconfiguredWaf('xss-v33-stable')"
SERVICIOS = {"evydentia-backend-bs", "evydentia-web-bs"}


def _balanceador() -> dict:
    return leer_yaml(BALANCEADOR.read_text(encoding="utf-8"))


def _regla(prioridad: int) -> dict:
    reglas = [r for r in _balanceador()["politica_cloud_armor"]["reglas"] if r["prioridad"] == prioridad]
    assert len(reglas) == 1, f"la regla {prioridad} debe aparecer una sola vez en evydentia-waf"
    return reglas[0]


def _opt_out(expresion: str) -> list[str]:
    """Los ids de `opt_out_rule_ids` de una expresión `evaluatePreconfiguredWaf`, en orden."""
    lista = re.search(r"'opt_out_rule_ids'\s*:\s*\[([^\]]*)\]", expresion)
    return re.findall(r"'([^']+)'", lista.group(1)) if lista else []


def _seccion_1_especificacion() -> str:
    texto = ESPECIFICACION.read_text(encoding="utf-8")
    seccion = re.search(r"^## 1\. .*?(?=^## 2\. )", texto, flags=re.S | re.M)
    assert seccion, "la especificación GCP-04b debe tener las secciones §1 y §2"
    return seccion.group(0)


def test_regla_1000_excluye_solo_942421():
    regla = _regla(1000)
    expresion = regla["expresion"]
    assert expresion == EXPRESION_NUBE_1000, "R4: la regla 1000 debe ser carácter a carácter la de la nube"
    assert re.search(r"'sensitivity'\s*:\s*4\b", expresion), "R1: la regla 1000 conserva la sensibilidad 4"
    assert _opt_out(expresion) == ["owasp-crs-v030301-id942421-sqli"], "R1: se excluye solo la firma 942421"
    assert regla["accion"] == "deny(403)"


def test_regla_1001_sin_cambios():
    regla = _regla(1001)
    assert regla["expresion"] == EXPRESION_1001
    assert regla["accion"] == "deny(403)"


def test_exclusiones_con_evidencia():
    seccion_1 = _seccion_1_especificacion()
    for regla in _balanceador()["politica_cloud_armor"]["reglas"]:
        for firma in _opt_out(regla.get("expresion") or ""):
            assert firma in seccion_1, (
                f"R2: la firma {firma} de la regla {regla['prioridad']} se excluye sin evidencia en la §1 de GCP-04b"
            )


def test_registro_en_todos_los_servicios():
    servicios = _balanceador()["servicios_backend"]
    assert {s["name"] for s in servicios} == SERVICIOS
    for servicio in servicios:
        registro = servicio.get("registro")
        assert registro == {"habilitado": True, "muestreo": 1}, (
            f"R3: {servicio['name']} debe llevar registro: {{habilitado: true, muestreo: 1}}"
        )
