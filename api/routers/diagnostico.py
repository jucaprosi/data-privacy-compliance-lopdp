"""Enrutador REST para la Sala ADPA: Diagnóstico de la Empresa."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field

from api.dependencies import obtener_tenant_id_actual
from features.diagnostico.diagnostico_service import (
    obtener_preguntas_sesion_diagnostico,
    evaluar_resultados_diagnostico,
    generar_informe_diagnostico_markdown,
    generar_informe_diagnostico_html,
    evaluar_assessment_por_dimension,
    obtener_dimensiones_sgpdp,
)
from features.diagnostico.domain.models import (
    FichaOrganizacion,
    RespuestaDiagnostico,
    NivelEvidencia,
    EstadoCumplimiento,
    RespuestaControl,
)

router = APIRouter(prefix="/diagnostico", tags=["Diagnóstico de la Empresa"])

class FichaOrganizacionSchema(BaseModel):
    sector: str = Field(..., description="Sector económico de la empresa")
    tamano: str = Field(..., description="Tamaño de la organización")
    emplea_nube: bool = True
    trata_datos_salud: bool = False
    emplea_ia: bool = False
    videovigilancia: bool = False
    transferencias_internacionales: bool = False

class RespuestaItemSchema(BaseModel):
    id_pregunta: str
    respuesta_afirmativa: bool
    nivel_evidencia: NivelEvidencia = NivelEvidencia.E0_SIN_EVIDENCIA
    rationale: str = ""

class EvaluacionDiagnosticoRequest(BaseModel):
    respuestas: List[RespuestaItemSchema]

class InformeDiagnosticoRequest(BaseModel):
    ficha: FichaOrganizacionSchema
    respuestas: List[RespuestaItemSchema]

class RespuestaControlSchema(BaseModel):
    pregunta_id: int = Field(..., description="Identificador numérico del control del assessment")
    cumple: EstadoCumplimiento = Field(
        EstadoCumplimiento.PENDIENTE, description="Estado declarado del control"
    )
    evidencia_nivel: int = Field(0, ge=0, le=3, description="Nivel de evidencia E0 (0) a E3 (3)")
    criticidad: int = Field(3, ge=1, le=5, description="Criticidad del control (1 a 5)")
    es_critica: bool = Field(False, description="Marca el control como jurídicamente crítico")
    dimension_id: Optional[str] = Field(None, description="Dimensión SGPDP D01-D10")
    dominio_id: Optional[str] = Field(None, description="Dominio JUBYS G01-G16 si no se envía dimensión")
    control: str = Field("", description="Nombre del control evaluado")
    pendiente_validacion: bool = False

class AssessmentDimensionalRequest(BaseModel):
    respuestas: List[RespuestaControlSchema]

class DimensionSGPDPSchema(BaseModel):
    id: str
    nombre: str
    peso: float
    dominios_origen: List[str]

class ResultadoDimensionSchema(BaseModel):
    id: str
    nombre: str
    peso: float
    items_aplicables: int
    items_evaluados: int
    cobertura_porcentaje: float
    score: float
    nivel: int
    nivel_etiqueta: str
    brechas_criticas: int
    brechas_altas: int
    observacion: str

class BrechaDetectadaSchema(BaseModel):
    pregunta_id: int
    control: str
    dimension_id: str
    dimension_nombre: str
    severidad: str
    nivel_efectivo: float
    riesgo: float
    es_estructural: bool

class ResultadoAssessmentSchema(BaseModel):
    score_ponderado: float
    nivel_teorico: int
    nivel_teorico_etiqueta: str
    nivel_ajustado: int
    nivel_ajustado_etiqueta: str
    ajuste_por_brecha_estructural: bool
    brechas_criticas: int
    brechas_altas: int
    controles_estructurales_degradados: int
    total_evaluados: int
    total_aplicables: int
    cobertura_porcentaje: float

class AssessmentDimensionalResponse(BaseModel):
    tenant_id: str
    global_: ResultadoAssessmentSchema = Field(..., alias="global")
    dimensiones: List[ResultadoDimensionSchema]
    brechas: List[BrechaDetectadaSchema]

    model_config = {"populate_by_name": True}

class CatalogoDimensionesResponse(BaseModel):
    total_dimensiones: int
    dimensiones: List[DimensionSGPDPSchema]

@router.post("/preguntas")
def obtener_preguntas_diagnostico(
    ficha_input: FichaOrganizacionSchema,
    tenant_id: str = Depends(obtener_tenant_id_actual),
):
    """Retorna el banco podado de preguntas adaptado a la organización (máximo 80)."""
    ficha = FichaOrganizacion(
        tenant_id=tenant_id,
        sector=ficha_input.sector,
        tamano=ficha_input.tamano,
        emplea_nube=ficha_input.emplea_nube,
        trata_datos_salud=ficha_input.trata_datos_salud,
        emplea_ia=ficha_input.emplea_ia,
        videovigilancia=ficha_input.videovigilancia,
        transferencias_internacionales=ficha_input.transferencias_internacionales,
    )
    preguntas = obtener_preguntas_sesion_diagnostico(ficha)
    return {
        "tenant_id": tenant_id,
        "total_preguntas": len(preguntas),
        "preguntas": [
            {
                "id_pregunta": p.id_pregunta,
                "dominio_id": p.dominio_id,
                "enunciado": p.enunciado,
                "referencia_normativa": p.referencia_normativa,
                "es_nucleo": p.es_nucleo,
                "evidencia_esperada": p.evidencia_esperada,
            }
            for p in preguntas
        ],
    }

@router.post("/evaluar")
def evaluar_diagnostico(
    payload: EvaluacionDiagnosticoRequest,
    tenant_id: str = Depends(obtener_tenant_id_actual),
):
    """Calcula el scoring multidimensional sin dilución de brechas."""
    respuestas_dominio = [
        RespuestaDiagnostico(
            id_pregunta=r.id_pregunta,
            respuesta_afirmativa=r.respuesta_afirmativa,
            nivel_evidencia=r.nivel_evidencia,
            rationale=r.rationale,
        )
        for r in payload.respuestas
    ]
    scoring = evaluar_resultados_diagnostico(respuestas_dominio)
    return {
        "tenant_id": tenant_id,
        "scoring": {
            "madurez_spdp": scoring.madurez_spdp,
            "madurez_nivel_etiqueta": scoring.madurez_nivel_etiqueta,
            "porcentaje_conformidad_juridica": scoring.porcentaje_conformidad_juridica,
            "cobertura_evidencia_porcentaje": scoring.cobertura_evidencia_porcentaje,
            "brechas_criticas_abiertas": scoring.brechas_criticas_abiertas,
            "preguntas_respondidas_total": scoring.preguntas_respondidas_total,
            "duracion_minutos_estimada": scoring.duracion_minutos_estimada,
        },
    }

@router.post("/informe/markdown")
def obtener_informe_markdown(
    payload: InformeDiagnosticoRequest,
    tenant_id: str = Depends(obtener_tenant_id_actual),
):
    """Genera informe técnico-ejecutivo post-diagnóstico en formato Markdown."""
    ficha = FichaOrganizacion(
        tenant_id=tenant_id,
        sector=payload.ficha.sector,
        tamano=payload.ficha.tamano,
        emplea_nube=payload.ficha.emplea_nube,
        trata_datos_salud=payload.ficha.trata_datos_salud,
        emplea_ia=payload.ficha.emplea_ia,
        videovigilancia=payload.ficha.videovigilancia,
        transferencias_internacionales=payload.ficha.transferencias_internacionales,
    )
    respuestas_dominio = [
        RespuestaDiagnostico(
            id_pregunta=r.id_pregunta,
            respuesta_afirmativa=r.respuesta_afirmativa,
            nivel_evidencia=r.nivel_evidencia,
            rationale=r.rationale,
        )
        for r in payload.respuestas
    ]
    scoring = evaluar_resultados_diagnostico(respuestas_dominio)
    md = generar_informe_diagnostico_markdown(ficha, scoring, respuestas_dominio)
    return {"tenant_id": tenant_id, "informe_markdown": md}

@router.post("/informe/html")
def obtener_informe_html(
    payload: InformeDiagnosticoRequest,
    tenant_id: str = Depends(obtener_tenant_id_actual),
):
    """Genera informe corporativo post-diagnóstico en formato HTML corporativo."""
    ficha = FichaOrganizacion(
        tenant_id=tenant_id,
        sector=payload.ficha.sector,
        tamano=payload.ficha.tamano,
        emplea_nube=payload.ficha.emplea_nube,
        trata_datos_salud=payload.ficha.trata_datos_salud,
        emplea_ia=payload.ficha.emplea_ia,
        videovigilancia=payload.ficha.videovigilancia,
        transferencias_internacionales=payload.ficha.transferencias_internacionales,
    )
    respuestas_dominio = [
        RespuestaDiagnostico(
            id_pregunta=r.id_pregunta,
            respuesta_afirmativa=r.respuesta_afirmativa,
            nivel_evidencia=r.nivel_evidencia,
            rationale=r.rationale,
        )
        for r in payload.respuestas
    ]
    scoring = evaluar_resultados_diagnostico(respuestas_dominio)
    html = generar_informe_diagnostico_html(ficha, scoring, respuestas_dominio)
    return {"tenant_id": tenant_id, "informe_html": html}

@router.get("/dimensiones", response_model=CatalogoDimensionesResponse)
def obtener_catalogo_dimensiones_sgpdp():
    """Retorna el catálogo canónico de las 10 dimensiones ponderadas del SGPDP."""
    dimensiones = obtener_dimensiones_sgpdp()
    return CatalogoDimensionesResponse(
        total_dimensiones=len(dimensiones),
        dimensiones=[
            DimensionSGPDPSchema(
                id=d.id,
                nombre=d.nombre,
                peso=d.peso,
                dominios_origen=list(d.dominios_origen),
            )
            for d in dimensiones
        ],
    )

@router.post("/assessment/dimensiones", response_model=AssessmentDimensionalResponse)
def evaluar_assessment_dimensional(
    payload: AssessmentDimensionalRequest,
    tenant_id: str = Depends(obtener_tenant_id_actual),
):
    """Agrega el assessment en las 10 dimensiones ponderadas del SGPDP.

    Devuelve el resultado por dimensión y el resultado global con el nivel
    ajustado por degradación de controles estructurales habilitadores.
    """
    respuestas_dominio = [
        RespuestaControl(
            pregunta_id=r.pregunta_id,
            cumple=r.cumple,
            evidencia_nivel=r.evidencia_nivel,
            criticidad=r.criticidad,
            es_critica=r.es_critica,
            dimension_id=r.dimension_id,
            dominio_id=r.dominio_id,
            control=r.control,
            pendiente_validacion=r.pendiente_validacion,
        )
        for r in payload.respuestas
    ]
    resultado = evaluar_assessment_por_dimension(respuestas_dominio)
    return AssessmentDimensionalResponse(
        tenant_id=tenant_id,
        **{
            "global": ResultadoAssessmentSchema(
                score_ponderado=resultado.score_ponderado,
                nivel_teorico=resultado.nivel_teorico,
                nivel_teorico_etiqueta=resultado.nivel_teorico_etiqueta,
                nivel_ajustado=resultado.nivel_ajustado,
                nivel_ajustado_etiqueta=resultado.nivel_ajustado_etiqueta,
                ajuste_por_brecha_estructural=resultado.ajuste_por_brecha_estructural,
                brechas_criticas=resultado.brechas_criticas,
                brechas_altas=resultado.brechas_altas,
                controles_estructurales_degradados=resultado.controles_estructurales_degradados,
                total_evaluados=resultado.total_evaluados,
                total_aplicables=resultado.total_aplicables,
                cobertura_porcentaje=resultado.cobertura_porcentaje,
            )
        },
        dimensiones=[
            ResultadoDimensionSchema(
                id=d.id,
                nombre=d.nombre,
                peso=d.peso,
                items_aplicables=d.items_aplicables,
                items_evaluados=d.items_evaluados,
                cobertura_porcentaje=d.cobertura_porcentaje,
                score=d.score,
                nivel=d.nivel,
                nivel_etiqueta=d.nivel_etiqueta,
                brechas_criticas=d.brechas_criticas,
                brechas_altas=d.brechas_altas,
                observacion=d.observacion,
            )
            for d in resultado.dimensiones
        ],
        brechas=[
            BrechaDetectadaSchema(
                pregunta_id=b.pregunta_id,
                control=b.control,
                dimension_id=b.dimension_id,
                dimension_nombre=b.dimension_nombre,
                severidad=b.severidad.value,
                nivel_efectivo=b.nivel_efectivo,
                riesgo=b.riesgo,
                es_estructural=b.es_estructural,
            )
            for b in resultado.brechas
        ],
    )

@router.get("/{id}/exportar")
def exportar_informe_pdf(
    id: str,
    tenant_id: str = Depends(obtener_tenant_id_actual),
):
    """Retorna un PDF WORM con el informe de diagnóstico."""
    from features.diagnostico.diagnostico_service import generar_pdf_diagnostico_oficial
    pdf_bytes = generar_pdf_diagnostico_oficial(tenant_id, id)
    return Response(content=pdf_bytes, media_type="application/pdf")
