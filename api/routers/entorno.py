# ¤entorno-pruebas
"""GET /entorno (EP-01): identidad pública del entorno, sin autenticación."""
from fastapi import APIRouter
from pydantic import BaseModel

from app_core.entorno import datos_ficticios, entorno_actual

AUTO_REGISTRO = True
PREFIJO = "/api/v1"

router = APIRouter(prefix="/entorno", tags=["Salud del Sistema"])


class IdentidadEntorno(BaseModel):
    entorno: str
    datos_ficticios: bool


@router.get("", response_model=IdentidadEntorno)
def obtener_entorno() -> IdentidadEntorno:
    entorno = entorno_actual()
    return IdentidadEntorno(entorno=entorno, datos_ficticios=datos_ficticios(entorno))
