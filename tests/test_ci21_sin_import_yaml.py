# ¤¤qa-engineer
# ¤arbitro
"""CI-21: ninguna prueba ni script importa `yaml` (PyYAML no está en requirements.txt), y el lector común
`tests/_lector_yaml.py` lee los manifiestos de governance/operaciones o falla con el número de línea."""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from tests._lector_yaml import leer_yaml

RAIZ = Path(__file__).resolve().parent.parent
OPERACIONES = RAIZ / "governance" / "operaciones"
MANIFIESTOS = sorted(OPERACIONES.rglob("*.yaml")) + sorted(OPERACIONES.rglob("*.yml"))


def _es_yaml(nombre: str | None) -> bool:
    return nombre == "yaml" or bool(nombre and nombre.startswith("yaml."))


def importaciones_de_yaml(codigo: str) -> list[int]:
    """Las líneas que importan `yaml`: import, from, importlib.import_module o __import__."""
    lineas = []
    for nodo in ast.walk(ast.parse(codigo)):
        if isinstance(nodo, ast.Import) and any(_es_yaml(a.name) for a in nodo.names):
            lineas.append(nodo.lineno)
        elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0 and _es_yaml(nodo.module):
            lineas.append(nodo.lineno)
        elif isinstance(nodo, ast.Call) and nodo.args and isinstance(nodo.args[0], ast.Constant):
            f = nodo.func
            nombre = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
            if nombre in ("import_module", "__import__") and _es_yaml(nodo.args[0].value if isinstance(nodo.args[0].value, str) else None):
                lineas.append(nodo.lineno)
    return sorted(lineas)


def _archivos_python() -> list[Path]:
    return sorted(p for carpeta in ("tests", "scripts") for p in (RAIZ / carpeta).rglob("*.py")
                  if "node_modules" not in p.parts and "__pycache__" not in p.parts)


# 1 · Ningún archivo de tests/ ni de scripts/ importa yaml.
def test_ninguna_prueba_ni_script_importa_yaml():
    hallados = [f"{p.relative_to(RAIZ).as_posix()}:{n}"
                for p in _archivos_python() for n in importaciones_de_yaml(p.read_text(encoding="utf-8"))]
    assert not hallados, "importan yaml (use tests/_lector_yaml.py): " + ", ".join(hallados)


@pytest.mark.parametrize("codigo", [
    "import yaml", "import yaml as y", "import os, yaml", "from yaml import safe_load", "from yaml.loader import SafeLoader",
    "import importlib\nimportlib.import_module('yaml')", "__import__('yaml')", "def f():\n    import yaml",
])
def test_el_arbitro_detecta_cada_forma_de_importar(codigo):
    assert importaciones_de_yaml(codigo)


@pytest.mark.parametrize("codigo", ["import yamlito", "from tests._lector_yaml import leer_yaml", "x = 'import yaml'"])
def test_el_arbitro_no_confunde_otros_nombres(codigo):
    assert importaciones_de_yaml(codigo) == []


# 2 · Cada manifiesto de governance/operaciones se lee.
def test_hay_manifiestos_que_leer():
    assert len(MANIFIESTOS) >= 5


@pytest.mark.parametrize("ruta", MANIFIESTOS, ids=lambda p: p.relative_to(OPERACIONES).as_posix())
def test_cada_manifiesto_se_lee(ruta):
    documento = leer_yaml(ruta.read_text(encoding="utf-8"))
    assert isinstance(documento, (dict, list)) and documento


# 3 · El subconjunto soportado.
def test_mapas_listas_y_escalares():
    texto = (
        "# comentario\n"
        "nombre: evydentia   # comentario al final\n"
        "puerto: 3000\n"
        "negativo: -5\n"
        "activo: true\n"
        "apagado: false\n"
        "nada: null\n"
        "vacio:\n"
        "comillas: \"true\"\n"
        "simples: 'a # no es comentario'\n"
        "url: https://ejemplo.invalid/ruta\n"
        "en_linea: [a, \"b c\", 3]\n"
        "mapa:\n"
        "  hijo:\n"
        "    nieto: 1\n"
        "lista:\n"
        "  - uno\n"
        "  - clave: 1\n"
        "    otra: dos\n"
        "  -\n"
        "    anidada: si\n"
        "pegada:\n"
        "- x\n"
    )
    assert leer_yaml(texto) == {
        "nombre": "evydentia", "puerto": 3000, "negativo": -5, "activo": True, "apagado": False,
        "nada": None, "vacio": None, "comillas": "true", "simples": "a # no es comentario",
        "url": "https://ejemplo.invalid/ruta", "en_linea": ["a", "b c", 3],
        "mapa": {"hijo": {"nieto": 1}},
        "lista": ["uno", {"clave": 1, "otra": "dos"}, {"anidada": "si"}],
        "pegada": ["x"],
    }


