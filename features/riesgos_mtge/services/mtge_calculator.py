"""Cálculo del Modelo Técnico de Gran Escala (MTGE), Res. SPDP-SPD-2026-0005-R.

Un tratamiento es de gran escala si cae en un supuesto del art. 14 (sin necesidad de calcular) o
si la suma de las seis variables del art. 8 llega al umbral del art. 10. El cálculo es por
tratamiento (arts. 3.8 y 7), nunca sumando toda la organización.
"""
from features.riesgos_mtge.domain.models import (
    AlcanceGeografico,
    CategoriasDatos,
    EntradaCalculoMTGE,
    Frecuencia,
    Permanencia,
    ResultadoMTGE,
)

UMBRAL_GRAN_ESCALA_PUNTOS = 6.0  # Art. 10: gran escala si P >= 6.


def puntos_titulares(titulares: int) -> float:
    """Art. 8.1. De 100.001 a 100.999 el texto no fija tramo: se asignan 4 puntos porque superan
    el tramo de 3 («hasta 100.000»); decisión aprobada por el propietario (MTGE-01)."""
    if titulares < 0:
        raise ValueError("El número de titulares no puede ser negativo")
    if titulares <= 1_000:
        return 1.0  # 8.1.1
    if titulares <= 10_000:
        return 2.0  # 8.1.2
    if titulares <= 100_000:
        return 3.0  # 8.1.3
    return 4.0  # 8.1.4 («desde 101.000») y el hueco 100.001-100.999


def puntos_tipos_datos(tipos: int) -> float:
    """Art. 8.2: tipos de datos por titular."""
    if tipos < 1:
        raise ValueError("Un tratamiento trata al menos un tipo de dato")
    if tipos <= 10:
        return 0.5  # 8.2.1
    if tipos <= 30:
        return 1.0  # 8.2.2
    if tipos <= 100:
        return 2.0  # 8.2.3
    return 3.0  # 8.2.4


PUNTOS_CATEGORIAS = {  # Art. 8.3
    CategoriasDatos.BASICAS: 0.5,
    CategoriasDatos.UNA_ESPECIAL: 2.0,
    CategoriasDatos.VARIAS_ESPECIALES_VULNERABLES_O_PENALES: 3.0,
}
PUNTOS_FRECUENCIA = {  # Art. 8.4
    Frecuencia.PUNTUAL: 0.5,
    Frecuencia.PERIODICA: 1.0,
    Frecuencia.CONTINUA: 2.0,
}
PUNTOS_PERMANENCIA = {  # Art. 8.5
    Permanencia.OCASIONAL: 0.5,
    Permanencia.TEMPORAL: 1.0,
    Permanencia.PROLONGADA: 2.0,
}
PUNTOS_ALCANCE = {  # Art. 8.6
    AlcanceGeografico.LOCAL: 1.0,
    AlcanceGeografico.NACIONAL: 2.0,
    AlcanceGeografico.GLOBAL_O_TRANSFRONTERIZO: 3.0,
}


def calcular_mtge_actividad(entrada: EntradaCalculoMTGE) -> ResultadoMTGE:
    desglose = {
        "titulares": puntos_titulares(entrada.titulares_12_meses),
        "volumen": puntos_tipos_datos(entrada.tipos_datos_por_titular),
        "categorias": PUNTOS_CATEGORIAS[entrada.categorias_datos],
        "frecuencia": PUNTOS_FRECUENCIA[entrada.frecuencia],
        "permanencia": PUNTOS_PERMANENCIA[entrada.permanencia],
        "geografia": PUNTOS_ALCANCE[entrada.alcance],
    }
    puntaje = sum(desglose.values())  # Art. 9
    supuestos = tuple(s.value for s in entrada.supuestos_directos)

    if supuestos:
        criterio = "CALIFICACION_DIRECTA_ART_14"
        motivo = f"Gran escala por calificación directa (art. 14: {', '.join(supuestos)})"
    elif puntaje >= UMBRAL_GRAN_ESCALA_PUNTOS:
        criterio = "PUNTAJE_ART_10"
        motivo = f"Gran escala: P = {puntaje:g} alcanza el umbral de {UMBRAL_GRAN_ESCALA_PUNTOS:g} (arts. 9 y 10)"
    else:
        criterio = "NO_ALCANZA_UMBRAL"
        motivo = f"No es gran escala: P = {puntaje:g} es menor que {UMBRAL_GRAN_ESCALA_PUNTOS:g} (art. 10)"
    es_gran_escala = criterio != "NO_ALCANZA_UMBRAL"
    if es_gran_escala:
        motivo += ". Efectos del art. 12: EIPD previa, DPO obligatorio, inclusión en el RAT y medidas reforzadas."

    return ResultadoMTGE(
        actividad_rat_id=entrada.actividad_rat_id,
        puntaje_mtge=puntaje,
        desglose=desglose,
        es_gran_escala=es_gran_escala,
        criterio_activacion=criterio,
        supuestos_directos=supuestos,
        detona_eipd_obligatoria=es_gran_escala,
        detona_dpo_obligatorio=es_gran_escala,
        incluir_en_rat=es_gran_escala,
        medidas_reforzadas=es_gran_escala,
        rationale=motivo,
    )
