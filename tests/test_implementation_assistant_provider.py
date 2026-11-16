# ¤¤qa-engineer
"""Contrato del asistente de implementación sobre la compuerta de inferencia (IA-07).

Las pruebas no realizan solicitudes de red. El pasillo de inferencia se sustituye
por una compuerta falsa para verificar el contexto saliente y las respuestas adversariales.
"""
from __future__ import annotations

import json
import logging
from types import SimpleNamespace

import pytest

from app_core.pasillo import inferencia as pasillo_inferencia

from features.ai_copilot.domain.assistant_models import ConsultaAsistente
from features.ai_copilot.services import assistant_provider
from features.ai_copilot.services.implementation_assistant import responder_implementacion
from features.regulacion_rag.domain.corpus import CORPUS_VERSION
from features.regulacion_rag.services.implementation_guides import obtener_guia_brecha


ORG = "org-prueba-ia07"


class CompuertaFalsa:
    """Sustituye el pasillo de inferencia: registra llamadas y devuelve la salida o el error dado."""

    def __init__(self, salida: dict | None = None, error: Exception | None = None, disponible: bool = True):
        self.salida, self.error, self.disponible, self.llamadas = salida, error, disponible, []

    def estado(self):
        return SimpleNamespace(disponible=self.disponible)

    async def generar_estructurado(self, sistema, usuario, esquema, *, modelo, org_id):
        self.llamadas.append({"sistema": sistema, "usuario": usuario, "modelo": modelo, "org_id": org_id})
        if self.error:
            raise self.error
        return esquema.model_validate(self.salida)


def instalar_compuerta(monkeypatch, compuerta: CompuertaFalsa) -> CompuertaFalsa:
    monkeypatch.setattr(assistant_provider, "pasillo_inferencia", compuerta)
    return compuerta


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
async def test_compuerta_recibe_contexto_minimo_sanitizado_y_fusiona_salida(monkeypatch):
    externo = {
        "respuesta": "Aplique el plan verificable conforme al Art. 8.",
        "enfoque": "plan",
        "planes": [plan_externo()],
    }
    compuerta = instalar_compuerta(monkeypatch, CompuertaFalsa(externo))
    guias, fuentes = guia_y_fuentes()

    respuesta = await responder_implementacion(
        consulta_con_datos_que_no_deben_salir(), guias, fuentes, CORPUS_VERSION, org_id=ORG,
    )

    assert respuesta.modo == "externo"
    assert respuesta.respuesta.startswith("Aplique el plan verificable")
    assert respuesta.planes[0].pasos == plan_externo()["pasos"]
    assert respuesta.planes[0].responsable_sugerido == "Dueño del canal digital"

    assert len(compuerta.llamadas) == 1
    llamada = compuerta.llamadas[0]
    assert llamada["modelo"] == "gemini-2.5-pro"
    assert llamada["org_id"] == ORG
    cuerpo = llamada["usuario"]
    for dato_privado in (
        "Ana Perez", "ana@example.test", "1710034065", "Acme Corp",
        "HISTORIAL-PRIVADO", "UltraReservada", "contrato-7788", "0991234567",
    ):
        assert dato_privado not in cuerpo
    assert "historial" not in cuerpo.lower()
    assert "[EMAIL_1]" in cuerpo
    assert "[DATO_SANITIZADO_POR_DLP]" in cuerpo

    contexto = json.loads(cuerpo)["contexto_minimo"]
    assert contexto["brechas"] == [{
        "pregunta_id": 21, "control": guias[21]["control"], "severidad": "Alto",
    }]
    assert contexto["prioridad_usuario"] == {
        "brecha_id": 21, "estado": "Implementación",
        "instruccion": "Prioriza este estado al explicar el plan.",
    }
    assert contexto["fundamentos"]
    assert all(f["version"] == CORPUS_VERSION for f in contexto["fundamentos"])
    assert all(f["url"].startswith("https://www.gob.ec/") for f in contexto["fundamentos"])


