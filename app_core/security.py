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

from fastapi import Request, HTTPException, status
import json

async def get_current_tenant(request: Request) -> str:
    """
    Extrae el tenant_id del token JWT simulado en el header Authorization.
    Lanza 401 si no hay token válido.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header Authorization faltante o inválido para resolución de tenant_id"
        )
    
    token = auth_header.split(" ")[1]
    
    # Mock JWT para desarrollo/pruebas.
    # Simulamos que el token lleva como prefijo "jwt_mock_tenant_" y el resto es el UUID.
    prefix = "jwt_mock_tenant_"
    if not token.startswith(prefix):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o malformado"
        )
        
    tenant_id = token[len(prefix):]
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no contiene tenant_id"
        )
        
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
