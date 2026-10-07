"""Cliente Upstash Redis (TCP) para cola de jobs.

- Encolar: RPUSH roadmap_jobs.
- Consumir: LPOP con polling adaptativo.
- Estado de job: hash roadmap_job:{job_id}.
"""
import json
import os

import redis

_client = None
QUEUE_NAME = "roadmap_jobs"
JOB_TTL_SECONDS = 3600


def get_client():
    """Devuelve un cliente Redis singleton."""
    global _client
    if _client is None:
        _client = redis.from_url(
            os.environ["UPSTASH_REDIS_URL"],
            decode_responses=True,
        )
    return _client


def enqueue_job(payload: dict) -> str:
    """Encola un job y devuelve su job_id."""
    job_id = payload.get("job_id")
    if not job_id:
        raise ValueError("payload requiere job_id")
    client = get_client()
    client.hset(
        f"roadmap_job:{job_id}",
        mapping={
            "status": "queued",
            "payload": json.dumps(payload, ensure_ascii=False),
        },
    )
    client.expire(f"roadmap_job:{job_id}", JOB_TTL_SECONDS)
    client.rpush(QUEUE_NAME, job_id)
    return job_id


def pop_job():
    """Saca el próximo job_id de la cola. Devuelve None si está vacía."""
    return get_client().lpop(QUEUE_NAME)


def get_job_status(job_id: str):
    """Devuelve el estado de un job. None si no existe."""
    data = get_client().hgetall(f"roadmap_job:{job_id}")
    if not data:
        return None
    if "payload" in data:
        try:
            data["payload"] = json.loads(data["payload"])
        except (TypeError, ValueError):
            pass
    return data


def set_job_status(job_id: str, status: str, extra: dict | None = None) -> None:
    """Actualiza el estado de un job."""
    client = get_client()
    mapping = {"status": status}
    if extra:
        for k, v in extra.items():
            mapping[k] = (
                json.dumps(v, ensure_ascii=False)
                if isinstance(v, (dict, list))
                else str(v)
            )
    client.hset(f"roadmap_job:{job_id}", mapping=mapping)
    client.expire(f"roadmap_job:{job_id}", JOB_TTL_SECONDS)
