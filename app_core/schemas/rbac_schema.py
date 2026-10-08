"""Contratos tipados para la administración de usuarios, áreas y roles por tenant."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app_core.schemas.roadmap_schema import Role

# Roles que pueden acotarse a un área. El resto es transversal al tenant.
AREA_SCOPED_ROLES = {Role.responsable_area}

# Art. 48 LOPDP: el DPO supervisa, no ejecuta.
DPO_INCOMPATIBLE_ROLES = {Role.implementador, Role.encargado}


class UserCreate(BaseModel):
    email: str = Field(max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    nombre: str = Field(min_length=1, max_length=255)


class AreaCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    codigo: Optional[str] = Field(default=None, max_length=50)
    parent_area_id: Optional[str] = None


class AreaUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=255)
    codigo: Optional[str] = Field(default=None, max_length=50)
    responsable_user_id: Optional[str] = None


class RoleGrant(BaseModel):
    user_id: str = Field(min_length=1)
    role: Role
    area_id: Optional[str] = None
    valid_to: Optional[datetime] = None

    @model_validator(mode="after")
    def area_solo_en_roles_acotables(self) -> "RoleGrant":
        if self.area_id and self.role not in AREA_SCOPED_ROLES:
            raise ValueError(f"El rol '{self.role.value}' es transversal al tenant y no admite area_id")
        return self
