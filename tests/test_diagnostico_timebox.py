"""Test de verificación de Diagnóstico en 60 min y Scoring Multidimensional.
Invariantes: INV_LOPDP_60MIN_TIMEBOX_LIMIT, INV_LOPDP_MULTIDIMENSIONAL_METRICS.
"""
from features.diagnostico.diagnostico_service import (
    obtener_preguntas_sesion_diagnostico,
    evaluar_resultados_diagnostico,
    generar_informe_diagnostico_markdown,
    generar_informe_diagnostico_html,
)
from features.diagnostico.domain.models import (
    FichaOrganizacion,
    RespuestaDiagnostico,
    NivelEvidencia,
)

def test_diagnostico_cota_superior_80_preguntas():
    """El diagnóstico adaptativo nunca supera la cota de 80 preguntas visibles."""
    # Ficha con todas las banderas de alta complejidad activas
    ficha_compleja = FichaOrganizacion(
        tenant_id="org-compleja",
        sector="Salud y Finanzas",
        tamano="Corporativo",
        emplea_nube=True,
        trata_datos_salud=True,
        emplea_ia=True,
        videovigilancia=True,
        transferencias_internacionales=True,
    )
    preguntas = obtener_preguntas_sesion_diagnostico(ficha_compleja)
    assert len(preguntas) <= 80, f"Se violó la cota de 80 preguntas visibles: {len(preguntas)}"
    assert len(preguntas) >= 48, "Debe contener al menos las 48 preguntas núcleo de los 16 dominios"

def test_scoring_multidimensional_no_diluye_brechas():
    """El scoring separa explícitamente madurez, conformidad y brechas críticas."""
    respuestas = [
        RespuestaDiagnostico(id_pregunta="G01-P01", respuesta_afirmativa=True, nivel_evidencia=NivelEvidencia.E2_IMPLEMENTADA),
        RespuestaDiagnostico(id_pregunta="G01-P02", respuesta_afirmativa=True, nivel_evidencia=NivelEvidencia.E3_PROBADA),
        RespuestaDiagnostico(id_pregunta="G01-P03", respuesta_afirmativa=False, nivel_evidencia=NivelEvidencia.E0_SIN_EVIDENCIA), # BRECHA CRITICA
    ]
    scoring = evaluar_resultados_diagnostico(respuestas)
    
    # 2 de 3 afirmativas = 66.7% conformidad
    assert scoring.porcentaje_conformidad_juridica == 66.7
    # 1 brecha crítica no enmascarada
    assert scoring.brechas_criticas_abiertas == 1
    # Madurez computable por nivel de evidencias: (2.0 + 3.0 + 0) / 3 = 1.67
    assert scoring.madurez_spdp == 1.67
    assert scoring.madurez_nivel_etiqueta == "2 · Temprano explícito"
    # Cobertura de evidencia: 2 de 3 con evidencia válida (E2, E3) = 66.7%
    assert scoring.cobertura_evidencia_porcentaje == 66.7
    assert scoring.preguntas_respondidas_total == 3
    assert scoring.duracion_minutos_estimada == 2


def test_generador_informes_diagnostico_markdown_y_html():
    """Valida la generación de informes ejecutivo y técnico sin dilución y con formatos correctos."""
    ficha = FichaOrganizacion(
        tenant_id="empresa-demo-ec",
        sector="Telecomunicaciones",
        tamano="Mediana",
    )
    respuestas = [
        RespuestaDiagnostico(id_pregunta="G01-P01", respuesta_afirmativa=True, nivel_evidencia=NivelEvidencia.E3_PROBADA),
        RespuestaDiagnostico(id_pregunta="G02-P01", respuesta_afirmativa=False, nivel_evidencia=NivelEvidencia.E0_SIN_EVIDENCIA, rationale="Falta inventario"),
    ]
    scoring = evaluar_resultados_diagnostico(respuestas)
    
    # Generar Markdown
    md_report = generar_informe_diagnostico_markdown(ficha, scoring, respuestas)
    assert "JUBYS Plataforma LOPDP 360 · Informe Ejecutivo de Diagnóstico" in md_report
    assert "empresa-demo-ec" in md_report
    assert "Brecha #1" in md_report
    assert "Falta inventario" in md_report
    assert "Plan de Acción Recomendado" in md_report
    
    # Generar HTML
    html_report = generar_informe_diagnostico_html(ficha, scoring, respuestas)
    assert "<!DOCTYPE html>" in html_report
    assert "empresa-demo-ec" in html_report
    assert "Brecha #1" in html_report
    assert "Madurez SPDP" in html_report

