# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""Pruebas de PLAT-01: Alta idempotente de organizaciones sintéticas en plataforma_service."""
from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from app_core.errors import ErrorNegocio
from features.plataforma.plataforma_service import (
    OrganizacionSintetica,
    asegurar_organizacion_sintetica,
    asegurar_persona_sintetica,
)
from features.plataforma.services.organizacion_sintetica_engine import PREFIJO_RUC_SINTETICO

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture
def mock_entorno_valido(monkeypatch):
    monkeypatch.setenv("APP_ENV", "pruebas")
    monkeypatch.delenv("AUTH_MODE", raising=False)
    monkeypatch.setattr("features.plataforma.services.organizacion_sintetica_engine.validar_arranque", lambda: "pruebas")


def test_ningun_archivo_de_api_ni_routes_importa_la_compuerta():
    """R6 · Sin superficie HTTP: ningún router de api/ ni features/*/routes/ importa las funciones."""
    carpetas = [RAIZ / "api"] + list(RAIZ.glob("features/*/routes"))
    archivos = [p for c in carpetas if c.exists() for p in c.rglob("*.py")]
    assert len(archivos) > 0

    objetivos = {"asegurar_organizacion_sintetica", "asegurar_persona_sintetica", "OrganizacionSintetica"}

    for p in archivos:
        arbol = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.ImportFrom):
                if nodo.module and "organizacion_sintetica" in nodo.module:
                    pytest.fail(f"{p.relative_to(RAIZ)} importa directamente de organizacion_sintetica_engine")
                for alias in nodo.names:
                    if alias.name in objetivos:
                        pytest.fail(f"{p.relative_to(RAIZ)} importa {alias.name}")
            elif isinstance(nodo, ast.Import):
                for alias in nodo.names:
                    if "organizacion_sintetica" in alias.name:
                        pytest.fail(f"{p.relative_to(RAIZ)} importa {alias.name}")


@pytest.mark.parametrize("entorno_invalido", ["development", "test", "production", "staging", ""])
@pytest.mark.asyncio
async def test_entorno_no_sintetico_falla_antes_de_la_primera_consulta(entorno_invalido, monkeypatch):
    """R1 · Entorno primero: fuera de pruebas y demo falla antes de cualquier execute()."""
    monkeypatch.setenv("APP_ENV", entorno_invalido)

    sesion = AsyncMock()
    sesion.execute.side_effect = RuntimeError("execute() no debió llamarse")

    org = OrganizacionSintetica(
        id="ep-org-test",
        nombre_comercial="Org Test",
        razon_social="Org Test SA",
        ruc=f"{PREFIJO_RUC_SINTETICO}0001",
        sector="Pruebas",
        tamano="micro",
    )

    with pytest.raises(ErrorNegocio) as exc_org:
        await asegurar_organizacion_sintetica(sesion, org)
    assert exc_org.value.code == "ENTORNO_NO_SINTETICO"
    sesion.execute.assert_not_called()

    with pytest.raises(ErrorNegocio) as exc_per:
        await asegurar_persona_sintetica(sesion, "ep-org-test", "persona@example.test", "Persona")
    assert exc_per.value.code == "ENTORNO_NO_SINTETICO"
    sesion.execute.assert_not_called()


@pytest.mark.asyncio
async def test_demo_con_huella_de_produccion_falla_antes_de_primera_consulta(monkeypatch):
    """R1: demo con DATABASE_URL conteniendo la huella de producción falla antes de execute()."""
    huella = "prod-proy-123456"
    monkeypatch.setenv("APP_ENV", "demo")
    monkeypatch.delenv("AUTH_MODE", raising=False)
    monkeypatch.setenv("HUELLA_PROYECTO_PRODUCCION", huella)
    monkeypatch.setenv("DATABASE_URL", f"postgresql://usr:pwd@{huella}.db/prod")

    sesion = AsyncMock()
    sesion.execute.side_effect = RuntimeError("execute() no debió llamarse")

    org = OrganizacionSintetica(
        id="ep-org-test",
        nombre_comercial="Org Test",
        razon_social="Org Test SA",
        ruc=f"{PREFIJO_RUC_SINTETICO}0001",
        sector="Pruebas",
        tamano="micro",
    )

    with pytest.raises(ErrorNegocio) as exc:
        await asegurar_organizacion_sintetica(sesion, org)
    assert exc.value.code == "ENTORNO_NO_SINTETICO"
    sesion.execute.assert_not_called()


