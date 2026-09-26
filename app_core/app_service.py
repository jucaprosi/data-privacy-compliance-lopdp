# ¤¤app_infrastructure_service
"""Compuerta pública de servicios de infraestructura y seguridad transversal."""
from typing import Tuple
from app_core.config import config, AppConfig
from app_core.models import Tenant, BaseEntity
from app_core.security import RolUsuario, AccionOperativa, UsuarioContexto, validar_permiso_sod
from app_core.dlp_sanitizer import sanitizar_texto_dlp, sanitizar_texto_pii, validar_cedula_ecuatoriana
from app_core.models_base import TareaMitigacionORM

# ¤get-app-config
def get_app_config() -> AppConfig:
    return config

# ¤verificar-accion-sod
def verificar_accion_sod(usuario: UsuarioContexto, accion: AccionOperativa) -> bool:
    """Verifica si una acción es conforme con la Segregación de Funciones (SoD)."""
    return validar_permiso_sod(usuario, accion)

# ¤filtrar-datos-sensibles-dlp
def filtrar_datos_sensibles_dlp(contenido: str) -> Tuple[str, int]:
    """Aplica sanitización DLP a cualquier contenido antes de ser procesado o almacenado."""
    return sanitizar_texto_dlp(contenido)

