# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""GCP-04b · Registro permanente del balanceador.

`¤seguridad` `¤arbitro` — contrato: governance/especificaciones/GCP-04b.md
"""
from __future__ import annotations

from pathlib import Path

from tests._lector_yaml import leer_yaml

RAIZ = Path(__file__).resolve().parents[1]
BALANCEADOR = RAIZ / "governance/operaciones/cloud_load_balancer.yaml"

SERVICIOS = {"evydentia-backend-bs", "evydentia-web-bs"}


def _balanceador() -> dict:
    return leer_yaml(BALANCEADOR.read_text(encoding="utf-8"))


def test_registro_en_todos_los_servicios():
    servicios = _balanceador()["servicios_backend"]
    assert {s["name"] for s in servicios} == SERVICIOS
    for servicio in servicios:
        registro = servicio.get("registro")
        assert registro == {"habilitado": True, "muestreo": 1}, (
            f"R3: {servicio['name']} debe llevar registro: {{habilitado: true, muestreo: 1}}"
        )