@pytest.mark.asyncio
async def test_cita_fuera_del_corpus_fuerza_respaldo_local(monkeypatch):
    externo = {
        "respuesta": "La LOPDP, Art. 999 obliga a comprar una herramienta específica.",
        "enfoque": "plan", "planes": [plan_externo()],
    }
    instalar_compuerta(monkeypatch, CompuertaFalsa(externo))
    guias, fuentes = guia_y_fuentes()

    respuesta = await responder_implementacion(
        consulta_con_datos_que_no_deben_salir(), guias, fuentes, CORPUS_VERSION, org_id=ORG,
    )

    assert respuesta.modo == "local"
    assert "Art. 999" not in respuesta.model_dump_json()
    assert respuesta.planes[0].pasos == guias[21]["pasos"]
    assert any("respaldo local" in aviso for aviso in respuesta.advertencias)


@pytest.mark.asyncio
async def test_plan_de_id_ajeno_se_descarta_y_no_modifica_otras_brechas(monkeypatch):
    externo = {
        "respuesta": "Se preparó una orientación operativa con las fuentes entregadas.",
        "enfoque": "plan", "planes": [plan_externo(80)],
    }
    instalar_compuerta(monkeypatch, CompuertaFalsa(externo))
    guias, fuentes = guia_y_fuentes()

    respuesta = await responder_implementacion(
        consulta_con_datos_que_no_deben_salir(), guias, fuentes, CORPUS_VERSION, org_id=ORG,
    )

    assert respuesta.modo == "externo"
    assert [p.pregunta_id for p in respuesta.planes] == [21]
    assert respuesta.planes[0].pasos == guias[21]["pasos"]


@pytest.mark.asyncio
@pytest.mark.parametrize("fallo", ["compuerta", "esquema"])
async def test_fallo_de_compuerta_o_salida_invalida_usa_respaldo_local(monkeypatch, fallo):
    no_disponible, _ = pasillo_inferencia.errores()
    if fallo == "compuerta":
        compuerta = CompuertaFalsa(error=no_disponible())
    else:
        compuerta = CompuertaFalsa({"respuesta": 3})
    instalar_compuerta(monkeypatch, compuerta)
    guias, fuentes = guia_y_fuentes()

    resultado = await responder_implementacion(
        consulta_con_datos_que_no_deben_salir(), guias, fuentes, CORPUS_VERSION, org_id=ORG,
    )

    assert resultado.modo == "local"
    assert resultado.planes[0].pasos == guias[21]["pasos"]
    assert any("no respondió de forma verificable" in a for a in resultado.advertencias)


def test_estado_refleja_la_compuerta_sin_exponer_proveedor(monkeypatch, caplog):
    instalar_compuerta(monkeypatch, CompuertaFalsa())
    caplog.set_level(logging.DEBUG)

    estado = assistant_provider.estado_proveedor_asistente()

    assert estado["proveedor_configurado"] is True
    assert estado["proveedor"] == "externo"
    assert estado["modo"] == "externo"
    assert estado["dlp_activo"] is True
    assert "historial" in estado["datos_excluidos"]
    texto = json.dumps(estado, ensure_ascii=False).lower()
    assert "gemini" not in texto and "vertex" not in texto


@pytest.mark.asyncio
async def test_compuerta_no_disponible_no_llama_y_reporta_modo_local(monkeypatch):
    compuerta = instalar_compuerta(monkeypatch, CompuertaFalsa(disponible=False))
    guias, fuentes = guia_y_fuentes()
    respuesta = await responder_implementacion(
        consulta_con_datos_que_no_deben_salir(), guias, fuentes, CORPUS_VERSION, org_id=ORG,
    )
    estado = assistant_provider.estado_proveedor_asistente()

    assert compuerta.llamadas == []
    assert respuesta.modo == "local"
    assert estado["proveedor_configurado"] is False
    assert estado["modo"] == "local"
    assert estado["inferencia_externa_habilitada"] is False
