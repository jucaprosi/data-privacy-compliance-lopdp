# -*- coding: utf-8 -*-
# ¤rbac-tenant ¤arbitro
"""ORG-22: el rol auditor existe, lee, registra y verifica en CAPA, y no ejecuta ni cierra.

Mutaciones documentadas:
  - quitar `Role.auditor` → fallan todas (AttributeError);
  - añadir `auditor` a ROLES_CIERRE_CAPA, ROLES_GESTION o ROLES_VENCIMIENTO → falla
    test_el_auditor_no_ejecuta_ni_cierra;
  - quitarlo de ROLES_REGISTRO_CAPA, ROLES_LECTURA_CAPA, ROLES_CONSULTA o ROLES_VERIFICACION → falla
    test_el_auditor_lee_registra_y_verifica_en_capa;
  - quitar las tuplas (auditor, implementador) → falla test_la_incompatibilidad_con_implementador_esta_presente;
  - quitar al auditor de data/demo/cooperativa_demo.json → falla test_la_plantilla_demo_tiene_seis_personas_de_un_solo_rol.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.routers import auditoria_capa as capa
from api.routers import auditoria_capa_controles as controles
from features.organizacion import organizacion_service as org

RAIZ = Path(__file__).resolve().parents[1]


def test_el_rol_existe_y_no_se_acota_a_un_area():
    assert org.Role.auditor.value == "auditor"
    assert org.Role.auditor not in org.AREA_SCOPED_ROLES


def test_el_auditor_lee_registra_y_verifica_en_capa():
    assert "auditor" in capa.ROLES_REGISTRO_CAPA
    assert "auditor" in capa.ROLES_LECTURA_CAPA
    assert "auditor" in controles.ROLES_CONSULTA
    assert "auditor" in controles.ROLES_VERIFICACION


def test_el_auditor_no_ejecuta_ni_cierra():
    assert "auditor" not in capa.ROLES_CIERRE_CAPA
    assert "auditor" not in controles.ROLES_GESTION
    assert "auditor" not in controles.ROLES_VENCIMIENTO


def test_la_incompatibilidad_con_implementador_esta_presente():
    pares = {(a, b) for a, b, _, _ in org.INCOMPATIBILIDADES_ROLES}
    assert (org.Role.auditor, org.Role.implementador) in pares
    for a, b, motivo, base in org.INCOMPATIBILIDADES_ROLES:
        if org.Role.auditor in (a, b):
            assert motivo and "INV_LOPDP_AUDITOR_SOLE_ROLE" in base


def test_la_plantilla_demo_tiene_seis_personas_de_un_solo_rol():
    plantilla = json.loads((RAIZ / "data" / "demo" / "cooperativa_demo.json").read_text(encoding="utf-8"))
    personas = plantilla["personas"]
    assert len(personas) == 6
    assert sorted(p["rol"] for p in personas) == sorted(r.value for r in org.Role)
    assert all(p["correo"].endswith(".invalid") for p in personas)


@pytest.mark.asyncio
async def test_el_check_acepta_auditor(db_engine):
    fabrica = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    sufijo = uuid.uuid4().hex[:8]
    async with fabrica() as s:
        await s.execute(text(
            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
            "VALUES (:t, 'Org 22', 'Org 22 SA', :ruc, 'mediana')"), {"t": f"t-{sufijo}", "ruc": f"RUC{sufijo}"})
        await s.execute(text("INSERT INTO users (id, email, nombre, activo) VALUES (:u, :e, 'Persona', TRUE)"),
                        {"u": f"u-{sufijo}", "e": f"u-{sufijo}@org22.invalid"})
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": f"t-{sufijo}"})
        await s.execute(text(
            "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, 'auditor')"),
            {"i": f"utr-{sufijo}", "u": f"u-{sufijo}", "t": f"t-{sufijo}"})
        with pytest.raises(IntegrityError):
            async with s.begin_nested():
                await s.execute(text(
                    "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES ('utr-x', :u, :t, 'inventado')"),
                    {"u": f"u-{sufijo}", "t": f"t-{sufijo}"})
        await s.rollback()
