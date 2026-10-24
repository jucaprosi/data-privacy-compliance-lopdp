"""Enrutador REST para la Sala ADPA: Riesgos y Motor MTGE Gran Escala."""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from features.riesgos_mtge.riesgos_mtge_service import evaluar_gran_escala_mtge
from features.riesgos_mtge.domain.models import EntradaCalculoMTGE, Titulares12Meses, TiposDatos, CategoriasDatos, Frecuencia, Permanencia, AlcanceGeografico, SupuestoDirecto

router = APIRouter(prefix="/riesgos", tags=["Riesgos y Motor MTGE Gran Escala"])

class EvaluarMTGERequest(BaseModel):
    actividad_rat_id: str = Field(..., description="ID de la actividad en el RAT")
    titulares_12_meses: Titulares12Meses
    tipos_datos: TiposDatos
    categorias_datos: CategoriasDatos
    frecuencia: Frecuencia
    permanencia: Permanencia
    alcance: AlcanceGeografico
    supuestos_directos: list[SupuestoDirecto] = Field(default_factory=list)

@router.post("/mtge/evaluar")
def evaluar_mtge(payload: EvaluarMTGERequest):
    """Calcula el umbral paramétrico MTGE conforme a la Resolución SPDP-SPD-2026-0005-R."""
    entrada = EntradaCalculoMTGE(
        actividad_rat_id=payload.actividad_rat_id,
        titulares_12_meses=payload.titulares_12_meses,
        tipos_datos=payload.tipos_datos,
        categorias_datos=payload.categorias_datos,
        frecuencia=payload.frecuencia,
        permanencia=payload.permanencia,
        alcance=payload.alcance,
        supuestos_directos=tuple(payload.supuestos_directos),
    )
    resultado = evaluar_gran_escala_mtge(entrada)
    return {
        "actividad_rat_id": resultado.actividad_rat_id,
        "puntaje_mtge": resultado.puntaje_mtge,
        "es_gran_escala": resultado.es_gran_escala,
        "detona_dpo_obligatorio": resultado.detona_dpo_obligatorio,
        "detona_eipd_obligatoria": resultado.detona_eipd_obligatoria,
        "incluir_en_rat": resultado.incluir_en_rat,
        "medidas_reforzadas": resultado.medidas_reforzadas,
        "criterio_activacion": resultado.criterio_activacion,
        "desglose": resultado.desglose,
        "supuestos_directos": resultado.supuestos_directos,
        "rationale": resultado.rationale,
    }
