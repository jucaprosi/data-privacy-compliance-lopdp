# ¤roadmap
"""Contrato OpenAPI congelado para la Hoja de Ruta Inteligente: compatibilidad hacia atrás.

El frontend se apoya en governance/contratos/hoja_de_ruta.openapi.json. Lo que necesita es
que lo ya publicado no se rompa, no que la API entera sea idéntica al archivo: exigir
igualdad obligaba a cada tarea que añade un endpoint a reescribir el mismo JSON, y varias
ramas paralelas chocaban en él aunque cada una fuese correcta.

La prueba falla si el contrato congelado deja de cumplirse (ruta, método, parámetro,
respuesta, esquema o propiedad eliminados o con otro tipo, o un parámetro que pasa a ser
obligatorio). Añadir rutas, métodos, esquemas o propiedades no la rompe; el coordinador
regenera el archivo con scripts/exportar_contrato_hoja_ruta.py al cerrar cada oleada.
"""
import json
from pathlib import Path

from main import app

RAIZ = Path(__file__).resolve().parent.parent
CONTRATO_FILE = RAIZ / "governance" / "contratos" / "hoja_de_ruta.openapi.json"
METODOS = ("get", "put", "post", "delete", "patch", "options", "head")


def incompatibilidades(guardado: dict, actual: dict) -> list[str]:
    """Rupturas del contrato `guardado` en el esquema `actual`; lista vacía = compatible."""
    rupturas = []
    rutas_actuales = actual.get("paths", {})
    for ruta, operaciones in guardado.get("paths", {}).items():
        if ruta not in rutas_actuales:
            rupturas.append(f"ruta eliminada: {ruta}")
            continue
        for metodo in (m for m in METODOS if m in operaciones):
            op_actual = rutas_actuales[ruta].get(metodo)
            if op_actual is None:
                rupturas.append(f"método eliminado: {metodo.upper()} {ruta}")
                continue
            op = operaciones[metodo]
            donde = f"{metodo.upper()} {ruta}"

            params_actuales = {(p["in"], p["name"]): p for p in op_actual.get("parameters", [])}
            for p in op.get("parameters", []):
                clave = (p["in"], p["name"])
                if clave not in params_actuales:
                    rupturas.append(f"parámetro eliminado: {donde} {p['in']}:{p['name']}")
                    continue
                nuevo = params_actuales[clave]
                if not p.get("required", False) and nuevo.get("required", False):
                    rupturas.append(f"parámetro ahora obligatorio: {donde} {p['in']}:{p['name']}")
                tipo_antes = p.get("schema", {}).get("type")
                tipo_ahora = nuevo.get("schema", {}).get("type")
                if tipo_antes != tipo_ahora:
                    rupturas.append(
                        f"tipo de parámetro cambiado: {donde} {p['name']} {tipo_antes}→{tipo_ahora}"
                    )

            for codigo in op.get("responses", {}):
                if codigo not in op_actual.get("responses", {}):
                    rupturas.append(f"respuesta eliminada: {donde} {codigo}")

    esquemas_actuales = actual.get("components", {}).get("schemas", {})
    for nombre, esquema in guardado.get("components", {}).get("schemas", {}).items():
        if nombre not in esquemas_actuales:
            rupturas.append(f"esquema eliminado: {nombre}")
            continue
        props_actuales = esquemas_actuales[nombre].get("properties", {})
        for prop, definicion in esquema.get("properties", {}).items():
            if prop not in props_actuales:
                rupturas.append(f"propiedad eliminada: {nombre}.{prop}")
            elif definicion.get("type") != props_actuales[prop].get("type"):
                rupturas.append(
                    f"tipo de propiedad cambiado: {nombre}.{prop} "
                    f"{definicion.get('type')}→{props_actuales[prop].get('type')}"
                )
    return rupturas


# --- El comparador detecta: sin esto, un comparador que no ve nada daría un falso verde ---

