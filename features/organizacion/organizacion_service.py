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

# === ORG-06 ===
from features.organizacion.services.designacion_engine import (
    DeclaracionConflictosCreate,
    DesignacionCreate,
    InscripcionSpdpCreate,
    RevocacionCreate,
    TipoDesignacion,
    VinculoDesignacion,
    crear_designacion_formal,
    listar_designaciones_formales,
    obtener_designacion_formal,
    obtener_informe_estado_designaciones,
    registrar_declaracion_conflictos,
    registrar_inscripcion_spdp,
    revocar_designacion_formal,
)

__all__ += [
    "DeclaracionConflictosCreate",
    "DesignacionCreate",
    "InscripcionSpdpCreate",
    "RevocacionCreate",
    "TipoDesignacion",
    "VinculoDesignacion",
    "crear_designacion_formal",
    "listar_designaciones_formales",
    "obtener_designacion_formal",
    "obtener_informe_estado_designaciones",
    "registrar_declaracion_conflictos",
    "registrar_inscripcion_spdp",
    "revocar_designacion_formal",
]
# === fin ORG-06 ===

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
    verificar_excepcion_coordinador_responsable,
)

__all__ += [
    "evaluar_tamano",
    "traducir_error_trigger",
    "verificar_excepcion_coordinador_responsable",
]
# === fin RM-16 ===

# === ORG-07 ===
from features.organizacion.services.estructura_engine import (
    AreaEstructuraCreate,
    AreaEstructuraUpdate,
    CargoCreate,
    CargoTitularSet,
    CargoUpdate,
    NivelArea,
    TipoCargo,
    TIPOS_INCOMPATIBLES_CON_DPD,
    asignar_titular_cargo,
    cargos_incompatibles_con_dpd,
    crear_area_estructura,
    crear_cargo,
    editar_area_estructura,
    editar_cargo,
    obtener_arbol_estructura,
    obtener_informe_cobertura,
)

__all__ += [
    "AreaEstructuraCreate",
    "AreaEstructuraUpdate",
    "CargoCreate",
    "CargoTitularSet",
    "CargoUpdate",
    "NivelArea",
    "TipoCargo",
    "TIPOS_INCOMPATIBLES_CON_DPD",
    "asignar_titular_cargo",
    "cargos_incompatibles_con_dpd",
    "crear_area_estructura",
    "crear_cargo",
    "editar_area_estructura",
    "editar_cargo",
    "obtener_arbol_estructura",
    "obtener_informe_cobertura",
]
# === fin ORG-07 ===

# === ORG-02 ===
from features.organizacion.services.excepcion_sod_engine import (
    ControlCompensatorioTipo,
    EstadoExcepcionSoD,
    ExcepcionSoDAprobar,
    ExcepcionSoDCreate,
    ExcepcionSoDObservacionDpo,
    ExcepcionSoDRevocar,
    OrigenExcepcionSoD,
    agregar_observacion_dpo,
    aprobar_excepcion_sod,
    listar_excepciones_sod,
    obtener_excepcion_sod,
    revocar_excepcion_sod,
    solicitar_excepcion_sod,
)

__all__ += [
    "ControlCompensatorioTipo",
    "EstadoExcepcionSoD",
    "ExcepcionSoDAprobar",
    "ExcepcionSoDCreate",
    "ExcepcionSoDObservacionDpo",
    "ExcepcionSoDRevocar",
    "OrigenExcepcionSoD",
    "agregar_observacion_dpo",
    "aprobar_excepcion_sod",
    "listar_excepciones_sod",
    "obtener_excepcion_sod",
    "revocar_excepcion_sod",
    "solicitar_excepcion_sod",
]
# === fin ORG-02 ===

# === ORG-05 ===
from features.organizacion.services.roles_engine import (
    ROLES_OPERATIVOS,
    conceder_rol_directo,
    revocar_rol_directo,
)

__all__ += [
    "ROLES_OPERATIVOS",
    "conceder_rol_directo",
    "revocar_rol_directo",
]
# === fin ORG-05 ===

# === ORG-13 ===
from features.organizacion.services.roles_engine import (  # noqa: E402
    MENSAJE_ORGANIZACION_EXCLUSIVA,
    listar_mis_organizaciones,
)

__all__ += [
    "MENSAJE_ORGANIZACION_EXCLUSIVA",
    "listar_mis_organizaciones",
]
# === fin ORG-13 ===