def test_bloque_literal():
    texto = "guion: |\n  linea uno\n    sangrada # texto\n\n  linea tres\nsigue: 1\nsin_salto: |-\n  fin\n"
    assert leer_yaml(texto) == {"guion": "linea uno\n  sangrada # texto\n\nlinea tres\n", "sigue": 1, "sin_salto": "fin"}


def test_varios_documentos_dan_una_lista():
    assert leer_yaml("# cabecera\na: 1\n---\nb: 2\n") == [{"a": 1}, {"b": 2}]


# 4 · Lo no soportado da ValueError con su línea, un caso por prueba.
def test_un_alias_da_error_con_su_linea():
    with pytest.raises(ValueError, match=r"línea 3: un alias"):
        leer_yaml("a: 1\nb: 2\nc: *a\n")


def test_una_etiqueta_da_error_con_su_linea():
    with pytest.raises(ValueError, match=r"línea 2: una etiqueta"):
        leer_yaml("a: 1\nb: !Ref otro\n")


def test_un_flujo_anidado_da_error_con_su_linea():
    with pytest.raises(ValueError, match=r"línea 4: un flujo anidado"):
        leer_yaml("a: 1\nb: 2\nc: 3\nd: [1, [2, 3]]\n")


@pytest.mark.parametrize("texto, linea", [
    ("a: &ancla 1\n", 1), ("a: {b: 1}\n", 1), ("a: >\n  plegado\n", 1), ("a: 1\n  b: 2\n", 2),
    ("a: 1\nesto no es clave\n", 2), ("a: 1\na: 2\n", 2), ("a:\n\t- x\n", 2),
])
def test_lo_demas_no_soportado_tambien_da_error(texto, linea):
    with pytest.raises(ValueError, match=rf"línea {linea}:"):
        leer_yaml(texto)


# 6 · Prueba dorada.
_WEB_PRODUCCION = {
    "apiVersion": "serving.knative.dev/v1",
    "kind": "Service",
    "metadata": {
        "name": "evydentia-web",
        "labels": {"entorno": "production"},
        "annotations": {
            "run.googleapis.com/ingress": "internal-and-cloud-load-balancing",
            "run.googleapis.com/invoker-iam-disabled": "true",
        },
    },
    "spec": {"template": {
        "metadata": {"annotations": {
            "run.googleapis.com/startup-cpu-boost": "true",
            "run.googleapis.com/vpc-access-connector": "CONECTOR_VPC",
            "run.googleapis.com/vpc-access-egress": "private-ranges-only",
            "autoscaling.knative.dev/minScale": "0",
            "autoscaling.knative.dev/maxScale": "10",
        }},
        "spec": {
            "containerConcurrency": 80,
            "serviceAccountName": "CUENTA_DE_SERVICIO",
            "containers": [{
                "image": "IMAGEN",
                "ports": [{"name": "http1", "containerPort": 3000}],
                "resources": {"limits": {"cpu": "1", "memory": "512Mi"}},
                "env": [
                    {"name": "APP_ENV", "value": "production"},
                    {"name": "BACKEND_URL", "value": "https://app.evydentia.com"},
                    {"name": "PROXY_AUTH_CLOUD_RUN", "value": "ninguna"},
                ],
                "startupProbe": {"httpGet": {"path": "/health", "port": 3000}, "periodSeconds": 5, "failureThreshold": 12},
                "livenessProbe": {"httpGet": {"path": "/health", "port": 3000}, "periodSeconds": 30},
            }],
        },
    }},
}


def _hojas(valor) -> int:
    if isinstance(valor, dict):
        return sum(_hojas(v) if isinstance(v, (dict, list)) else 1 for v in valor.values())
    if isinstance(valor, list):
        return sum(_hojas(v) for v in valor if isinstance(v, (dict, list)))
    return 0


def test_dorada_cloudrun_frontend_service():
    texto = (OPERACIONES / "cloudrun_frontend_service.yaml").read_text(encoding="utf-8")
    documentos = leer_yaml(texto)
    assert [d["metadata"]["name"] for d in documentos] == ["evydentia-web", "evydentia-web-pruebas", "evydentia-web-demo"]
    assert documentos[0] == _WEB_PRODUCCION
    lineas_clave_valor = [l for l in texto.splitlines()
                          if re.match(r"^\s*(?:- )?[\w./-]+:\s+[^#\s]", l) and not l.lstrip().startswith("#")]
    assert sum(_hojas(d) for d in documentos) == len(lineas_clave_valor)
