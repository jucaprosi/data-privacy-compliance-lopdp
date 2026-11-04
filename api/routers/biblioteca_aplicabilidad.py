# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Router de aplicabilidad determinista y plantillas recomendadas (BIB-204).

La organización sale siempre de la sesión (X-Tenant-ID / context), no del cuerpo.
Expone API para consultar qué plantillas aplican y registrar correcciones humanas explicables.
"""
from typing import Annotated, Any, Literal
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import get_context, require_role
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as biblioteca
from features.organizacion import organizacion_service
from features.rat import rat_service
from features.riesgos_mtge import riesgos_mtge_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca", tags=["Biblioteca aplicabilidad"])
Sesion = Annotated[AsyncSession, Depends(get_session)]

ROLES_LECTURA = ("admin_organizacion", "dpo", "coordinador", "implementador", "responsable_area")
ROLES_MODIFICACION = ("admin_organizacion", "dpo", "coordinador", "implementador")

_FUENTES = biblioteca.FuentesAplicabilidad(
    obtener_organizacion=organizacion_service.obtener_datos_documentales,
    listar_actividades=rat_service.listar_actividades_rat,
    obtener_gran_escala=riesgos_mtge_service.organizacion_tiene_gran_escala,
)


# ¤adpa
class ReglaEvaluadaResponse(BaseModel):
    regla_id: str
    nombre: str
    resultado: str
    explicacion: str
    fuente_normativa: str
    version_regla: str
    hechos_analizados: dict[str, Any]
    hechos_faltantes: list[str]


# ¤adpa
class ModificacionHumanaResponse(BaseModel):
    resultado_original: str
    resultado_modificado: str
    motivo: str
    evidencia: str
    autor_id: str
    fecha: str
    es_obligacion_confirmada: bool
    revisor_juridico_id: str | None = None


# ¤adpa
class EvaluacionPlantillaResponse(BaseModel):
    codigo: str
    nombre: str
    resultado: str
    resultado_calculado: str
    tipo: str
    familia: str
    formato: str
    naturaleza: str
    es_obligacion: bool
    fuentes_normativas: list[str]
    version_regla: str
    motivo_recomendacion: str
    hechos_relevantes: dict[str, Any]
    hechos_faltantes: list[str]
    reglas_evaluadas: list[ReglaEvaluadaResponse]
    modificacion_humana: ModificacionHumanaResponse | None = None


# ¤adpa
class ModificacionEntrada(BaseModel):
    resultado_modificado: Literal["Aplica", "No aplica"]
    motivo: str = Field(min_length=3)
    evidencia: str = Field(min_length=1)
    revisor_juridico_id: str | None = None


def _a_response(ev: biblioteca.EvaluacionPlantilla) -> EvaluacionPlantillaResponse:
    mod_resp = None
    if ev.modificacion_humana:
        mod_resp = ModificacionHumanaResponse(
            resultado_original=ev.modificacion_humana.resultado_original.value,
            resultado_modificado=ev.modificacion_humana.resultado_modificado.value,
            motivo=ev.modificacion_humana.motivo,
            evidencia=ev.modificacion_humana.evidencia,
            autor_id=ev.modificacion_humana.autor_id,
            fecha=ev.modificacion_humana.fecha.isoformat(),
            es_obligacion_confirmada=ev.modificacion_humana.es_obligacion_confirmada,
            revisor_juridico_id=ev.modificacion_humana.revisor_juridico_id,
        )
    return EvaluacionPlantillaResponse(
        codigo=ev.codigo,
        nombre=ev.nombre,
        resultado=ev.resultado.value,
        resultado_calculado=ev.resultado_calculado.value,
        tipo=ev.tipo,
        familia=ev.familia,
        formato=ev.formato,
        naturaleza=ev.naturaleza,
        es_obligacion=ev.es_obligacion,
        fuentes_normativas=ev.fuentes_normativas,
        version_regla=ev.version_regla,
        motivo_recomendacion=ev.motivo_recomendacion,
        hechos_relevantes=ev.hechos_relevantes,
        hechos_faltantes=ev.hechos_faltantes,
        reglas_evaluadas=[
            ReglaEvaluadaResponse(
                regla_id=r.regla_id,
                nombre=r.nombre,
                resultado=r.resultado.value,
                explicacion=r.explicacion,
                fuente_normativa=r.fuente_normativa,
                version_regla=r.version_regla,
                hechos_analizados=r.hechos_analizados,
                hechos_faltantes=r.hechos_faltantes,
            ) for r in ev.reglas_evaluadas
        ],
        modificacion_humana=mod_resp,
    )


# ¤adpa
@router.get("/aplicabilidad", response_model=list[EvaluacionPlantillaResponse])
async def obtener_aplicabilidad(
    session: Sesion,
    ctx: dict = Depends(require_role(*ROLES_LECTURA)),
    resultado: Annotated[str | None, Query()] = None,
):
    """Consulta la aplicabilidad de todas las plantillas para la organización activa."""
    evaluaciones = await biblioteca.evaluar_aplicabilidad_organizacion(session, ctx["tenant_id"], fuentes=_FUENTES)
    if resultado:
        evaluaciones = [e for e in evaluaciones if e.resultado.value.lower() == resultado.lower()]
    return [_a_response(e) for e in evaluaciones]


# ¤adpa
@router.get("/recomendados", response_model=list[EvaluacionPlantillaResponse])
async def obtener_recomendados(
    session: Sesion,
    ctx: dict = Depends(require_role(*ROLES_LECTURA)),
):
    """Retorna exclusivamente las plantillas recomendadas (cuyo resultado es 'Aplica')."""
    evaluaciones = await biblioteca.evaluar_aplicabilidad_organizacion(session, ctx["tenant_id"], fuentes=_FUENTES)
    recomendadas = [e for e in evaluaciones if e.resultado == biblioteca.ResultadoAplicabilidad.APLICA]
    return [_a_response(e) for e in recomendadas]


# ¤adpa
@router.post("/aplicabilidad/{codigo}/modificar", response_model=ModificacionHumanaResponse, status_code=status.HTTP_200_OK)
async def modificar_aplicabilidad(
    codigo: str,
    entrada: ModificacionEntrada,
    session: Sesion,
    ctx: dict = Depends(require_role(*ROLES_MODIFICACION)),
):
    """Registra una corrección humana con motivo y evidencia (exige rol o revisión jurídica para obligaciones)."""
    es_juridico = (ctx["role"] == "dpo") or (entrada.revisor_juridico_id is not None)
    res_mod = biblioteca.ResultadoAplicabilidad(entrada.resultado_modificado)
    mod = await biblioteca.registrar_modificacion_aplicabilidad(
        session=session,
        tenant_id=ctx["tenant_id"],
        actor_id=ctx["user_id"],
        plantilla_codigo=codigo,
        resultado_modificado=res_mod,
        motivo=entrada.motivo,
        evidencia=entrada.evidencia,
        es_juridico=es_juridico,
        revisor_juridico_id=entrada.revisor_juridico_id,
        fuentes=_FUENTES,
    )
    return ModificacionHumanaResponse(
        resultado_original=mod.resultado_original.value,
        resultado_modificado=mod.resultado_modificado.value,
        motivo=mod.motivo,
        evidencia=mod.evidencia,
        autor_id=mod.autor_id,
        fecha=mod.fecha.isoformat(),
        es_obligacion_confirmada=mod.es_obligacion_confirmada,
        revisor_juridico_id=mod.revisor_juridico_id,
    )
