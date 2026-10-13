# ¤adpa
"""Pruebas unitarias para el catálogo y manejador de excepciones de negocio (RM-00)."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app_core.errors import (
    CATALOGO_ERRORES,
    TENANT_SIZE_NOT_CONFIGURED,
    SOD_VIOLATION,
    DPO_INDEPENDENCE_VIOLATED,
    SELF_VALIDATION_FORBIDDEN,
    MEMBER_ALREADY_EXISTS,
    LAST_ADMIN_CANNOT_BE_REVOKED,
    CodigoErrorNegocio,
)
from api.errores import ErrorNegocio, error_negocio_handler


def test_catalogo_errores_codigos_esperados():
    """Verifica que el catálogo contenga los códigos obligatorios de RM-00 y PRD Módulo 5."""
    assert TENANT_SIZE_NOT_CONFIGURED.codigo == "TENANT_SIZE_NOT_CONFIGURED"
    assert TENANT_SIZE_NOT_CONFIGURED.status_code == 409
    assert TENANT_SIZE_NOT_CONFIGURED.action_required == "configure_tenant_size"

    assert SOD_VIOLATION.codigo == "SOD_VIOLATION"
    assert SOD_VIOLATION.status_code == 409

    assert DPO_INDEPENDENCE_VIOLATED.codigo == "DPO_INDEPENDENCE_VIOLATED"
    assert DPO_INDEPENDENCE_VIOLATED.status_code == 409

    assert SELF_VALIDATION_FORBIDDEN.codigo == "SELF_VALIDATION_FORBIDDEN"
    assert SELF_VALIDATION_FORBIDDEN.status_code == 403

    assert MEMBER_ALREADY_EXISTS.codigo == "MEMBER_ALREADY_EXISTS"
    assert MEMBER_ALREADY_EXISTS.status_code == 409

    assert LAST_ADMIN_CANNOT_BE_REVOKED.codigo == "LAST_ADMIN_CANNOT_BE_REVOKED"
    assert LAST_ADMIN_CANNOT_BE_REVOKED.status_code == 409

    for cod in [
        "TENANT_SIZE_NOT_CONFIGURED",
        "SOD_VIOLATION",
        "DPO_INDEPENDENCE_VIOLATED",
        "SELF_VALIDATION_FORBIDDEN",
        "MEMBER_ALREADY_EXISTS",
        "LAST_ADMIN_CANNOT_BE_REVOKED",
    ]:
        assert cod in CATALOGO_ERRORES


def test_error_negocio_instanciacion_con_objeto():
    """Prueba instanciación con objeto CodigoErrorNegocio."""
    exc = ErrorNegocio(TENANT_SIZE_NOT_CONFIGURED)
    assert exc.code == "TENANT_SIZE_NOT_CONFIGURED"
    assert exc.status_code == 409
    assert exc.action_required == "configure_tenant_size"
    assert exc.detail == "El tamaño de la organización no está configurado."


def test_error_negocio_instanciacion_con_str_conocido():
    """Prueba instanciación con string presente en catálogo."""
    exc = ErrorNegocio("SOD_VIOLATION", detail="Conflicto detectado")
    assert exc.code == "SOD_VIOLATION"
    assert exc.status_code == 409
    assert exc.detail == "Conflicto detectado"
    assert exc.action_required is None


def test_error_negocio_instanciacion_con_str_desconocido():
    """Prueba instanciación libre con string fuera de catálogo."""
    exc = ErrorNegocio("CODIGO_PERSONALIZADO", detail="Error custom", status_code=422, action_required="revisar")
    assert exc.code == "CODIGO_PERSONALIZADO"
    assert exc.status_code == 422
    assert exc.detail == "Error custom"
    assert exc.action_required == "revisar"


def test_manejador_error_negocio_formato_json():
    """Prueba que el manejador FastAPI responda status_code y estructura JSON de tres campos."""
    app_test = FastAPI()
    app_test.add_exception_handler(ErrorNegocio, error_negocio_handler)

    @app_test.get("/falla-tamano")
    def ruta_tamano():
        raise ErrorNegocio(TENANT_SIZE_NOT_CONFIGURED)

    @app_test.get("/falla-cuatro-ojos")
    def ruta_cuatro_ojos():
        raise ErrorNegocio(
            SELF_VALIDATION_FORBIDDEN,
            detail="Quien sube la evidencia no puede aprobarla",
        )

    cliente = TestClient(app_test)

    # 1. Caso 409 TENANT_SIZE_NOT_CONFIGURED
    resp1 = cliente.get("/falla-tamano")
    assert resp1.status_code == 409
    data1 = resp1.json()
    assert data1["code"] == "TENANT_SIZE_NOT_CONFIGURED"
    assert data1["action_required"] == "configure_tenant_size"
    assert data1["detail"] == "El tamaño de la organización no está configurado."

    # 2. Caso 403 SELF_VALIDATION_FORBIDDEN
    resp2 = cliente.get("/falla-cuatro-ojos")
    assert resp2.status_code == 403
    data2 = resp2.json()
    assert data2["code"] == "SELF_VALIDATION_FORBIDDEN"
    assert data2["action_required"] is None
    assert data2["detail"] == "Quien sube la evidencia no puede aprobarla"
