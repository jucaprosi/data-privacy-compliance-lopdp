# ¤gemini-vertex ¤arbitro
"""IA-10: cada resultado de IA lleva su traza (invariante 64). Cliente falso; nunca llama a Vertex."""
import asyncio
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from app_core.pasillo import inferencia
from features.inferencia import inferencia_service as svc
from features.inferencia.domain.errores import InferenciaNoDisponible
from features.inferencia.domain.traza import Traza

ALIAS = "gemini-2.5-flash"
VERSION = "gemini-2.5-flash-002"
SHA = "a" * 64


class Esquema(BaseModel):
    estado: str


class ModelosFalsos:
    def __init__(self, model_version=VERSION):
        self.model_version = model_version

    async def generate_content(self, **kw):
        return SimpleNamespace(text='{"estado": "ok"}', model_version=self.model_version)


class ClienteFalso:
    def __init__(self, **kw):
        self.aio = SimpleNamespace(models=ModelosFalsos(**kw))


PROMPT = inferencia.prompt_versionado("roadmap.redaccion", 2, "Eres un redactor.", "Resume: {tema}")


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "proyecto-prueba")
    monkeypatch.setenv("VERTEX_LOCATION", "us-central1")
    monkeypatch.setattr(svc, "_cliente", None)

    async def consumir(org):
        return None

    svc.inyectar_consumidor_de_prueba(consumir)
    yield
    svc.inyectar_cliente_de_prueba(None)
    svc.inyectar_consumidor_de_prueba(None)


def _trazado(cliente=None, **kw):
    svc.inyectar_cliente_de_prueba(cliente or ClienteFalso())
    return asyncio.run(
        inferencia.generar_trazado(PROMPT, {"tema": "retención"}, Esquema, modelo=ALIAS, org_id="org-1", **kw)
    )


def test_la_traza_lleva_la_version_del_modelo_y_no_el_alias():
    resultado, traza = _trazado()
    assert resultado == Esquema(estado="ok")
    assert traza.modelo_version == VERSION
    assert traza.modelo_solicitado == ALIAS
    assert traza.modelo_version != traza.modelo_solicitado


def test_la_traza_identifica_prompt_sala_y_organizacion():
    _, traza = _trazado()
    assert (traza.prompt_id, traza.prompt_version) == ("roadmap.redaccion", 2)
    assert traza.sala == "roadmap"
    assert traza.tenant_id == "org-1"
    assert traza.corpus_sha256 is None


def test_el_sha256_del_corpus_se_conserva():
    _, traza = _trazado(corpus_sha256=SHA)
    assert traza.corpus_sha256 == SHA


@pytest.mark.parametrize("ausente", [None, "", "   "])
def test_sin_version_del_modelo_falla_cerrada(ausente):
    with pytest.raises(InferenciaNoDisponible):
        _trazado(ClienteFalso(model_version=ausente))


def test_generar_estructurado_sigue_funcionando_sin_traza():
    svc.inyectar_cliente_de_prueba(ClienteFalso())
    r = asyncio.run(svc.generar_estructurado("s", "u", Esquema, modelo=ALIAS, org_id="org-1"))
    assert r == Esquema(estado="ok")


class SesionFalsa:
    def __init__(self):
        self.ejecuciones = []
        self.commits = 0

    async def execute(self, sentencia, params=None):
        self.ejecuciones.append((str(sentencia), params))

    async def commit(self):
        self.commits += 1


def test_registrar_traza_escribe_en_la_sesion_del_llamador_sin_commit():
    traza = Traza("roadmap", "org-1", VERSION, ALIAS, "roadmap.redaccion", 2, SHA)
    sesion = SesionFalsa()
    asyncio.run(inferencia.registrar_traza(sesion, traza, "roadmaps", "rm-1"))
    assert sesion.commits == 0
    (sql, params), = sesion.ejecuciones
    assert "INSERT INTO trazas_ia" in sql
    assert ":tenant_id" in sql and "org-1" not in sql  # parámetros ligados, no texto interpolado
    assert params["modelo_version"] == VERSION and params["entidad"] == "roadmaps" and params["entidad_id"] == "rm-1"
