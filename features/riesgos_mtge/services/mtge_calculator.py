"""Motor determinista de cálculo MTGE (Matriz de Tratamientos a Gran Escala).
Conforme a la Resolución SPDP-SPD-2026-0005-R e invariante INV_LOPDP_MTGE_DETERMINISTIC_TRIGGER.
"""
from features.riesgos_mtge.domain.models import EntradaCalculoMTGE, ResultadoMTGE, AlcanceGeografico

UMBRAL_GRAN_ESCALA_PUNTOS = 100.0

def calcular_mtge_actividad(entrada: EntradaCalculoMTGE) -> ResultadoMTGE:
    """Calcula si un tratamiento califica como Gran Escala por casos directos o por umbral MTGE."""
    # 1. Verificación de Casos Directos Normativos
    if entrada.es_caso_directo_salud_masiva:
        return ResultadoMTGE(
            actividad_rat_id=entrada.actividad_rat_id,
            puntaje_mtge=150.0,
            es_gran_escala=True,
            detona_dpo_obligatorio=True,
            detona_eipd_obligatoria=True,
            criterio_activacion="CASO_DIRECTO_SALUD",
            rationale="Calificación directa por tratamiento masivo de datos de salud (Res. SPDP-SPD-2026-0005-R, Art. 12).",
        )

    if entrada.es_caso_directo_perfilamiento_ia:
        return ResultadoMTGE(
            actividad_rat_id=entrada.actividad_rat_id,
            puntaje_mtge=140.0,
            es_gran_escala=True,
            detona_dpo_obligatorio=True,
            detona_eipd_obligatoria=True,
            criterio_activacion="CASO_DIRECTO_IA",
            rationale="Calificación directa por perfilamiento sistemático y automatizado a gran escala.",
        )

    # 2. Cálculo Paramétrico por Variables
    puntos = 0.0

    # Variable Titulares
    if entrada.numero_titulares > 50000:
        puntos += 50.0
    elif entrada.numero_titulares > 10000:
        puntos += 30.0
    elif entrada.numero_titulares > 1000:
        puntos += 15.0
    else:
        puntos += 5.0

    # Variable Sensibilidad
    if entrada.trata_datos_sensibles:
        puntos += 35.0

    # Variable Permanencia/Frecuencia
    if entrada.frecuencia_permanente:
        puntos += 20.0

    # Variable Alcance Geográfico
    if entrada.alcance in (AlcanceGeografico.NACIONAL, AlcanceGeografico.INTERNACIONAL):
        puntos += 25.0
    elif entrada.alcance == AlcanceGeografico.PROVINCIAL:
        puntos += 15.0
    else:
        puntos += 5.0

    es_ge = puntos >= UMBRAL_GRAN_ESCALA_PUNTOS
    criterio = "UMBRAL_PUNTAJE" if es_ge else "NO_ALCANZA"
    rationale = (
        f"Puntaje obtenido: {puntos} / {UMBRAL_GRAN_ESCALA_PUNTOS}. "
        + ("Supera el umbral de Gran Escala; activa DPD/DPO y EIPD obligatorios." if es_ge else "Tratamiento ordinario.")
    )

    return ResultadoMTGE(
        actividad_rat_id=entrada.actividad_rat_id,
        puntaje_mtge=puntos,
        es_gran_escala=es_ge,
        detona_dpo_obligatorio=es_ge,
        detona_eipd_obligatoria=es_ge,
        criterio_activacion=criterio,
        rationale=rationale,
    )
