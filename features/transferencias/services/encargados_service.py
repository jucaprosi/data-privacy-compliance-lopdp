from sqlalchemy import Column, String, Boolean, Enum, text
from sqlalchemy.dialects.postgresql import UUID
import enum
from app_core.db.base import Base

class RolTercero(str, enum.Enum):
    ENCARGADO = "ENCARGADO"
    SUBENCARGADO = "SUBENCARGADO"
    DESTINATARIO = "DESTINATARIO"

class NivelProteccion(str, enum.Enum):
    ADECUADO = "ADECUADO"
    ESTANDAR = "ESTANDAR"
    NO_ADECUADO = "NO_ADECUADO"

# ADPA-08: el modelo vive en la sala, en features/transferencias/models.py.
from features.transferencias.models import TerceroEncargado  # noqa: E402,F401
