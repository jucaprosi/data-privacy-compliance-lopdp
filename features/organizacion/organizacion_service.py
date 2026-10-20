"""Compuerta pública de la sala ADPA: Organización (usuarios, áreas, roles, SoD y tamaños).

Única vía por la que otras salas y la API acceden a la organización.
Cada tarea posterior edita solo su sección reservada (# === <ID> === … # === fin <ID> ===).
"""
from __future__ import annotations

from features.organizacion.domain.models import (
    AreaCreate,
    AreaUpdate,
    RbacError,
    RoleGrant,
    SoDViolation,
    UserCreate,
)
from features.organizacion.domain.roles import (
    AREA_SCOPED_ROLES,
    DPO_INCOMPATIBLE_ROLES,
    Role,
)
from features.organizacion.domain.tamanos import TAMANOS_ORGANIZACION, TamanoOrganizacion
from features.organizacion.services.areas_engine import (
    allowed_area_ids,
    create_area,
    list_areas,
    update_area,
)
from features.organizacion.services.roles_engine import (
    grant_role,
    list_role_assignments,
    revoke_role,
)
from features.organizacion.services.sod_engine import check_dpo_sod, check_four_eyes
from features.organizacion.services.usuarios_engine import (
    create_or_get_user,
    has_active_role,
    list_my_roles,
    list_tenant_users,
)

__all__ = [
    "AREA_SCOPED_ROLES",
    "DPO_INCOMPATIBLE_ROLES",
    "TAMANOS_ORGANIZACION",
    "AreaCreate",
    "AreaUpdate",
    "RbacError",
    "Role",
    "RoleGrant",
    "SoDViolation",
    "TamanoOrganizacion",
    "UserCreate",
    "allowed_area_ids",
    "check_dpo_sod",
    "check_four_eyes",
    "create_area",
    "create_or_get_user",
    "grant_role",
    "has_active_role",
    "list_areas",
    "list_my_roles",
    "list_role_assignments",
    "list_tenant_users",
    "revoke_role",
    "update_area",
]

# === ORG-01 ===
from features.organizacion.domain.roles import INCOMPATIBILIDADES_ROLES

__all__ += [
    "INCOMPATIBILIDADES_ROLES",
]
# === fin ORG-01 ===

# === RM-10 ===
from features.organizacion.services.solicitud_responsable_engine import (
    ResponsableRequestCreate,
    ResponsableRequestDecision,
    ResponsableRequestPatch,
    approve_responsable_request,
    cancel_responsable_request,
    create_responsable_request,
    execute_responsable_request,
    get_responsable_request,
    list_responsable_requests,
    reject_responsable_request,
)

__all__ += [
    "ResponsableRequestCreate",
    "ResponsableRequestDecision",
    "ResponsableRequestPatch",
    "approve_responsable_request",
    "cancel_responsable_request",
    "create_responsable_request",
    "execute_responsable_request",
    "get_responsable_request",
    "list_responsable_requests",
    "reject_responsable_request",
]
# === fin RM-10 ===

# === RM-15 ===
from features.organizacion.services.configuracion_engine import (
    get_tenant_config,
    update_tenant_config,
)

__all__ += [
    "get_tenant_config",
    "update_tenant_config",
]
# === fin RM-15 ===

# === RM-16 ===
from features.organizacion.services.regla_tamano_engine import (
    evaluar_tamano,
    traducir_error_trigger,
    verificar_encargado_responsable,
)

__all__ += [
    "evaluar_tamano",
    "traducir_error_trigger",
    "verificar_encargado_responsable",
]
# === fin RM-16 ===
