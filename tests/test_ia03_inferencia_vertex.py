# ¤gemini-vertex ¤arbitro
"""IA-03: compuerta de inferencia Gemini en Vertex AI sin clave. Cliente falso; nunca llama a Vertex."""
import asyncio
import os
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from app_core.errors import ErrorNegocio, IA_TOPE_ORGANIZACION
from features.inferencia import inferencia_service as svc
from features.inferencia.domain.errores import MOTIVO_NEUTRO, InferenciaNoDisponible
from features.inferencia.domain.regiones import UBICACION_POR_REGION
from features.inferencia.services import cliente_vertex


class Esquema(BaseModel):
    estado: str


class ModelosFalsos:
    def __init__(self, texto='{"estado": "ok"}', error=None):
        self.llamadas = []
        self.texto = texto
        self.error = error

    async def generate_content(self, **kw):
        self.llamadas.append(kw)
        if self.error:
            raise self.error
        return SimpleNamespace(text=self.texto)


class ClienteFalso:
    def __init__(self, **kw):
        self.modelos = ModelosFalsos(**kw)
        self.aio = SimpleNamespace(models=self.modelos)


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "proyecto-prueba")
    monkeypatch.setenv("VERTEX_LOCATION", "us-central1")
    monkeypatch.setattr(svc, "_cliente", None)
    consumos = []

    async def consumir(org):
        consumos.append(org)

    svc.inyectar_consumidor_de_prueba(consumir)
    yield consumos
    svc.inyectar_cliente_de_prueba(None)
    svc.inyectar_consumidor_de_prueba(None)


def _gen(cliente, usuario="hola", sistema="s", modelo="gemini-2.5-flash"):
    svc.inyectar_cliente_de_prueba(cliente)
    return asyncio.run(svc.generar_estructurado(sistema, usuario, Esquema, modelo=modelo, org_id="org-1"))


def test_respuesta_valida_y_esquema_pydantic():
    c = ClienteFalso()
    r = _gen(c)
    assert r == Esquema(estado="ok")
    assert c.modelos.llamadas[0]["config"].response_schema is Esquema


def test_respuesta_invalida_falla_cerrada():
    with pytest.raises(InferenciaNoDisponible):
        _gen(ClienteFalso(texto='{"otro": 1}'))


def test_excepcion_del_cliente_falla_cerrada_con_un_reintento():
    c = ClienteFalso(error=RuntimeError("403 PERMISSION_DENIED GOOGLE_CLOUD_PROJECT"))
    with pytest.raises(InferenciaNoDisponible) as e:
        _gen(c)
    assert len(c.modelos.llamadas) == 2
    assert str(e.value) == MOTIVO_NEUTRO
    assert "GOOGLE_CLOUD_PROJECT" not in str(e.value) and "VERTEX_LOCATION" not in str(e.value)


def test_modelo_fuera_de_lista_falla():
    c = ClienteFalso()
    with pytest.raises(InferenciaNoDisponible):
        _gen(c, modelo="gemini-9-ultra")
    assert c.modelos.llamadas == []


def test_dlp_previo_enmascara_cedula_y_correo():
    c = ClienteFalso()
    _gen(c, usuario="cédula 1713175071 correo ana@ejemplo.invalid", sistema="mail x@y.invalid")
    cfg = c.modelos.llamadas[0]
    assert "1713175071" not in cfg["contents"] and "ana@ejemplo.invalid" not in cfg["contents"]
    assert "x@y.invalid" not in cfg["config"].system_instruction


def test_cada_llamada_consume_el_tope(entorno):
    _gen(ClienteFalso())
    assert entorno == ["org-1"]


def test_tope_agotado_no_llama_al_cliente():
    async def agotado(org):
        raise ErrorNegocio(IA_TOPE_ORGANIZACION)

    svc.inyectar_consumidor_de_prueba(agotado)
    c = ClienteFalso()
    with pytest.raises(ErrorNegocio):
        _gen(c)
    assert c.modelos.llamadas == []


def test_cliente_vertex_sin_clave(monkeypatch):
    capturado = {}

    class Fake:
        def __init__(self, **kw):
            capturado.update(kw)

    import google.genai as genai

    monkeypatch.setattr(genai, "Client", Fake)
    cliente_vertex.crear_cliente()
    assert capturado["vertexai"] is True
    assert "api_key" not in capturado
    assert capturado["location"] == "us-central1"


def test_sin_configuracion_no_disponible_y_sin_conectar(monkeypatch):
    monkeypatch.delenv("VERTEX_LOCATION")
    e = svc.estado()
    assert not e.disponible and e.motivo == MOTIVO_NEUTRO
    assert svc._cliente is None


def test_estado_region_y_ubicacion():
    e = svc.estado()
    assert e.disponible and e.region == "us-central1" and e.ubicacion == "Estados Unidos"


def test_region_sin_etiqueta_no_disponible(monkeypatch):
    monkeypatch.setenv("VERTEX_LOCATION", "europe-west9")
    assert not svc.estado().disponible
    with pytest.raises(InferenciaNoDisponible):
        _gen(ClienteFalso())


def test_cada_region_permitida_tiene_etiqueta():
    assert UBICACION_POR_REGION and all(v.strip() for v in UBICACION_POR_REGION.values())


def test_pasillo_solo_reexporta():
    from app_core.pasillo import inferencia

    assert inferencia.estado() == svc.estado()
    assert inferencia.errores()[0] is InferenciaNoDisponible
