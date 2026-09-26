# ¤¤qa-engineer
"""Contrato del proveedor externo del asistente de implementación.

Las pruebas no realizan solicitudes de red. La frontera HTTP se sustituye para
verificar el contexto saliente y las respuestas adversariales del proveedor.
"""
from __future__ import annotations

import json
import logging

import httpx
import pytest

from features.ai_copilot.domain.assistant_models import ConsultaAsistente
from features.ai_copilot.services import assistant_provider
from features.ai_copilot.services.implementation_assistant import responder_implementacion
from features.regulacion_rag.domain.corpus import CORPUS_VERSION
from features.regulacion_rag.services.implementation_guides import obtener_guia_brecha


CLAVE_PRUEBA = "ds-clave-que-no-debe-salir"


class RespuestaHTTPFalsa:
    def __init__(self, cuerpo=None, error_http: Exception | None = None):
        self.cuerpo = cuerpo
        self.error_http = error_http

    def raise_for_status(self):
        if self.error_http:
            raise self.error_http

    def json(self):
        return self.cuerpo


def instalar_http_falso(monkeypatch, respuesta: RespuestaHTTPFalsa):
    llamadas = []

    class ClienteHTTPFalso:
        def __init__(self, *args, **kwargs):
            self.opciones = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, **kwargs):
            llamadas.append({"url": url, **kwargs})
            return respuesta

    monkeypatch.setattr(assistant_provider.httpx, "AsyncClient", ClienteHTTPFalso)
    return llamadas


def configurar_deepseek(monkeypatch, tmp_path, habilitado: bool = True):
    monkeypatch.setattr(assistant_provider, "ENV_PATH", tmp_path / "sin-env")
    if habilitado:
        monkeypatch.setenv("DEEPSEEK_API_KEY", CLAVE_PRUEBA)
        monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-flash-prueba")
    else:
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)


def consulta_con_datos_que_no_deben_salir() -> ConsultaAsistente:
    return ConsultaAsistente.model_validate({
        "pregunta": (
            "¿Cómo cierro consentimiento para Ana Perez, ana@example.test, "
            "cédula 1710034065?"
        ),
        "brechas": [{
            "pregunta_id": 21,
            "control": "Gestión del consentimiento de Acme Corp",
            "dimension_id": "D03",
            "severidad": "Alto",
        }],
        "historial": [{
            "rol": "usuario",
            "contenido": (
                "HISTORIAL-PRIVADO de Organización UltraReservada C.A.; "
                "evidencia real contrato-7788; teléfono 0991234567"
            ),
        }],
        "brecha_id": 21,
        "estado": "Implementación",
    })


def guia_y_fuentes():
    guia = obtener_guia_brecha(21, "Gestión del consentimiento", "D03")
    assert guia is not None
    return {21: guia}, guia["fundamento"]


def salida_deepseek(resultado: dict) -> dict:
    return {
        "choices": [{
            "message": {"content": json.dumps(resultado, ensure_ascii=False)},
        }],
    }


def plan_externo(pregunta_id: int = 21) -> dict:
    return {
        "pregunta_id": pregunta_id,
        "pasos": [
            "Configure un registro de consentimiento por finalidad y pruebe su revocación."
        ],
        "responsable_sugerido": "Dueño del canal digital",
        "evidencias": ["Resultado de una prueba con datos ficticios"],
        "criterio_cierre": "La revocación queda trazada y detiene el tratamiento.",
        "seguimiento": "Revisar trimestralmente una muestra de registros.",
    }


@pytest.mark.asyncio
async def test_deepseek_recibe_contexto_minimo_sanitizado_y_fusiona_salida(
    monkeypatch, tmp_path,
):
    configurar_deepseek(monkeypatch, tmp_path)
    externo = {
        "respuesta": "Aplique el plan verificable conforme al Art. 8.",
        "enfoque": "plan",
        "planes": [plan_externo()],
    }
    llamadas = instalar_http_falso(
        monkeypatch, RespuestaHTTPFalsa(salida_deepseek(externo)),
    )
    guias, fuentes = guia_y_fuentes()

    respuesta = await responder_implementacion(
        consulta_con_datos_que_no_deben_salir(), guias, fuentes, CORPUS_VERSION,
    )

    assert respuesta.modo == "deepseek"
    assert respuesta.respuesta.startswith("Aplique el plan verificable")
    assert respuesta.planes[0].pasos == plan_externo()["pasos"]
    assert respuesta.planes[0].responsable_sugerido == "Dueño del canal digital"
    assert respuesta.planes[0].fundamento == [
        type(f).model_validate(f.model_dump()) for f in respuesta.planes[0].fundamento
    ]

    assert len(llamadas) == 1
    llamada = llamadas[0]
    assert llamada["url"] == "https://api.deepseek.com/chat/completions"
    assert llamada["headers"]["Authorization"] == f"Bearer {CLAVE_PRUEBA}"
    assert llamada["json"]["model"] == "deepseek-flash-prueba"
    assert llamada["json"]["response_format"] == {"type": "json_object"}

    cuerpo = json.dumps(llamada["json"], ensure_ascii=False)
    for dato_privado in (
        CLAVE_PRUEBA, "Ana Perez", "ana@example.test", "1710034065", "Acme Corp",
        "HISTORIAL-PRIVADO", "UltraReservada", "contrato-7788", "0991234567",
    ):
        assert dato_privado not in cuerpo
    assert "historial" not in cuerpo.lower()
    assert "[EMAIL_1]" in cuerpo
    assert "[DATO_SANITIZADO_POR_DLP]" in cuerpo

    mensaje_usuario = json.loads(llamada["json"]["messages"][1]["content"])
    contexto = mensaje_usuario["contexto_minimo"]
    assert contexto["brechas"] == [{
        "pregunta_id": 21,
        "control": guias[21]["control"],
        "severidad": "Alto",
    }]
    assert contexto["prioridad_usuario"] == {
        "brecha_id": 21, "estado": "Implementación",
        "instruccion": "Prioriza este estado al explicar el plan.",
    }
    assert contexto["fundamentos"]
    assert all(f["version"] == CORPUS_VERSION for f in contexto["fundamentos"])
    assert all(f["url"].startswith("https://www.gob.ec/") for f in contexto["fundamentos"])


