"""Definiciones de seguridad, roles y Segregación de Funciones (SoD)."""
from enum import Enum
from dataclasses import dataclass
from typing import Set

class RolUsuario(str, Enum):
    ADMIN_PLATAFORMA = "ADMIN_PLATAFORMA"
    CONSULTOR_LIDER = "CONSULTOR_LIDER"
    RESPONSABLE_TRATAMIENTO = "RESPONSABLE_TRATAMIENTO"
    ENCARGADO_TRATAMIENTO = "ENCARGADO_TRATAMIENTO"
    DPD_DPO_INTERNO = "DPD_DPO_INTERNO"
    DPD_DPO_EXTERNO = "DPD_DPO_EXTERNO"
    AUDITOR = "AUDITOR"
    GESTOR_PROCESO = "GESTOR_PROCESO"

import asyncio
import os
from typing import Optional

import jwt
from fastapi import Header, HTTPException, status
from sqlalchemy import text

# ¤seguridad ¤rbac-tenant
# Autenticación de la API. Una sola verificación de identidad para todos los mecanismos:
#   - modo "oidc" (por defecto): el usuario sale SOLO del token de identidad de Google, verificado
#     (firma RS256, emisor, audiencia, vigencia y correo verificado). El tenant y el rol que declara
#     el cliente son solicitudes que se autorizan contra user_tenant_roles del usuario verificado.
#   - modo "headers": identidad declarada por cabeceras. Solo existe si se pide de forma explícita con
#     AUTH_MODE=headers (desarrollo, pruebas y el periodo previo a que el frontend inicie sesión).
MODO_OIDC = "oidc"
MODO_HEADERS = "headers"

# https://developers.google.com/identity/openid-connect/openid-connect (consultado 2026-10-17)
EMISORES_GOOGLE = ("https://accounts.google.com", "accounts.google.com")
URL_CLAVES_GOOGLE = "https://www.googleapis.com/oauth2/v3/certs"
VIGENCIA_CLAVES_SEGUNDOS = 3600

_cliente_claves: Optional[jwt.PyJWKClient] = None


def modo_autenticacion() -> str:
    """`headers` solo si AUTH_MODE lo dice exactamente; ausente, vacío o desconocido ⟹ `oidc`."""
    valor = os.environ.get("AUTH_MODE", "").strip().lower()
    return MODO_HEADERS if valor == MODO_HEADERS else MODO_OIDC


def _no_autenticado(detalle: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detalle,
        headers={"WWW-Authenticate": "Bearer"},
    )


def extraer_bearer(authorization: Optional[str]) -> str:
    """Devuelve el token de `Authorization: Bearer <token>` o responde 401."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _no_autenticado("Falta el token de identidad (Authorization: Bearer).")
    token = authorization[7:].strip()
    if not token:
        raise _no_autenticado("Falta el token de identidad (Authorization: Bearer).")
    return token


def _clave_de_firma(token: str):
    """Clave pública de Google que firmó el token. Las claves se cachean: no hay red en cada petición."""
    global _cliente_claves
    if _cliente_claves is None:
        _cliente_claves = jwt.PyJWKClient(
            URL_CLAVES_GOOGLE, cache_keys=True, lifespan=VIGENCIA_CLAVES_SEGUNDOS
        )
    return _cliente_claves.get_signing_key_from_jwt(token).key


@dataclass(frozen=True)
class IdentidadVerificada:
    sub: str
    email: str


@dataclass(frozen=True)
class UsuarioAutenticado:
    usuario_id: str
    email: str
    sub: str


async def verificar_token_google(token: str) -> IdentidadVerificada:
    """Verifica el token de identidad de Google. Todo fallo es 401; sin configuración, 503 (cierra)."""
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
    if not client_id:
        # Sin audiencia configurada no se puede verificar nada: se cierra, nunca se acepta.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La autenticación no está configurada en el servidor.",
        )
    try:
        clave = await asyncio.to_thread(_clave_de_firma, token)
        claims = jwt.decode(
            token,
            clave,
            algorithms=["RS256"],
            audience=client_id,
            issuer=list(EMISORES_GOOGLE),
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
    except jwt.PyJWKClientConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo verificar la identidad: servicio de claves no disponible.",
        )
    except jwt.PyJWTError:
        # Un único mensaje para firma, emisor, audiencia, caducidad y formato: no orienta a quien prueba.
        raise _no_autenticado("Token de identidad inválido o caducado.")
    if claims.get("email_verified") not in (True, "true"):
        raise _no_autenticado("El correo de la cuenta de Google no está verificado.")
    email = str(claims.get("email") or "").strip().lower()
    if not email:
        raise _no_autenticado("El token no incluye el correo de la cuenta.")
    return IdentidadVerificada(sub=str(claims["sub"]), email=email)


async def usuario_de_identidad(session, identidad: IdentidadVerificada) -> str:
    """Id del usuario de la plataforma al que corresponde la identidad verificada.

    Se busca por `google_sub`; si no hay, por correo verificado, y entonces se vincula. Una cuenta ya
    vinculada a otro `sub` no se reasigna. No se crean usuarios: quien no está registrado recibe 403.
    """
    fila = (await session.execute(
        text("SELECT id FROM users WHERE google_sub = :sub AND activo AND deleted_at IS NULL"),
        {"sub": identidad.sub},
    )).first()
    if fila:
        return fila[0]
    fila = (await session.execute(
        text("SELECT id, google_sub FROM users WHERE lower(email) = :email AND activo AND deleted_at IS NULL"),
        {"email": identidad.email},
    )).first()
    if fila is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuario no registrado en la plataforma.")
    if fila[1] and fila[1] != identidad.sub:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "La cuenta está vinculada a otra identidad de Google.")
    await session.execute(
        text("UPDATE users SET google_sub = :sub WHERE id = :id AND google_sub IS NULL"),
        {"sub": identidad.sub, "id": fila[0]},
    )
    return fila[0]


async def usuario_verificado(session, authorization: Optional[str]) -> UsuarioAutenticado:
    """Token ⟹ identidad verificada ⟹ usuario de la plataforma."""
    identidad = await verificar_token_google(extraer_bearer(authorization))
    usuario_id = await usuario_de_identidad(session, identidad)
    return UsuarioAutenticado(usuario_id=usuario_id, email=identidad.email, sub=identidad.sub)


async def roles_activos(session, tenant_id: str, usuario_id: str) -> set[str]:
    """Roles vigentes del usuario en el tenant (vacío si no es miembro)."""
    from app_core.db.session import fijar_contexto_rls  # session.py importa este módulo

    await fijar_contexto_rls(session, tenant_id, usuario_id)
    filas = (await session.execute(
        text(
            "SELECT role FROM user_tenant_roles "
            "WHERE user_id = :u AND tenant_id = :t AND (valid_to IS NULL OR valid_to > now())"
        ),
        {"u": usuario_id, "t": tenant_id},
    )).all()
    return {f[0] for f in filas}


async def autenticar_en_tenant(
    authorization: Optional[str], tenant_id: str
) -> tuple[UsuarioAutenticado, set[str]]:
    """Modo oidc fuera de un endpoint con sesión propia: usuario verificado y sus roles en el tenant.

    Sin ningún rol vigente en el tenant declarado responde 403.
    """
    from app_core.db.session import async_session_factory  # session.py importa este módulo

    async with async_session_factory() as session:
        usuario = await usuario_verificado(session, authorization)
        roles = await roles_activos(session, tenant_id, usuario.usuario_id)
        if not roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Sin membresía activa")
        await session.commit()
        return usuario, roles


PREFIJO_TOKEN_SIMULADO = "jwt_mock_tenant_"


def _tenant_de_token_simulado(authorization: Optional[str]) -> str:
    """Tenant del antiguo token simulado (solo modo `headers`); cadena vacía si no es de ese tipo."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return ""
    token = authorization[7:].strip()
    return token[len(PREFIJO_TOKEN_SIMULADO):] if token.startswith(PREFIJO_TOKEN_SIMULADO) else ""