def _base() -> dict:
    return {
        "paths": {
            "/a": {
                "get": {
                    "parameters": [
                        {"name": "q", "in": "query", "required": False, "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {}, "422": {}},
                },
                "post": {"responses": {"201": {}}},
            }
        },
        "components": {
            "schemas": {"S": {"properties": {"x": {"type": "string"}, "n": {"type": "integer"}}}}
        },
    }


def _copia(d: dict) -> dict:
    return json.loads(json.dumps(d))


def test_esquema_identico_es_compatible():
    assert incompatibilidades(_base(), _copia(_base())) == []


def test_anadir_rutas_metodos_esquemas_y_propiedades_es_compatible():
    nuevo = _copia(_base())
    nuevo["paths"]["/b"] = {"get": {"responses": {"200": {}}}}
    nuevo["paths"]["/a"]["delete"] = {"responses": {"204": {}}}
    nuevo["paths"]["/a"]["get"]["responses"]["404"] = {}
    nuevo["components"]["schemas"]["T"] = {"properties": {}}
    nuevo["components"]["schemas"]["S"]["properties"]["extra"] = {"type": "boolean"}
    assert incompatibilidades(_base(), nuevo) == []


def test_ruta_o_metodo_eliminado_rompe_el_contrato():
    sin_ruta = _copia(_base())
    del sin_ruta["paths"]["/a"]
    assert incompatibilidades(_base(), sin_ruta) == ["ruta eliminada: /a"]

    sin_metodo = _copia(_base())
    del sin_metodo["paths"]["/a"]["post"]
    assert incompatibilidades(_base(), sin_metodo) == ["método eliminado: POST /a"]


def test_parametro_eliminado_obligatorio_o_con_otro_tipo_rompe_el_contrato():
    sin_param = _copia(_base())
    sin_param["paths"]["/a"]["get"]["parameters"] = []
    assert incompatibilidades(_base(), sin_param) == ["parámetro eliminado: GET /a query:q"]

    obligatorio = _copia(_base())
    obligatorio["paths"]["/a"]["get"]["parameters"][0]["required"] = True
    assert incompatibilidades(_base(), obligatorio) == ["parámetro ahora obligatorio: GET /a query:q"]

    otro_tipo = _copia(_base())
    otro_tipo["paths"]["/a"]["get"]["parameters"][0]["schema"]["type"] = "integer"
    assert incompatibilidades(_base(), otro_tipo) == ["tipo de parámetro cambiado: GET /a q string→integer"]


def test_respuesta_eliminada_rompe_el_contrato():
    sin_respuesta = _copia(_base())
    del sin_respuesta["paths"]["/a"]["get"]["responses"]["422"]
    assert incompatibilidades(_base(), sin_respuesta) == ["respuesta eliminada: GET /a 422"]


def test_esquema_o_propiedad_eliminados_o_con_otro_tipo_rompen_el_contrato():
    sin_esquema = _copia(_base())
    del sin_esquema["components"]["schemas"]["S"]
    assert incompatibilidades(_base(), sin_esquema) == ["esquema eliminado: S"]

    sin_prop = _copia(_base())
    del sin_prop["components"]["schemas"]["S"]["properties"]["x"]
    assert incompatibilidades(_base(), sin_prop) == ["propiedad eliminada: S.x"]

    otro_tipo = _copia(_base())
    otro_tipo["components"]["schemas"]["S"]["properties"]["n"]["type"] = "string"
    assert incompatibilidades(_base(), otro_tipo) == ["tipo de propiedad cambiado: S.n integer→string"]


# --- Invariante real ---

def test_contrato_hoja_de_ruta_sigue_cumpliendose():
    """La API actual cumple todo lo que promete governance/contratos/hoja_de_ruta.openapi.json."""
    assert CONTRATO_FILE.exists(), (
        f"El archivo de contrato no existe en {CONTRATO_FILE}. "
        "Ejecuta: python scripts/exportar_contrato_hoja_ruta.py"
    )
    contrato_guardado = json.loads(CONTRATO_FILE.read_text(encoding="utf-8"))
    rupturas = incompatibilidades(contrato_guardado, app.openapi())
    assert not rupturas, (
        "La API rompe el contrato congelado:\n- " + "\n- ".join(rupturas)
        + "\nSi el cambio es intencionado, regenera con python scripts/exportar_contrato_hoja_ruta.py."
    )
