"""Enrutador REST para la Sala ADPA: Riesgos y Motor MTGE Gran Escala."""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from features.riesgos_mtge.riesgos_mtge_service import evaluar_gran_escala_mtge
from features.riesgos_mtge.domain.models import EntradaCalculoMTGE, AlcanceGeografico

router = APIRouter(prefix="/riesgos", tags=["Riesgos y Motor MTGE Gran Escala"])

class EvaluarMTGERequest(BaseModel):
    actividad_rat_id: str = Field(..., description="ID de la actividad en el RAT")
    numero_titulares: int = Field(..., description="Volumen estimado de personas naturales afectadas")
    volumen_datos_por_titular: int = Field(..., description="Número de atributos o campos recabados")
    trata_datos_sensibles: bool = False
    frecuencia_permanente: bool = True
    alcance: AlcanceGeografico = AlcanceGeografico.NACIONAL
    es_caso_directo_salud_masiva: bool = False
    es_caso_directo_perfilamiento_ia: bool = False

@router.post("/mtge/evaluar")
def evaluar_mtge(payload: EvaluarMTGERequest):
    """Calcula el umbral paramétrico MTGE conforme a la Resolución SPDP-SPD-2026-0005-R."""
    entrada = EntradaCalculoMTGE(
        actividad_rat_id=payload.actividad_rat_id,
        numero_titulares=payload.numero_titulares,
        volumen_datos_por_titular=payload.volumen_datos_por_titular,
        trata_datos_sensibles=payload.trata_datos_sensibles,
        frecuencia_permanente=payload.frecuencia_permanente,
        alcance=payload.alcance,
        es_caso_directo_salud_masiva=payload.es_caso_directo_salud_masiva,
        es_caso_directo_perfilamiento_ia=payload.es_caso_directo_perfilamiento_ia,
    )
    resultado = evaluar_gran_escala_mtge(entrada)
    return {
        "actividad_rat_id": resultado.actividad_rat_id,
        "puntaje_mtge": resultado.puntaje_mtge,
        "es_gran_escala": resultado.es_gran_escala,
        "detona_dpo_obligatorio": resultado.detona_dpo_obligatorio,
        "detona_eipd_obligatoria": resultado.detona_eipd_obligatoria,
        "criterio_activacion": resultado.criterio_activacion,
        "rationale": resultado.rationale,
    }
