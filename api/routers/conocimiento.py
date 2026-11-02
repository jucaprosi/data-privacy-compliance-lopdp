# ¤adpa
# ¤regulation-code
"""Centro de conocimiento (REG-02): normativa del corpus y ayuda contextual con cita obligatoria."""
from fastapi import APIRouter, Depends

from api.dependencies import obtener_tenant_id_actual
from api.errores import ErrorNegocio
from features.regulacion_rag import regulacion_rag_service as regulacion

AUTO_REGISTRO = True

router = APIRouter(prefix="/conocimiento", tags=["Centro de conocimiento"])


@router.get("/normativa")
def normativa(fuente: str = "", q: str = "", _tenant_id: str = Depends(obtener_tenant_id_actual)):
    """Artículos del corpus versionado, filtrables por fuente y por texto."""
    return {"articulos": regulacion.listar_normativa(fuente=fuente, q=q)}


@router.get("/ayuda")
def ayuda(control_ref: str = "", articulo: str = "", _tenant_id: str = Depends(obtener_tenant_id_actual)):
    """Texto del corpus con su cita; sin fuente en el corpus no hay ayuda (R1)."""
    respuesta = regulacion.obtener_ayuda(control_ref=control_ref, articulo=articulo)
    if respuesta is None:
        raise ErrorNegocio("SIN_FUENTE", detail="Sin fuente en el corpus.", status_code=404)
    return respuesta
