# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤rbac-tenant ¤arbitro
"""BIB-101 · Contexto y acceso de Biblioteca.

Criterio 2 del kit: una cuenta sin asignación en una organización recibe denegación al pedir sus
documentos por API. Biblioteca no tiene todavía rutas de documentos (las crea BIB-107); aquí se
prueba la compuerta por la que pasarán, `get_current_tenant` (app_core/security.py), con la misma
forma en que el frontend de Biblioteca pide (`X-Tenant-ID` de la sesión, nunca en la URL).

Sin base de datos: el usuario verificado y sus roles se simulan, así que esto NO acredita RLS ni
persistencia. Las comprobaciones estáticas fijan el contrato del frontend (BIB-101) con FE-22.

Mutación decisiva: quitar `if not roles: raise ...403` en `autenticar_en_tenant` hace fallar
`test_organizacion_ajena_se_deniega_por_api`.
"""
import re
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app_core import security

RAIZ = Path(__file__).resolve().parent.parent
PROPIA, AJENA = "org-propia-bib101", "org-ajena-bib101"
RUTA = "/prueba/biblioteca/pendientes"


class _SesionFalsa:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def commit(self):
        return None


@pytest.fixture
def api(monkeypatch):
    """App mínima con una ruta tras la compuerta de tenant, en modo oidc y sin base de datos."""
    monkeypatch.setenv("AUTH_MODE", "oidc")
    if "app_core.db.session" in sys.modules:
        monkeypatch.setattr(sys.modules["app_core.db.session"], "async_session_factory", _SesionFalsa)
    else:
        falso = ModuleType("app_core.db.session")
        falso.async_session_factory = _SesionFalsa
        monkeypatch.setitem(sys.modules, "app_core.db.session", falso)
    monkeypatch.setattr(security, "usuario_verificado",
                        AsyncMock(return_value=SimpleNamespace(usuario_id="usuario-bib101")))

    async def roles(_sesion, tenant_id, _usuario):
        return {"implementador"} if tenant_id == PROPIA else set()

    monkeypatch.setattr(security, "roles_activos", roles)

    app = FastAPI()

    @app.get(RUTA)
    async def pendientes(tenant_id: str = Depends(security.get_current_tenant)):
        return {"tenant": tenant_id, "borrador": 0, "en_revision": 0, "por_vencer": 0, "vencidos": 0, "total": 0}

    return TestClient(app)


def _pedir(api, tenant=None):
    cabeceras = {"Authorization": "Bearer token-de-prueba"}
    if tenant:
        cabeceras["X-Tenant-ID"] = tenant
    return api.get(RUTA, headers=cabeceras)


def test_organizacion_propia_entra_con_la_organizacion_de_la_sesion(api):
    r = _pedir(api, PROPIA)
    assert r.status_code == 200
    assert r.json()["tenant"] == PROPIA


def test_organizacion_ajena_se_deniega_por_api(api):
    r = _pedir(api, AJENA)
    assert r.status_code == 403
    assert AJENA not in r.text


def test_sin_organizacion_no_hay_organizacion_por_defecto(api):
    assert _pedir(api).status_code == 401