async def get_current_tenant(
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
) -> str:
    """Tenant de la solicitud. En `oidc` exige token verificado y membresía; en `headers`, X-Tenant-ID."""
    tenant_id = (x_tenant_id or "").strip()
    if modo_autenticacion() == MODO_HEADERS:
        # Compatibilidad transitoria, solo en este modo explícito: ArcoModule, TercerosModule y
        # MitigationTracker del frontend envían `Bearer jwt_mock_tenant_<tenant>` y no X-Tenant-ID.
        # En `oidc` ese token no vale nada. Se retira cuando esos módulos usen la sesión de FE-07.
        if not tenant_id:
            tenant_id = _tenant_de_token_simulado(authorization)
        if not tenant_id:
            raise _no_autenticado("Falta el tenant (X-Tenant-ID) para resolver el contexto.")
        return tenant_id
    if not tenant_id:
        raise _no_autenticado("Falta el tenant (X-Tenant-ID) para resolver el contexto.")
    await autenticar_en_tenant(authorization, tenant_id)
    return tenant_id

class AccionOperativa(str, Enum):
    ASIGNAR_DUEÑO_CONTROL = "ASIGNAR_DUEÑO_CONTROL"
    EJECUTAR_REMEDIACION_CAPA = "EJECUTAR_REMEDIACION_CAPA"
    APROBAR_FINALIDAD_RAT = "APROBAR_FINALIDAD_RAT"
    APROBAR_POLITICA_PRIVACIDAD = "APROBAR_POLITICA_PRIVACIDAD"
    EMITIR_DICTAMEN_DPO = "EMITIR_DICTAMEN_DPO"
    SUPERVISAR_AUDITORIA = "SUPERVISAR_AUDITORIA"

# Conjunto de acciones prohibidas para el rol DPD/DPO según Art. 48 LOPDP e invariante INV_LOPDP_DPO_INDEPENDENCE
ACCIONES_INCOMPATIBLES_DPO: Set[AccionOperativa] = {
    AccionOperativa.ASIGNAR_DUEÑO_CONTROL,
    AccionOperativa.EJECUTAR_REMEDIACION_CAPA,
    AccionOperativa.APROBAR_FINALIDAD_RAT,
    AccionOperativa.APROBAR_POLITICA_PRIVACIDAD,
}

@dataclass
class UsuarioContexto:
    usuario_id: str
    tenant_id: str
    email: str
    rol: RolUsuario

def validar_permiso_sod(usuario: UsuarioContexto, accion: AccionOperativa) -> bool:
    """Valida que no se violen las reglas de independencia y Segregación de Funciones."""
    if usuario.rol in {RolUsuario.DPD_DPO_INTERNO, RolUsuario.DPD_DPO_EXTERNO}:
        if accion in ACCIONES_INCOMPATIBLES_DPO:
            return False
    return True
