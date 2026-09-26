"""Motor de evaluación adaptativa y scoring multidimensional para Diagnóstico en 60 min."""
from typing import List, Tuple
from features.diagnostico.domain.models import (
    FichaOrganizacion,
    PreguntaDiagnostico,
    RespuestaDiagnostico,
    ScoringDiagnostico,
    NivelEvidencia,
)

DOMINIOS_JUBYS = [
    ("G01", "Gobierno y responsabilidad proactiva"),
    ("G02", "Inventario de datos, procesos y RAT"),
    ("G03", "Licitud, bases de legitimación y transparencia"),
    ("G04", "Derechos de titulares"),
    ("G05", "Categorías especiales y menores"),
    ("G06", "Gestión de riesgos y EIPD"),
    ("G07", "Protección desde el diseño y por defecto"),
    ("G08", "Seguridad y resiliencia"),
    ("G09", "Encargados, terceros y contratos"),
    ("G10", "Transferencias nacionales e internacionales"),
    ("G11", "Conservación, bloqueo y eliminación"),
    ("G12", "Vulneraciones e incidentes"),
    ("G13", "DPD/DPO e independencia"),
    ("G14", "Auditoría y mejora continua"),
    ("G15", "IA y decisiones automatizadas"),
    ("G16", "Tratamientos a gran escala"),
]

def generar_banco_preguntas_diagnostico() -> List[PreguntaDiagnostico]:
    """Genera las 48 preguntas núcleo (3 por dominio) y hasta 12 condicionales críticas."""
    preguntas: List[PreguntaDiagnostico] = []
    # 48 preguntas núcleo (3 por cada uno de los 16 dominios)
    for dom_id, dom_nombre in DOMINIOS_JUBYS:
        for i in range(1, 4):
            preguntas.append(
                PreguntaDiagnostico(
                    id_pregunta=f"{dom_id}-P0{i}",
                    dominio_id=dom_id,
                    enunciado=f"Control núcleo {i} para {dom_nombre}",
                    referencia_normativa="LOPDP / RGLOPDP / Guías SPDP",
                    es_nucleo=True,
                    evidencia_esperada="Documento o registro operativo",
                )
            )

    # Preguntas condicionales críticas (ej. IA, Salud, Gran Escala)
    preguntas.append(
        PreguntaDiagnostico(
            id_pregunta="G15-COND-01",
            dominio_id="G15",
            enunciado="¿Se aplican evaluaciones de impacto EIPD específicas para sistemas de IA?",
            referencia_normativa="Resolución SPDP-SPD-2026-0009-R",
            es_nucleo=False,
            condicion_activacion="emplea_ia",
            evidencia_esperada="EIPD de algoritmo de IA",
        )
    )
    preguntas.append(
        PreguntaDiagnostico(
            id_pregunta="G16-COND-01",
            dominio_id="G16",
            enunciado="¿Se ha ejecutado el cálculo del umbral MTGE para gran escala?",
            referencia_normativa="Resolución SPDP-SPD-2026-0005-R",
            es_nucleo=False,
            condicion_activacion="trata_datos_salud",
            evidencia_esperada="Matriz MTGE calculada",
        )
    )
    return preguntas

def filtrar_preguntas_visibles(ficha: FichaOrganizacion) -> List[PreguntaDiagnostico]:
    """Aplica la poda lógica condicional. Invariante: Nunca supera 80 preguntas visibles."""
    todas = generar_banco_preguntas_diagnostico()
    visibles: List[PreguntaDiagnostico] = []

    for p in todas:
        if p.es_nucleo:
            visibles.append(p)
        else:
            # Evaluar condición
            if p.condicion_activacion == "emplea_ia" and ficha.emplea_ia:
                visibles.append(p)
            elif p.condicion_activacion == "trata_datos_salud" and ficha.trata_datos_salud:
                visibles.append(p)
            elif p.condicion_activacion == "transferencias" and ficha.transferencias_internacionales:
                visibles.append(p)

    # Invariante INV_LOPDP_60MIN_TIMEBOX_LIMIT
    if len(visibles) > 80:
        visibles = visibles[:80]

    return visibles

def calcular_scoring_multidimensional(respuestas: List[RespuestaDiagnostico]) -> ScoringDiagnostico:
    """Calcula los 4 vectores ortogonales del diagnóstico."""
    if not respuestas:
        return ScoringDiagnostico(
            madurez_spdp=0.0,
            madurez_nivel_etiqueta="0 · Caótico",
            porcentaje_conformidad_juridica=0.0,
            cobertura_evidencia_porcentaje=0.0,
            brechas_criticas_abiertas=0,
            preguntas_respondidas_total=0,
            duracion_minutos_estimada=0,
        )

    total_preguntas = len(respuestas)
    afirmativas = 0
    puntos_madurez = 0.0
    evidencias_validas = 0
    brechas_criticas = 0

    for r in respuestas:
        if r.respuesta_afirmativa:
            afirmativas += 1
            if r.nivel_evidencia == NivelEvidencia.E3_PROBADA:
                puntos_madurez += 3.0
                evidencias_validas += 1
            elif r.nivel_evidencia == NivelEvidencia.E2_IMPLEMENTADA:
                puntos_madurez += 2.0
                evidencias_validas += 1
            elif r.nivel_evidencia == NivelEvidencia.E1_DOCUMENTADA:
                puntos_madurez += 1.0
                evidencias_validas += 1
            else:
                # E0 sin evidencia no puede otorgar nivel de madurez alto
                puntos_madurez += 0.5
        else:
            brechas_criticas += 1

    madurez_promedio = round(puntos_madurez / total_preguntas, 2)
    if madurez_promedio < 0.75:
        etiqueta = "0 · Caótico"
    elif madurez_promedio < 1.5:
        etiqueta = "1 · Implícito"
    elif madurez_promedio < 2.25:
        etiqueta = "2 · Temprano explícito"
    else:
        etiqueta = "3 · Maduro explícito"

    conformidad_pct = round((afirmativas / total_preguntas) * 100.0, 1)
    cobertura_evidencia_pct = round((evidencias_validas / total_preguntas) * 100.0, 1)

    return ScoringDiagnostico(
        madurez_spdp=madurez_promedio,
        madurez_nivel_etiqueta=etiqueta,
        porcentaje_conformidad_juridica=conformidad_pct,
        cobertura_evidencia_porcentaje=cobertura_evidencia_pct,
        brechas_criticas_abiertas=brechas_criticas,
        preguntas_respondidas_total=total_preguntas,
        duracion_minutos_estimada=min(60, int(total_preguntas * 0.8)),
    )
