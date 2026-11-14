"""GCP-11 · DATABASE_URL, JWT_SECRET y SESSION_SECRET salen de Secret Manager, nunca como valor en claro.

`¤versionado-despliegue` `¤arbitro`. Sin `import yaml`: lector común de manifiestos.

Mutación documentada: poner `value:` literal en `DATABASE_URL` del manifiesto hace fallar
`test_el_manifiesto_toma_la_base_de_secret_manager`.
"""
import re
from pathlib import Path

from tests._lector_yaml import leer_yaml

RAIZ = Path(__file__).resolve().parents[1]
MANIFIESTO = RAIZ / "governance/operaciones/cloudrun_service.yaml"
WORKFLOW = RAIZ / ".github/workflows/deploy-gcp.yml"
SECRETOS = ("DATABASE_URL", "JWT_SECRET", "SESSION_SECRET")


def _env(texto: str) -> list[dict]:
    docs = leer_yaml(texto)
    docs = docs if isinstance(docs, list) and docs and "kind" in docs[0] else [docs]
    servicio = next(d for d in docs if d.get("kind") == "Service")
    return servicio["spec"]["template"]["spec"]["containers"][0]["env"]


def faltas_del_manifiesto(texto: str) -> list[str]:
    return [f"{e['name']} con valor en claro" for e in _env(texto) if e["name"] in SECRETOS and "value" in e]


def test_el_manifiesto_toma_la_base_de_secret_manager():
    entradas = {e["name"]: e for e in _env(MANIFIESTO.read_text(encoding="utf-8"))}
    assert "secretKeyRef" in entradas["DATABASE_URL"]["valueFrom"] and "value" not in entradas["DATABASE_URL"]
    assert faltas_del_manifiesto(MANIFIESTO.read_text(encoding="utf-8")) == []


def test_el_despliegue_carga_los_tres_secretos_desde_secret_manager():
    linea = next(l for l in WORKFLOW.read_text(encoding="utf-8").splitlines() if "--set-secrets" in l)
    for nombre in SECRETOS:
        assert re.search(rf"\b{nombre}=[A-Z_]+:", linea), f"{nombre} no sale de Secret Manager en el despliegue"


def test_mutacion_un_valor_literal_se_detecta():
    mutado = MANIFIESTO.read_text(encoding="utf-8").replace(
        "- name: DATABASE_URL\n              valueFrom:", "- name: DATABASE_URL\n              value: postgresql://x.invalid\n              valueFrom:", 1
    ).replace("\r\n", "\n")
    mutado = mutado.replace("- name: DATABASE_URL\r\n", "- name: DATABASE_URL\n")
    assert faltas_del_manifiesto(mutado) == ["DATABASE_URL con valor en claro"]