@pytest.mark.asyncio
async def test_ruc_no_sintetico_da_error(mock_entorno_valido):
    """RUC que no comienza con PREFIJO_RUC_SINTETICO falla con RUC_NO_SINTETICO."""
    sesion = AsyncMock()
    org_real = OrganizacionSintetica(
        id="org-real",
        nombre_comercial="Empresa Real",
        razon_social="Empresa Real Cia",
        ruc="1790012345001",
        sector="Banca",
        tamano="grande",
    )

    with pytest.raises(ErrorNegocio) as exc:
        await asegurar_organizacion_sintetica(sesion, org_real)
    assert exc.value.code == "RUC_NO_SINTETICO"
    sesion.execute.assert_not_called()


@pytest.mark.asyncio
async def test_organizacion_existente_sin_marca_sintetica_da_error_m2(mock_entorno_valido):
    """R3: si la base ya tiene una org con ese RUC/id sin la marca sintética, falla ORGANIZACION_NO_SINTETICA (m2)."""
    sesion = AsyncMock()
    mock_res_insert = MagicMock()
    mock_res_insert.scalar_one_or_none.return_value = None

    mock_res_select = MagicMock()
    mock_res_select.first.return_value = ("org-existente", "1790012345001")

    sesion.execute.side_effect = [mock_res_insert, mock_res_select]

    org = OrganizacionSintetica(
        id="org-existente",
        nombre_comercial="Org Sintetica",
        razon_social="Org Sintetica SA",
        ruc=f"{PREFIJO_RUC_SINTETICO}0001",
        sector="Servicios",
        tamano="micro",
    )

    with pytest.raises(ErrorNegocio) as exc:
        await asegurar_organizacion_sintetica(sesion, org)
    assert exc.value.code == "ORGANIZACION_NO_SINTETICA"


@pytest.mark.asyncio
async def test_persona_para_tenant_no_sintetico_da_error(mock_entorno_valido):
    """R4: asegurar persona para un tenant no sintético falla ORGANIZACION_NO_DISPONIBLE."""
    sesion = AsyncMock()
    mock_res_tenant = MagicMock()
    mock_res_tenant.first.return_value = ("1790000000001",)  # RUC no sintético

    sesion.execute.return_value = mock_res_tenant

    with pytest.raises(ErrorNegocio) as exc:
        await asegurar_persona_sintetica(sesion, "tenant-real", "test@example.test", "Nombre")
    assert exc.value.code == "ORGANIZACION_NO_DISPONIBLE"


@pytest.mark.asyncio
async def test_alta_sintetica_idempotente_y_auditoria_sin_datos_personales(mock_entorno_valido):
    """R2 y R7: inserción idempotente y auditoría sin datos personales."""
    sesion = AsyncMock()

    # 1. Primera llamada: crea org
    mock_insert_crea = MagicMock()
    mock_insert_crea.scalar_one_or_none.return_value = "ep-org-1"
    mock_select = MagicMock()
    mock_select.first.return_value = ("ep-org-1", f"{PREFIJO_RUC_SINTETICO}0001")
    mock_audit = MagicMock()

    sesion.execute.side_effect = [mock_insert_crea, mock_select, mock_audit]

    org = OrganizacionSintetica(
        id="ep-org-1",
        nombre_comercial="Org 1",
        razon_social="Org 1 SA",
        ruc=f"{PREFIJO_RUC_SINTETICO}0001",
        sector="Servicios",
        tamano="micro",
    )
    creada = await asegurar_organizacion_sintetica(sesion, org)
    assert creada is True

    # Comprueba llamada de auditoría (3ra llamada a execute)
    audit_call = sesion.execute.call_args_list[2]
    audit_params = audit_call[0][1]
    assert audit_params["actor_tipo"] == "sistema"
    assert audit_params["accion"] == "alta_sintetica"
    assert "sintetica" in audit_params["payload"]
    assert "nombre" not in audit_params["payload"]
    assert "correo" not in audit_params["payload"]

    # 2. Segunda llamada: ya existe (ON CONFLICT devuelve None)
    mock_insert_existente = MagicMock()
    mock_insert_existente.scalar_one_or_none.return_value = None
    sesion.execute.side_effect = [mock_insert_existente, mock_select]

    creada_segunda = await asegurar_organizacion_sintetica(sesion, org)
    assert creada_segunda is False
