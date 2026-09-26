from features.diagnostico.services.reporte_service import exportar_pdf_diagnostico
"""Compuerta pública de la sala ADPA: Diagnóstico."""
from typing import List
from features.diagnostico.domain.models import (
    FichaOrganizacion,
    PreguntaDiagnostico,
    RespuestaDiagnostico,
    ScoringDiagnostico,
    EstadoConformidad,
    NivelEvidencia,
    EstadoCumplimiento,
    SeveridadBrecha,
    DimensionSGPDP,
    ControlEstructural,
    RespuestaControl,
    ResultadoDimension,
    ResultadoAssessment,
)
from features.diagnostico.services.engine import (
    filtrar_preguntas_visibles,
    calcular_scoring_multidimensional,
)
from features.diagnostico.services.dimensiones_sgpdp import (
    agregar_resultado_por_dimension,
    dimension_de_dominio,
    obtener_catalogo_dimensiones,
    obtener_controles_estructurales,
)
from features.diagnostico.services.report_generator import (
    generar_informe_markdown,
    generar_informe_html,
)

def obtener_preguntas_sesion_diagnostico(ficha: FichaOrganizacion) -> List[PreguntaDiagnostico]:
    """Retorna la lista podada de preguntas para la sesión de 60 minutos (Máximo 80)."""
    return filtrar_preguntas_visibles(ficha)

def evaluar_resultados_diagnostico(respuestas: List[RespuestaDiagnostico]) -> ScoringDiagnostico:
    """Calcula el scoring multidimensional sin dilución de brechas."""
    return calcular_scoring_multidimensional(respuestas)

def generar_informe_diagnostico_markdown(
    ficha: FichaOrganizacion,
    scoring: ScoringDiagnostico,
    respuestas: List[RespuestaDiagnostico],
) -> str:
    """Genera informe técnico-ejecutivo post-diagnóstico en formato Markdown."""
    return generar_informe_markdown(ficha, scoring, respuestas)

def generar_informe_diagnostico_html(
    ficha: FichaOrganizacion,
    scoring: ScoringDiagnostico,
    respuestas: List[RespuestaDiagnostico],
) -> str:
    """Genera informe corporativo post-diagnóstico en formato HTML corporativo listo para impresión/PDF."""
    return generar_informe_html(ficha, scoring, respuestas)


def generar_pdf_diagnostico_oficial(tenant_id: str, id_diagnostico: str) -> bytes:
    """Genera el PDF WORM inmutable con snapshot normativo (ADPA)."""
    return exportar_pdf_diagnostico(tenant_id, id_diagnostico)


def obtener_dimensiones_sgpdp() -> List[DimensionSGPDP]:
    """Retorna el catálogo de las 10 dimensiones ponderadas del SGPDP."""
    return obtener_catalogo_dimensiones()


def obtener_controles_estructurales_sgpdp() -> List[ControlEstructural]:
    """Retorna los controles habilitadores que topan el nivel de madurez global."""
    return obtener_controles_estructurales()


def resolver_dimension_de_dominio(dominio_id: str) -> str:
    """Traduce un dominio JUBYS (G01-G16) a su dimensión ponderada (D01-D10)."""
    return dimension_de_dominio(dominio_id)


def evaluar_assessment_por_dimension(respuestas: List[RespuestaControl]) -> ResultadoAssessment:
    """Agrega el assessment en las 10 dimensiones ponderadas con degradación estructural."""
    return agregar_resultado_por_dimension(respuestas)
