"""Reglas RBAC puras: SoD del DPO, cuatro ojos y contrato RoleGrant. Sin BD."""
import pytest
from pydantic import ValidationError

from app_core.schemas.rbac_schema import RoleGrant, UserCreate
from app_core.schemas.roadmap_schema import Role
from app_core.services.rbac_service import check_dpo_sod, check_four_eyes


@pytest.mark.parametrize("operativo", [Role.implementador, Role.encargado])
def test_dpo_rechazado_si_ya_tiene_rol_operativo(operativo):
    assert check_dpo_sod(Role.dpo, [operativo]) is not None


@pytest.mark.parametrize("operativo", [Role.implementador, Role.encargado])
def test_rol_operativo_rechazado_si_ya_es_dpo(operativo):
    assert check_dpo_sod(operativo, [Role.dpo]) is not None


@pytest.mark.parametrize("otro", [Role.admin_organizacion, Role.responsable_area])
def test_dpo_compatible_con_roles_no_operativos(otro):
    assert check_dpo_sod(Role.dpo, [otro]) is None
    assert check_dpo_sod(otro, [Role.dpo]) is None


def test_roles_operativos_compatibles_entre_si():
    assert check_dpo_sod(Role.encargado, [Role.implementador]) is None


def test_cuatro_ojos():
    assert check_four_eyes("u1", "u1") is not None
    assert check_four_eyes("u1", "u2") is None
    assert check_four_eyes(None, "u2") is None


def test_area_solo_para_responsable_area():
    assert RoleGrant(user_id="u", role=Role.responsable_area, area_id="a1").area_id == "a1"
    with pytest.raises(ValidationError):
        RoleGrant(user_id="u", role=Role.dpo, area_id="a1")


def test_rol_desconocido_rechazado():
    with pytest.raises(ValidationError):
        RoleGrant(user_id="u", role="superusuario")


def test_email_invalido_rechazado():
    with pytest.raises(ValidationError):
        UserCreate(email="no-es-email", nombre="X")
