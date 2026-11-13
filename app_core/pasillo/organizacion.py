# ¤adpa
"""Capacidades de la sala Organización para otras salas."""
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession


async def areas_permitidas(session: AsyncSession, tenant_id: str, user_id: str) -> Optional[set[str]]:
    """Áreas al alcance del usuario; None significa alcance transversal a toda la organización."""
    from features.organizacion import organizacion_service

    return await organizacion_service.allowed_area_ids(session, tenant_id, user_id)


async def listar_areas(session: AsyncSession, tenant_id: str) -> list[dict]:
    from features.organizacion import organizacion_service

    return await organizacion_service.list_areas(session, tenant_id)


async def listar_usuarios(session: AsyncSession, tenant_id: str) -> list[dict]:
    from features.organizacion import organizacion_service

    return await organizacion_service.list_tenant_users(session, tenant_id)


async def listar_roles_de_usuario(session: AsyncSession, tenant_id: str, user_id: str) -> list[dict]:
    """Fija al usuario consultado en el contexto RLS; quien llama debe restablecer el suyo."""
    from features.organizacion import organizacion_service

    return await organizacion_service.list_my_roles(session, tenant_id, user_id)


async def configuracion_de_organizacion(session: AsyncSession, tenant_id: str) -> dict:
    from features.organizacion import organizacion_service

    return await organizacion_service.get_tenant_config(session, tenant_id)


async def informe_de_designaciones(session: AsyncSession, tenant_id: str) -> dict[str, Any]:
    from features.organizacion import organizacion_service

    return await organizacion_service.obtener_informe_estado_designaciones(session, tenant_id)


async def crear_o_recuperar_usuario(session: AsyncSession, email: str, nombre: str) -> dict:
    from features.organizacion import organizacion_service

    return await organizacion_service.create_or_get_user(
        session=session,
        payload=organizacion_service.UserCreate(email=email, nombre=nombre),
    )


async def conceder_rol(session: AsyncSession, tenant_id: str, concedido_por: str, user_id: str, rol: str) -> dict:
    from features.organizacion import organizacion_service

    return await organizacion_service.grant_role(
        session=session,
        tenant_id=tenant_id,
        granted_by=concedido_por,
        payload=organizacion_service.RoleGrant(user_id=user_id, role=rol),
    )


# --- INICIO ADPA-04 ---
def verificar_cuatro_ojos(subido_por, user_id: str):
    """Motivo de la violación de cuatro ojos, o None si quien valida no es quien subió."""
    from features.organizacion import organizacion_service

    return organizacion_service.check_four_eyes(subido_por, user_id)


def violacion_sod(motivo) -> Exception:
    """Instancia de la excepción SoDViolation de la sala, para que el manejador de la API la reconozca."""
    from features.organizacion import organizacion_service

    return organizacion_service.SoDViolation(motivo)


def error_rbac(codigo: int, mensaje: str) -> Exception:
    from features.organizacion import organizacion_service

    return organizacion_service.RbacError(codigo, mensaje)
# --- FIN ADPA-04 ---


# === ADPA-06 ===
# ¤adpa Sección reservada del andamiaje ADPA-06 en este pasillo.
# === fin ADPA-06 ===


# === DEMO-03a ===
# ¤demo Solo reexporta: la lógica vive en la compuerta organizacion_service.
async def clonar_desde_plantilla(session, origen: str, destino: str, mapa_ids: dict) -> dict:
    from features.organizacion import organizacion_service

    return await organizacion_service.clonar_desde_plantilla(session, origen, destino, mapa_ids)


async def sembrar_en_plantilla(session, plantilla_id: str, datos: dict) -> None:
    from features.organizacion import organizacion_service

    await organizacion_service.sembrar_en_plantilla(session, plantilla_id, datos)
# === fin DEMO-03a ===

# === DIAG-04 ===
# Sección reservada para DIAG-04.
# === fin DIAG-04 ===

# === ORG-17 ===
# Sección reservada para ORG-17.
# === fin ORG-17 ===

# === DIAG-07 ===
# Sección reservada para DIAG-07.
# === fin DIAG-07 ===

# === ORG-18 ===
# Sección reservada para ORG-18.
# === fin ORG-18 ===

# === REG-01 ===
# Sección reservada para REG-01.
# === fin REG-01 ===


# === CAPA-04 ===
# Sección reservada para CAPA-04.
# === fin CAPA-04 ===


# === FOR-01 ===
# Sección reservada para FOR-01.
# === fin FOR-01 ===


# === RAT-08 ===
# Sección reservada para RAT-08.
# === fin RAT-08 ===