# === ORG-14 ===
from features.organizacion.services.datos_documentales_engine import (
    CAMPOS_DOCUMENTALES,
    VARIABLES_DOCUMENTALES,
    DatosDocumentalesPatch,
    actualizar_datos_documentales,
    es_cedula_valida,
    es_identificacion_valida,
    normalizar_dato_documental,
    obtener_datos_documentales,
    obtener_variables_documentales,
)

__all__ += [
    "CAMPOS_DOCUMENTALES",
    "VARIABLES_DOCUMENTALES",
    "DatosDocumentalesPatch",
    "actualizar_datos_documentales",
    "es_cedula_valida",
    "es_identificacion_valida",
    "normalizar_dato_documental",
    "obtener_datos_documentales",
    "obtener_variables_documentales",
]
# === fin ORG-14 ===

# === ORG-16 ===
from features.organizacion.services.alta_engine import (
    PASOS as PASOS_ALTA,
    SUGERENCIAS_POR_SECTOR as SUGERENCIAS_ALTA_POR_SECTOR,
    PasoPerfil as PasoPerfilAlta,
    PasoPersonas as PasoPersonasAlta,
    _clave_sector as clave_sector_alta,
    guardar_paso as guardar_paso_alta,
    obtener_estado_alta,
    obtener_sugerencias as obtener_sugerencias_alta,
)

__all__ += [
    "PASOS_ALTA",
    "SUGERENCIAS_ALTA_POR_SECTOR",
    "PasoPerfilAlta",
    "PasoPersonasAlta",
    "clave_sector_alta",
    "guardar_paso_alta",
    "obtener_estado_alta",
    "obtener_sugerencias_alta",
]
# === fin ORG-16 ===

# === DEMO-03a ===
# ¤demo Copia de la sala al tenant de una demo y siembra de la plantilla (PRD EVYDENTIA §5.6.8).
from features.organizacion.services.clon_plantilla_engine import (  # noqa: E402
    clonar_desde_plantilla,
    sembrar_en_plantilla,
)

__all__ += [
    "clonar_desde_plantilla",
    "sembrar_en_plantilla",
]
# === fin DEMO-03a ===


# === ADPA-05 ===
# ¤adpa Los códigos de error de esta sala viven en features/organizacion/domain/errores.py y se registran al importarlo.
from features.organizacion.domain import errores as _errores_sala  # noqa: E402,F401
# === fin ADPA-05 ===

# === ORG-17 ===
# ¤inventario Activos, soportes y personas mínimas de la organización (ORG-17).
from features.organizacion.services.inventario_engine import (  # noqa: E402
    ActivoCrear,
    ActivoEditar,
    PersonaCrear,
    PersonaEditar,
    VinculosTratamientos,
    crear_activo,
    crear_persona,
    editar_activo,
    editar_persona,
    listar_activos,
    listar_personas,
    reemplazar_vinculos_tratamientos,
    tratamientos_disponibles,
)

__all__ += [
    "ActivoCrear",
    "ActivoEditar",
    "PersonaCrear",
    "PersonaEditar",
    "VinculosTratamientos",
    "crear_activo",
    "crear_persona",
    "editar_activo",
    "editar_persona",
    "listar_activos",
    "listar_personas",
    "reemplazar_vinculos_tratamientos",
    "tratamientos_disponibles",
]
# === fin ORG-17 ===

# === ORG-18 ===
# ¤inventario Sedes y clientes por encargo de la organización (ORG-18).
from features.organizacion.services.sedes_engine import (  # noqa: E402
    ClienteEntrada,
    SedeEntrada,
    crear_cliente,
    crear_sede,
    editar_cliente,
    editar_sede,
    listar_clientes,
    listar_sedes,
    retirar_cliente,
    retirar_sede,
)

__all__ += [
    "ClienteEntrada",
    "SedeEntrada",
    "crear_cliente",
    "crear_sede",
    "editar_cliente",
    "editar_sede",
    "listar_clientes",
    "listar_sedes",
    "retirar_cliente",
    "retirar_sede",
]
# === fin ORG-18 ===

# === ORG-15 ===
from features.organizacion.services.cartera_engine import armar_cartera  # noqa: E402

__all__ += ["armar_cartera"]
# === fin ORG-15 ===

# === ORG-24 ===
from features.organizacion.services.ficha_engine import armar_ficha  # noqa: E402

__all__ += ["armar_ficha"]
# === fin ORG-24 ===
