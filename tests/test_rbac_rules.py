"""Reglas RBAC puras: SoD del DPO, cuatro ojos y contrato RoleGrant. Sin BD."""
import pytest
from pydantic import ValidationError

from features.organizacion.organizacion_service import (
    Role,
    RoleGrant,
    UserCreate,
    check_dpo_sod,
    check_four_eyes,
)


@pytest.mark.parametrize(
    "otro_rol",
    [Role.implementador, Role.coordinador, Role.responsable_area, Role.admin_organizacion],
)
def test_dpo_rechazado_si_ya_tiene_otro_rol(otro_rol):
    assert check_dpo_sod(Role.dpo, [otro_rol]) is not None


@pytest.mark.parametrize(
    "otro_rol",
    [Role.implementador, Role.coordinador, Role.responsable_area, Role.admin_organizacion],
)
def test_otro_rol_rechazado_si_ya_es_dpo(otro_rol):
    assert check_dpo_sod(otro_rol, [Role.dpo]) is not None


def test_roles_operativos_compatibles_entre_si():
    assert check_dpo_sod(Role.coordinador, [Role.implementador]) is None


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
