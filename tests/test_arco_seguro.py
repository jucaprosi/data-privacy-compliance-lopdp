"""Contrato de seguridad del endpoint ARCO+ persistente."""

from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app_core.db.session import get_tenant_session
from main import app


TENANT = "00000000-0000-0000-0000-000000000008"
OTRO_TENANT = "00000000-0000-0000-0000-000000000099"


@pytest.fixture
def sesion():
    session = Mock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def cliente(sesion):
    async def sobrescribir_sesion():
        yield sesion

    app.dependency_overrides[get_tenant_session] = sobrescribir_sesion
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.pop(get_tenant_session, None)


def payload_valido(**cambios):
    payload = {
        "tenant_id": OTRO_TENANT,
        "tipo_solicitud": "RECTIFICACION",
        "cedula_solicitante": "1712345678",
        "nombre_solicitante": "Ana Titular",
    }
    payload.update(cambios)
    return payload


def test_post_persiste_y_ignora_tenant_del_cuerpo(cliente, sesion):
    respuesta = cliente.post(
        "/api/v1/arco/solicitudes",
        headers={"X-Tenant-ID": TENANT},
        json=payload_valido(),
    )

    assert respuesta.status_code == 200
    creada = sesion.add.call_args.args[0]
    assert creada.tenant_id == UUID(TENANT)
    assert respuesta.json()["tenant_id"] == TENANT
    sesion.flush.assert_awaited_once()
    sesion.refresh.assert_awaited_once_with(creada)


def test_sin_identidad_responde_401(cliente):
    respuesta = cliente.post("/api/v1/arco/solicitudes", json=payload_valido())
    assert respuesta.status_code == 401


@pytest.mark.parametrize(
    "cambio",
    [
        {"tipo_solicitud": "BORRADO"},
        {"cedula_solicitante": "12"},
        {"nombre_solicitante": ""},
    ],
)
def test_cuerpo_invalido_responde_422(cliente, cambio):
    respuesta = cliente.post(
        "/api/v1/arco/solicitudes",
        headers={"X-Tenant-ID": TENANT},
        json=payload_valido(**cambio),
    )
    assert respuesta.status_code == 422
