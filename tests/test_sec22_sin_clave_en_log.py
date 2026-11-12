"""SEC-22: la clave de API no aparece en ningún registro del motor de inferencia.

El detector revisa las cuatro vías por las que una clave llega a un registro: texto formateado
(f-string), argumento de formato, logger hijo y traza de excepción.
"""
import logging
import traceback

import pytest

from features.ai_copilot.domain.models import AnalisisDiagnosticoRequest
from features.ai_copilot.services import inference_engine

CLAVE_FALSA = "clave-falsa-123"
NOMBRE_LOGGER = "jubys_lopdp_json_logger"


def _request() -> AnalisisDiagnosticoRequest:
    return AnalisisDiagnosticoRequest(
        id_diagnostico="sec22", normativa="LOPDP", tenant_id="test",
        brechas_identificadas=["Sin política de retención"], scoring_global=2.0,
    )


def _textos(record: logging.LogRecord) -> list[str]:
    textos = [str(record.msg), record.getMessage(), str(record.args)]
    if record.exc_info:
        textos.append("".join(traceback.format_exception(*record.exc_info)))
    if record.exc_text:
        textos.append(record.exc_text)
    return textos


def clave_en_registros(caplog) -> bool:
    return any(CLAVE_FALSA in t for r in caplog.records for t in _textos(r)) or CLAVE_FALSA in caplog.text


@pytest.fixture
def con_clave(monkeypatch, caplog):
    monkeypatch.setenv("OPENAI_API_KEY", CLAVE_FALSA)
    caplog.set_level(logging.DEBUG)
    return caplog


@pytest.mark.asyncio
async def test_flujo_sin_cliente_no_registra_la_clave(monkeypatch, con_clave):
    monkeypatch.setattr(inference_engine, "AsyncOpenAI", None)
    await inference_engine.generar_plan_mitigacion(_request())
    assert not clave_en_registros(con_clave)


@pytest.mark.asyncio
async def test_flujo_con_error_del_proveedor_no_registra_la_clave(monkeypatch, con_clave):
    class ClienteQueFalla:
        def __init__(self, api_key):
            self.beta = self
            self.chat = self
            self.completions = self
            self._clave = api_key

        async def parse(self, **_):
            raise RuntimeError(f"401 credencial rechazada: {self._clave}")

    monkeypatch.setattr(inference_engine, "AsyncOpenAI", ClienteQueFalla)
    await inference_engine.generar_plan_mitigacion(_request())
    assert not clave_en_registros(con_clave)


def _fuga_f_string(logger):
    logger.info(f"Intentando invocar LLM con API KEY {CLAVE_FALSA}")


def _fuga_argumento(logger):
    logger.info("Intentando invocar LLM con API KEY %s", CLAVE_FALSA)


def _fuga_logger_hijo(logger):
    logging.getLogger(NOMBRE_LOGGER + ".hijo").info("clave %s", CLAVE_FALSA)


def _fuga_traza(logger):
    try:
        raise RuntimeError(f"fallo con {CLAVE_FALSA}")
    except RuntimeError:
        logger.exception("Error al invocar")


# ¤test-api-logger-filter
@pytest.mark.parametrize("fuga", [_fuga_f_string, _fuga_argumento, _fuga_logger_hijo, _fuga_traza])
def test_el_detector_ve_las_cuatro_vias_de_fuga(con_clave, fuga):
    """Control del árbitro: cada vía, inyectada a propósito, debe quedar detectada."""
    fuga(logging.getLogger(NOMBRE_LOGGER))
    assert clave_en_registros(con_clave)
