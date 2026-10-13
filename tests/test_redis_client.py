# ¤arbitro
"""Pruebas unitarias de aislamiento para app_core.queue.redis_client con mocks.

Verifica:
- Encolar job válido: serialización JSON, TTL y RPUSH en cola.
- Encolar sin job_id: lanza ValueError.
- Consumir próximo job: LPOP desde la cola designada.
- Obtener estado de job: deserialización automática de payload si existe y None si no existe.
- Actualizar estado de job: mapping con campos extras serializados (dict/list a JSON, escalares a str).
- get_client singleton: inicialización perezosa desde variable de entorno UPSTASH_REDIS_URL.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from app_core.queue import redis_client


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Garantiza aislamiento de singleton entre ejecuciones de pruebas."""
    orig_client = redis_client._client
    yield
    redis_client._client = orig_client


def test_enqueue_job_valido():
    mock_redis = MagicMock()
    redis_client._client = mock_redis

    payload = {"job_id": "job-test-01", "param": "valor", "items": [1, 2, 3]}
    res = redis_client.enqueue_job(payload)

    assert res == "job-test-01"
    mock_redis.hset.assert_called_once()
    call_args = mock_redis.hset.call_args
    assert call_args[0][0] == "roadmap_job:job-test-01"
    mapping = call_args[1]["mapping"]
    assert mapping["status"] == "queued"
    assert json.loads(mapping["payload"]) == payload

    mock_redis.expire.assert_called_once_with("roadmap_job:job-test-01", redis_client.JOB_TTL_SECONDS)
    mock_redis.rpush.assert_called_once_with(redis_client.QUEUE_NAME, "job-test-01")


def test_enqueue_job_sin_job_id_lanza_value_error():
    mock_redis = MagicMock()
    redis_client._client = mock_redis

    with pytest.raises(ValueError, match="payload requiere job_id"):
        redis_client.enqueue_job({"param": "sin-id"})

    assert mock_redis.hset.call_count == 0
    assert mock_redis.rpush.call_count == 0


def test_pop_job_retorna_job_id_o_none():
    mock_redis = MagicMock()
    redis_client._client = mock_redis

    mock_redis.lpop.return_value = "job-pop-1"
    assert redis_client.pop_job() == "job-pop-1"
    mock_redis.lpop.assert_called_with(redis_client.QUEUE_NAME)

    mock_redis.lpop.return_value = None
    assert redis_client.pop_job() is None


def test_get_job_status_existente_con_payload():
    mock_redis = MagicMock()
    redis_client._client = mock_redis

    datos_job = {
        "status": "processing",
        "payload": json.dumps({"foo": "bar", "num": 42}, ensure_ascii=False),
        "intentos": "1",
    }
    mock_redis.hgetall.return_value = datos_job

    resultado = redis_client.get_job_status("job-42")
    assert resultado is not None
    assert resultado["status"] == "processing"
    assert resultado["payload"] == {"foo": "bar", "num": 42}
    assert resultado["intentos"] == "1"
    mock_redis.hgetall.assert_called_once_with("roadmap_job:job-42")


def test_get_job_status_existente_con_payload_invalido():
    mock_redis = MagicMock()
    redis_client._client = mock_redis

    datos_job = {
        "status": "processing",
        "payload": "{invalid-json",
    }
    mock_redis.hgetall.return_value = datos_job

    resultado = redis_client.get_job_status("job-bad-payload")
    assert resultado is not None
    assert resultado["payload"] == "{invalid-json"


def test_get_job_status_inexistente():
    mock_redis = MagicMock()
    redis_client._client = mock_redis

    mock_redis.hgetall.return_value = {}
    resultado = redis_client.get_job_status("job-inexistente")
    assert resultado is None


def test_set_job_status_sin_extra():
    mock_redis = MagicMock()
    redis_client._client = mock_redis

    redis_client.set_job_status("job-100", "completed")
    mock_redis.hset.assert_called_once_with(
        "roadmap_job:job-100",
        mapping={"status": "completed"},
    )
    mock_redis.expire.assert_called_once_with("roadmap_job:job-100", redis_client.JOB_TTL_SECONDS)


def test_set_job_status_con_extra_mixto():
    mock_redis = MagicMock()
    redis_client._client = mock_redis

    extra = {
        "resultado": {"progreso": 100, "fase": "finalizada"},
        "errores": ["warn1"],
        "codigo": 200,
        "activo": True,
    }
    redis_client.set_job_status("job-200", "failed", extra=extra)

    mock_redis.hset.assert_called_once()
    call_mapping = mock_redis.hset.call_args[1]["mapping"]
    assert call_mapping["status"] == "failed"
    assert json.loads(call_mapping["resultado"]) == {"progreso": 100, "fase": "finalizada"}
    assert json.loads(call_mapping["errores"]) == ["warn1"]
    assert call_mapping["codigo"] == "200"
    assert call_mapping["activo"] == "True"


def test_get_client_inicializacion_singleton():
    redis_client._client = None
    with patch.dict("os.environ", {"UPSTASH_REDIS_URL": "rediss://default:token@cluster.upstash.io:6379"}):
        with patch("redis.from_url") as mock_from_url:
            mock_instancia = MagicMock()
            mock_from_url.return_value = mock_instancia

            c1 = redis_client.get_client()
            c2 = redis_client.get_client()

            assert c1 is mock_instancia
            assert c2 is mock_instancia
            mock_from_url.assert_called_once_with(
                "rediss://default:token@cluster.upstash.io:6379",
                decode_responses=True,
            )
