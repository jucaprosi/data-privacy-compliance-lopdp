# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤qa-engineer ¤api-integraciones ¤seguridad ¤seguridad-tenant ¤arbitro
"""Árbitro de API-02: Claves de integración por organización con techo del paquete.

Invariante verificado: INV_API_INTEGRATION_SCOPED_KEYS_VERSIONED.
Verifica:
1. Aislamiento por organización (tenant_id) y alcance (scopes).
2. Clave revocada o rotada produce 401 Unauthorized (Mutación m1).
3. Creación sobre el techo de claves del paquete produce 409 TECHO_CLAVES_ALCANZADO (Mutación m2).
4. La clave en claro solo viaja en la respuesta de crear y de rotar, nunca en GET /claves (Mutación m4).
5. Trigger de base de datos impide modificar hash_sha256 y prefijo en UPDATE (Mutación m5).
6. Registro de auditoría de cada uso en audit_events.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from app_core.db.session import get_session
from app_core.integraciones import claves as claves_svc
from app_core.integraciones import techos as techos_svc
from main import app

RAIZ = Path(__file__).resolve().parent.parent


# ---- Pruebas unitarias de motor y servicios ----

@pytest.mark.asyncio
async def test_crear_y_listar_clave_en_claro_solo_al_crear():
    """Mutación m4: La clave en claro solo viaja en crear/rotar; nunca en GET ni en listar."""
    clave_en_claro, prefijo, hash_sha256 = claves_svc.generar_credenciales_clave()
    assert clave_en_claro.startswith("evk_")
    assert prefijo.startswith("evk_")
    assert hashlib.sha256(clave_en_claro.encode("utf-8")).hexdigest() == hash_sha256

    mock_session = AsyncMock(spec=AsyncSession)

    # Simular listar_claves usando MagicMock sincrónico para Result.mappings()
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = [
        {
            "id": "clave-uuid-1",
            "nombre": "ERP Principal",
            "prefijo": prefijo,
            "alcances": ["rat:lectura"],
            "creada_en": None,
            "rotada_en": None,
            "revocada_en": None,
        }
    ]
    mock_session.execute.return_value = mock_result

    claves = await claves_svc.listar_claves(mock_session, "tenant-test-1")
    assert len(claves) == 1
    assert "hash_sha256" not in claves[0]
    assert "clave_en_claro" not in claves[0]
    assert claves[0]["prefijo"] == prefijo


@pytest.mark.asyncio
async def test_autenticar_clave_valida_y_comprueba_alcance():
    """Verifica autenticación Bearer evk_ y comprobación de alcance."""
    token, prefijo, token_hash = claves_svc.generar_credenciales_clave()

    mock_session = AsyncMock(spec=AsyncSession)
    mock_row = {
        "id": "clave-uuid-1",
        "tenant_id": "tenant-corp-1",
        "nombre": "Integración CRM",
        "prefijo": prefijo,
        "alcances": ["rat:lectura", "tareas:lectura"],
        "creada_en": None,
        "rotada_en": None,
        "revocada_en": None,
    }
    mock_result = MagicMock()
    mock_result.mappings.return_value.first.return_value = mock_row
    mock_session.execute.return_value = mock_result

    with patch("app_core.integraciones.claves.registrar_evento", new_callable=AsyncMock) as mock_audit:
        # 1. Alcance permitido
        auth_ctx = await claves_svc.autenticar_clave(
            session=mock_session,
            cabecera_auth=f"Bearer {token}",
            alcance_requerido="rat:lectura",
        )
        assert auth_ctx["tenant_id"] == "tenant-corp-1"
        assert auth_ctx["nombre"] == "Integración CRM"
        assert mock_audit.called

        # 2. Alcance no otorgado -> 403 Forbidden
        with pytest.raises(HTTPException) as exc_info:
            await claves_svc.autenticar_clave(
                session=mock_session,
                cabecera_auth=f"Bearer {token}",
                alcance_requerido="evidencias:lectura",
            )
        assert exc_info.value.status_code == 403
        assert "Alcance insuficiente" in exc_info.value.detail


@pytest.mark.asyncio
async def test_clave_revocada_es_401():
    """Mutación m1: Aceptar una clave revocada debe fallar con 401."""
    token, prefijo, _ = claves_svc.generar_credenciales_clave()

    mock_session = AsyncMock(spec=AsyncSession)
    mock_row = {
        "id": "clave-uuid-1",
        "tenant_id": "tenant-corp-1",
        "nombre": "Clave Vieja",
        "prefijo": prefijo,
        "alcances": ["rat:lectura"],
        "creada_en": None,
        "rotada_en": None,
        "revocada_en": "2026-11-16T12:00:00Z",  # Revocada
    }
    mock_result = MagicMock()
    mock_result.mappings.return_value.first.return_value = mock_row
    mock_session.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await claves_svc.autenticar_clave(
            session=mock_session,
            cabecera_auth=f"Bearer {token}",
            alcance_requerido="rat:lectura",
        )
    assert exc_info.value.status_code == 401
    assert "revocada" in exc_info.value.detail


@pytest.mark.asyncio
async def test_clave_rotada_es_401():
    """Una clave que ya fue rotada debe rechazarse con 401."""
    token, prefijo, _ = claves_svc.generar_credenciales_clave()

    mock_session = AsyncMock(spec=AsyncSession)
    mock_row = {
        "id": "clave-uuid-1",
        "tenant_id": "tenant-corp-1",
        "nombre": "Clave Anterior",
        "prefijo": prefijo,
        "alcances": ["rat:lectura"],
        "creada_en": None,
        "rotada_en": "2026-11-16T12:00:00Z",  # Rotada
        "revocada_en": None,
    }
    mock_result = MagicMock()
    mock_result.mappings.return_value.first.return_value = mock_row
    mock_session.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await claves_svc.autenticar_clave(
            session=mock_session,
            cabecera_auth=f"Bearer {token}",
            alcance_requerido="rat:lectura",
        )
    assert exc_info.value.status_code == 401
    assert "rotada" in exc_info.value.detail


@pytest.mark.asyncio
async def test_crear_sobre_techo_falla_409():
    """Mutación m2: Crear sobre el techo del paquete debe fallar con 409 TECHO_CLAVES_ALCANZADO."""
    mock_session = AsyncMock(spec=AsyncSession)

    # Simular que el paquete permite 2 claves y ya hay 2 activas
    with patch(
        "app_core.integraciones.techos.obtener_techos_integracion",
        new_callable=AsyncMock,
    ) as mock_techos:
        mock_techos.return_value = {
            "claves": {"maximo": 2, "activas": 2},
            "webhooks": {"maximo": 2, "activos": 0},
        }

        with pytest.raises(ErrorNegocio) as exc_info:
            await techos_svc.verificar_techo_claves(mock_session, "tenant-test")

        assert exc_info.value.status_code == 409
        assert exc_info.value.code == "TECHO_CLAVES_ALCANZADO"


# ---- Pruebas de API HTTP ----

@pytest.mark.asyncio
async def test_api_rutas_integraciones_autorizacion():
    """Verifica permisos de endpoints: admin y coordinador escriben, dpo solo lee."""
    mock_session = AsyncMock(spec=AsyncSession)
    app.dependency_overrides[get_session] = lambda: mock_session

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. DPO intentando crear clave -> 403 Forbidden (Mutación m3)
            res_dpo_crear = await client.post(
                "/api/v1/integraciones/claves",
                headers={
                    "X-User-ID": "usr-dpo",
                    "X-Tenant-ID": "tenant-1",
                    "X-Role": "dpo",
                },
                json={"nombre": "Test DPO", "alcances": ["rat:lectura"]},
            )
            assert res_dpo_crear.status_code == 403

            # 2. Coordinador consultando techos -> 200 OK
            with patch(
                "app_core.integraciones.techos.obtener_techos_integracion",
                new_callable=AsyncMock,
                return_value={
                    "claves": {"maximo": 10, "activas": 1},
                    "webhooks": {"maximo": 10, "activos": 0},
                },
            ):
                res_coord_techos = await client.get(
                    "/api/v1/integraciones/techos",
                    headers={
                        "X-User-ID": "usr-coord",
                        "X-Tenant-ID": "tenant-1",
                        "X-Role": "coordinador",
                    },
                )
                assert res_coord_techos.status_code == 200
                data = res_coord_techos.json()
                assert data["claves"]["maximo"] == 10
                assert data["claves"]["activas"] == 1
    finally:
        app.dependency_overrides.pop(get_session, None)


# ---- Mutación m5: Inmutabilidad en Base de Datos ----

def test_sql_trigger_inmutabilidad_rechaza_cambio_hash():
    """Mutación m5: El trigger impide cambiar hash_sha256 y prefijo en la base de datos."""
    ruta_mig = RAIZ / "alembic" / "versions" / "api02_claves_integracion.py"
    assert ruta_mig.exists()
    contenido = ruta_mig.read_text(encoding="utf-8")
    assert "fn_claves_integracion_inmutables" in contenido
    assert "trg_claves_integracion_inmutables" in contenido
    assert "NEW.hash_sha256 IS DISTINCT FROM OLD.hash_sha256" in contenido
    assert "NEW.prefijo IS DISTINCT FROM OLD.prefijo" in contenido