@pytest.mark.asyncio
async def test_cita_fuera_del_corpus_fuerza_respaldo_local(monkeypatch, tmp_path):
    configurar_deepseek(monkeypatch, tmp_path)
    externo = {
        "respuesta": "La LOPDP, Art. 999 obliga a comprar una herramienta específica.",
        "enfoque": "plan",
        "planes": [plan_externo()],
    }
    instalar_http_falso(monkeypatch, RespuestaHTTPFalsa(salida_deepseek(externo)))
    guias, fuentes = guia_y_fuentes()

    respuesta = await responder_implementacion(
        consulta_con_datos_que_no_deben_salir(), guias, fuentes, CORPUS_VERSION,
    )

    assert respuesta.modo == "local"
    assert "Art. 999" not in respuesta.model_dump_json()
    assert respuesta.planes[0].pasos == guias[21]["pasos"]
    assert any("respaldo local" in aviso for aviso in respuesta.advertencias)


@pytest.mark.asyncio
async def test_plan_de_id_ajeno_se_descarta_y_no_modifica_otras_brechas(
    monkeypatch, tmp_path,
):
    configurar_deepseek(monkeypatch, tmp_path)
    externo = {
        "respuesta": "Se preparó una orientación operativa con las fuentes entregadas.",
        "enfoque": "plan",
        "planes": [plan_externo(80)],
    }
    instalar_http_falso(monkeypatch, RespuestaHTTPFalsa(salida_deepseek(externo)))
    guias, fuentes = guia_y_fuentes()

    respuesta = await responder_implementacion(
        consulta_con_datos_que_no_deben_salir(), guias, fuentes, CORPUS_VERSION,
    )

    assert respuesta.modo == "deepseek"
    assert [p.pregunta_id for p in respuesta.planes] == [21]
    assert respuesta.planes[0].pasos == guias[21]["pasos"]
    assert all(p.pregunta_id != 80 for p in respuesta.planes)


@pytest.mark.asyncio
@pytest.mark.parametrize("fallo", ["http", "json"])
async def test_fallo_http_o_json_invalido_usa_respaldo_local(
    monkeypatch, tmp_path, fallo,
):
    configurar_deepseek(monkeypatch, tmp_path)
    if fallo == "http":
        request = httpx.Request("POST", assistant_provider.API_URL)
        response = httpx.Response(503, request=request)
        error = httpx.HTTPStatusError(
            "Servicio no disponible", request=request, response=response,
        )
        falsa = RespuestaHTTPFalsa(error_http=error)
    else:
        falsa = RespuestaHTTPFalsa({
            "choices": [{"message": {"content": "{json incompleto"}}],
        })
    instalar_http_falso(monkeypatch, falsa)
    guias, fuentes = guia_y_fuentes()

    resultado = await responder_implementacion(
        consulta_con_datos_que_no_deben_salir(), guias, fuentes, CORPUS_VERSION,
    )

    assert resultado.modo == "local"
    assert resultado.planes[0].pasos == guias[21]["pasos"]
    assert any("no respondió de forma verificable" in a for a in resultado.advertencias)


def test_estado_deepseek_refleja_configuracion_sin_exponer_clave(
    monkeypatch, tmp_path, caplog,
):
    configurar_deepseek(monkeypatch, tmp_path)
    caplog.set_level(logging.DEBUG)

    estado = assistant_provider.estado_proveedor_asistente()

    assert estado["proveedor_configurado"] is True
    assert estado["proveedor"] == "deepseek"
    assert estado["modo"] == "deepseek"
    assert estado["inferencia_externa_habilitada"] is True
    assert estado["dlp_activo"] is True
    assert "historial" in estado["datos_excluidos"]
    assert CLAVE_PRUEBA not in json.dumps(estado, ensure_ascii=False)
    assert CLAVE_PRUEBA not in caplog.text


@pytest.mark.asyncio
async def test_sin_clave_no_abre_cliente_http_y_reporta_modo_local(
    monkeypatch, tmp_path,
):
    configurar_deepseek(monkeypatch, tmp_path, habilitado=False)

    class ClienteProhibido:
        def __init__(self, *args, **kwargs):
            raise AssertionError("No debe abrirse HTTP sin configurar DeepSeek")

    monkeypatch.setattr(assistant_provider.httpx, "AsyncClient", ClienteProhibido)
    guias, fuentes = guia_y_fuentes()
    respuesta = await responder_implementacion(
        consulta_con_datos_que_no_deben_salir(), guias, fuentes, CORPUS_VERSION,
    )
    estado = assistant_provider.estado_proveedor_asistente()

    assert respuesta.modo == "local"
    assert estado["proveedor_configurado"] is False
    assert estado["modo"] == "local"
    assert estado["inferencia_externa_habilitada"] is False
