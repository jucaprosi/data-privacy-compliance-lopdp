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
    # Ficha con todas las banderas de alta complejidad activas y tamaño corporativo
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
    assert len(preguntas) == 80, "Para corporativo deben ser las 80 preguntas del banco"

    # Ficha microempresa debe podar según tamanoMinimo (39 preguntas exigibles)
    ficha_micro = FichaOrganizacion(
        tenant_id="org-micro",
        sector="Comercio",
        tamano="Microempresa",
    )
    preguntas_micro = obtener_preguntas_sesion_diagnostico(ficha_micro)
    assert len(preguntas_micro) == 39, f"Para microempresa se esperaban 39 preguntas, obtenidas: {len(preguntas_micro)}"

def test_scoring_multidimensional_no_diluye_brechas():
    """El scoring separa conformidad, evidencia y brechas críticas; la madurez va por dimensión."""
    respuestas = [
        RespuestaDiagnostico(id_pregunta="1", respuesta_afirmativa=True, nivel_evidencia=NivelEvidencia.E2_DOCUMENTAL),
        RespuestaDiagnostico(id_pregunta="2", respuesta_afirmativa=True, nivel_evidencia=NivelEvidencia.E3_OPERATIVA),
        RespuestaDiagnostico(id_pregunta="3", respuesta_afirmativa=False, nivel_evidencia=NivelEvidencia.E0_VERBAL), # BRECHA CRITICA
    ]
    scoring = evaluar_resultados_diagnostico(respuestas)
    
    # 2 de 3 afirmativas = 66.7% conformidad
    assert scoring.porcentaje_conformidad_juridica == 66.7
    # 1 brecha crítica no enmascarada
    assert scoring.brechas_criticas_abiertas == 1
    # DIAG-08: sin madurez global 0-3; solo el nivel por dimensión.
    assert not hasattr(scoring, "madurez_spdp")
    assert not hasattr(scoring, "madurez_nivel_etiqueta")
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
        RespuestaDiagnostico(id_pregunta="1", respuesta_afirmativa=True, nivel_evidencia=NivelEvidencia.E3_OPERATIVA),
        RespuestaDiagnostico(id_pregunta="9", respuesta_afirmativa=False, nivel_evidencia=NivelEvidencia.E0_VERBAL, rationale="Falta inventario"),
    ]
    scoring = evaluar_resultados_diagnostico(respuestas)
    
    # Generar Markdown
    md_report = generar_informe_diagnostico_markdown(ficha, scoring, respuestas)
    assert "JUBYS Plataforma LOPDP 360 · Informe Ejecutivo de Diagnóstico" in md_report
    assert "empresa-demo-ec" in md_report
    assert "Brecha #1" in md_report
    assert "Inventario de tratamientos" in md_report
    assert "Falta inventario" in md_report
    assert "Plan de Acción Recomendado" in md_report
    
    # Generar HTML
    html_report = generar_informe_diagnostico_html(ficha, scoring, respuestas)
    assert "<!DOCTYPE html>" in html_report
    assert "empresa-demo-ec" in html_report
    assert "Brecha #1" in html_report
    assert "Inventario de tratamientos" in html_report
    assert "Madurez SPDP" in html_report
    assert "Sin cifra global de la organización" in html_report
    assert "/ 3.0" not in html_report and "/ 3.0" not in md_report

