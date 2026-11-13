# ¤gemini-vertex ¤arbitro
"""IA-11: conjunto fijo de evaluación. Sin red: Vertex es un doble; el CI nunca ejecuta el script contra Vertex."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app_core.dlp_sanitizer import sanitizar_texto_pii
from features.inferencia import inferencia_service as svc
from features.inferencia.domain.modelos_permitidos import MODELOS_PERMITIDOS

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("evaluar_ia", RAIZ / "scripts" / "evaluar_ia.py")
ev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ev)

MODELO = "gemini-2.5-flash"
CASOS = {
    "prompt_id": "demo.resumen",
    "casos": [
        {
            "id": "c1",
            "valores": {"tema": "plazo de 15 dias", "fuente": "Art. 13"},
            "criterios": {
                "campos_obligatorios": ["resumen", "cita"],
                "cita_presente": True,
                "sin_cifras_inventadas": True,
            },
        }
    ],
}
PROMPTS_PY = (
    "from features.inferencia.domain.prompts import PromptVersionado\n"
    "VERSIONES = {n: PromptVersionado('demo.resumen', n, 'Sistema.', 'Resume: {tema} {fuente}')"
    " for n in range(1, VERSION_VIGENTE + 1)}\n"
    "VIGENTE = VERSION_VIGENTE\n"
)


def _repo(tmp_path: Path, version: int = 1) -> Path:
    """Repositorio mínimo en tmp con un prompt demo, sus casos y sin resultados."""
    ai = tmp_path / "features" / "demo" / "ai"
    ai.mkdir(parents=True)
    (ai / "prompts.py").write_text(f"VERSION_VIGENTE = {version}\n" + PROMPTS_PY, encoding="utf-8")
    casos = tmp_path / "evaluacion" / "ia" / "casos"
    casos.mkdir(parents=True)
    (tmp_path / "evaluacion" / "ia" / "resultados").mkdir(parents=True)
    (casos / "demo.resumen.json").write_text(json.dumps(CASOS), encoding="utf-8")
    return tmp_path


def _resultado(raiz: Path, version: int, puntaje: float, modelo: str = MODELO, huella: str | None = None):
    datos = {
        "prompt_id": "demo.resumen",
        "version": version,
        "modelo": modelo,
        "modelo_version": f"{modelo}-002",
        "puntaje": puntaje,
        "casos_evaluados": 1,
        "fecha": "2026-11-13T00:00:00Z",
        "huella_casos": huella or ev.huella_casos(raiz, "demo.resumen"),
    }
    destino = raiz / "evaluacion" / "ia" / "resultados" / f"demo.resumen_v{version}_{modelo}.json"
    destino.write_text(json.dumps(datos), encoding="utf-8")


# ---- el repositorio real

def test_casos_reales_sin_datos_personales_y_bien_formados():
    for archivo in sorted((RAIZ / "evaluacion" / "ia" / "casos").glob("*.json")):
        texto = archivo.read_text(encoding="utf-8")
        assert sanitizar_texto_pii(texto) == texto, archivo.name
        datos = json.loads(texto)
        assert datos["prompt_id"] == archivo.stem and datos["casos"]


def test_repositorio_real_cumple_y_cuenta_los_vigentes():
    vigentes = ev.vigentes(RAIZ)
    print(f"IA-11: {len(vigentes)} prompts VIGENTE descubiertos")
    assert isinstance(vigentes, list)
    assert ev.problemas_de_resultados(RAIZ, MODELOS_PERMITIDOS) == []


# ---- descubrimiento (no vacuo en silencio)

def test_descubre_un_prompts_py_puesto_en_tmp(tmp_path):
    assert ev.vigentes(_repo(tmp_path, 2)) == [("demo.resumen", 2)]


def test_mutacion_glob_equivocado_no_descubre(tmp_path, monkeypatch):
    raiz = _repo(tmp_path)
    monkeypatch.setattr(ev, "modulos_de_prompts", lambda r: [])  # un glob que no encuentra nada
    assert ev.vigentes(raiz) != [("demo.resumen", 1)]


# ---- reglas del CI con sus mutaciones

def test_vigente_con_resultado_y_puntaje_no_menor_pasa(tmp_path):
    raiz = _repo(tmp_path, 2)
    _resultado(raiz, 1, 0.8)
    _resultado(raiz, 2, 0.8)
    assert ev.problemas_de_resultados(raiz, MODELOS_PERMITIDOS) == []


def test_mutacion_version_subida_sin_resultado_da_rojo(tmp_path):
    raiz = _repo(tmp_path, 2)
    _resultado(raiz, 1, 0.9)  # v2 vigente, sin resultado
    assert any("falta el resultado" in p for p in ev.problemas_de_resultados(raiz, MODELOS_PERMITIDOS))


def test_vigente_sin_ningun_resultado_da_rojo(tmp_path):
    assert ev.problemas_de_resultados(_repo(tmp_path), MODELOS_PERMITIDOS)


def test_mutacion_puntaje_menor_que_el_anterior_da_rojo(tmp_path):
    raiz = _repo(tmp_path, 2)
    _resultado(raiz, 1, 0.9)
    _resultado(raiz, 2, 0.5)
    assert any("puntaje menor" in p for p in ev.problemas_de_resultados(raiz, MODELOS_PERMITIDOS))


def test_casos_cambiados_tras_la_evaluacion_da_rojo(tmp_path):
    raiz = _repo(tmp_path)
    _resultado(raiz, 1, 0.9, huella="0" * 64)
    assert any("casos cambiaron" in p for p in ev.problemas_de_resultados(raiz, MODELOS_PERMITIDOS))


@pytest.mark.parametrize("dato", ["escribe a ana@example.com", "cedula 1710034065"])
def test_mutacion_caso_con_correo_o_cedula_da_rojo(dato):
    texto = json.dumps({**CASOS, "nota": dato})
    assert sanitizar_texto_pii(texto) != texto


# ---- puntaje

def test_puntaje_por_criterios():
    caso = CASOS["casos"][0]
    assert ev.puntuar_caso(caso, {"resumen": "Plazo de 15 dias", "cita": "Art. 13 de la Ley"}) == 1.0
    assert ev.puntuar_caso(caso, {"resumen": "Plazo de 30 dias", "cita": "Art. 13"}) < 1.0  # cifra inventada
    assert ev.puntuar_caso(caso, {"resumen": "x", "cita": "sin referencia"}) < 1.0  # sin cita
    assert ev.puntuar_caso(caso, {"resumen": "x"}) < 1.0  # falta campo
    assert ev.puntuar_caso(caso, None) == 0.0


# ---- el script, con Vertex doble

class _Modelos:
    async def generate_content(self, **kw):
        return SimpleNamespace(
            text='{"resumen": "Plazo de 15 dias", "cita": "Art. 13"}', model_version="gemini-2.5-flash-002"
        )


@pytest.fixture
def vertex_doble(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "proyecto-prueba")
    monkeypatch.setenv("VERTEX_LOCATION", "us-central1")
    monkeypatch.setattr(svc, "_cliente", None)
    gastos = []

    async def consumir(org):
        gastos.append(org)

    svc.inyectar_consumidor_de_prueba(consumir)
    svc.inyectar_cliente_de_prueba(SimpleNamespace(aio=SimpleNamespace(models=_Modelos())))
    yield gastos
    svc.inyectar_cliente_de_prueba(None)
    svc.inyectar_consumidor_de_prueba(None)


def test_script_sin_confirmar_no_llama_ni_escribe(tmp_path, vertex_doble):
    raiz = _repo(tmp_path)
    assert ev.main(["demo.resumen", "1", MODELO, "--org-id", "org-eval"], raiz) == 2
    assert vertex_doble == [] and not list((raiz / "evaluacion" / "ia" / "resultados").glob("*.json"))


def test_script_exige_org_id():
    with pytest.raises(SystemExit):
        ev.main(["demo.resumen", "1", MODELO])


def test_script_rechaza_modelo_no_permitido(tmp_path, vertex_doble):
    assert ev.main(["demo.resumen", "1", "modelo-raro", "--org-id", "o", "--confirmar"], _repo(tmp_path)) == 2


def test_script_escribe_resultado_y_consume_tope(tmp_path, vertex_doble):
    raiz = _repo(tmp_path)
    assert ev.main(["demo.resumen", "1", MODELO, "--org-id", "org-eval", "--confirmar"], raiz) == 0
    datos = ev.leer_resultado(raiz, "demo.resumen", 1, MODELO)
    assert datos["puntaje"] == 1.0 and datos["modelo_version"] == "gemini-2.5-flash-002"
    assert datos["fecha"] and datos["huella_casos"] == ev.huella_casos(raiz, "demo.resumen")
    assert vertex_doble == ["org-eval"]
    assert ev.problemas_de_resultados(raiz, MODELOS_PERMITIDOS) == []


def test_script_no_usa_ganchos_de_prueba_ni_cliente_directo():
    fuente = (RAIZ / "scripts" / "evaluar_ia.py").read_text(encoding="utf-8")
    assert "inyectar_" not in fuente and "cliente_vertex" not in fuente
    assert "import yaml" not in fuente
