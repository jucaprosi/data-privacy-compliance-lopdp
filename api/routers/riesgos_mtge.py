"""Enrutador REST de la sala riesgos_mtge: cálculo de gran escala (Res. SPDP-SPD-2026-0005-R)."""
from dataclasses import asdict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from features.riesgos_mtge.riesgos_mtge_service import (
    AlcanceGeografico,
    CategoriasDatos,
    EntradaCalculoMTGE,
    Frecuencia,
    Permanencia,
    SupuestoDirecto,
    evaluar_gran_escala_mtge,
)

router = APIRouter(prefix="/riesgos", tags=["Riesgos y Motor MTGE Gran Escala"])


class EvaluarMTGERequest(BaseModel):
    """Las seis variables del art. 7, todas obligatorias: ningún valor por defecto decide el resultado."""
    actividad_rat_id: str = Field(..., min_length=1, description="Tratamiento evaluado (el cálculo es por tratamiento)")
    titulares_12_meses: int = Field(..., ge=0, description="Titulares únicos del tratamiento en 12 meses (art. 3.8)")
    tipos_datos_por_titular: int = Field(..., ge=1, description="Tipos de datos por titular (art. 8.2)")
    categorias_datos: CategoriasDatos
    frecuencia: Frecuencia
    permanencia: Permanencia
    alcance: AlcanceGeografico
    supuestos_directos: list[SupuestoDirecto] = Field(default_factory=list, description="Supuestos del art. 14")


@router.post("/mtge/evaluar")
def evaluar_mtge(payload: EvaluarMTGERequest):
    """Califica un tratamiento como de gran escala (arts. 8-10 y 14) y devuelve sus efectos (art. 12)."""
    entrada = EntradaCalculoMTGE(
        actividad_rat_id=payload.actividad_rat_id,
        titulares_12_meses=payload.titulares_12_meses,
        tipos_datos_por_titular=payload.tipos_datos_por_titular,
        categorias_datos=payload.categorias_datos,
        frecuencia=payload.frecuencia,
        permanencia=payload.permanencia,
        alcance=payload.alcance,
        supuestos_directos=tuple(dict.fromkeys(payload.supuestos_directos)),
    )
    return asdict(evaluar_gran_escala_mtge(entrada))
