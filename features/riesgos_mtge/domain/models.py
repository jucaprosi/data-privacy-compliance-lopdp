"""Tipos del Modelo Técnico de Gran Escala (MTGE), Res. SPDP-SPD-2026-0005-R.

Las seis variables del art. 7. Titulares y tipos de datos se reciben como cifras (el art. 8 las
define por tramos numéricos); el resto son categorías del art. 3 y del art. 8.
"""
from dataclasses import dataclass, field
from enum import Enum


class CategoriasDatos(str, Enum):
    """Art. 8.3."""
    BASICAS = "BASICAS"  # 8.3.1: solo datos que no son categorías especiales
    UNA_ESPECIAL = "UNA_ESPECIAL"  # 8.3.2: incluye una categoría especial
    VARIAS_ESPECIALES_VULNERABLES_O_PENALES = "VARIAS_ESPECIALES_VULNERABLES_O_PENALES"  # 8.3.3


class Frecuencia(str, Enum):
    """Arts. 3.7 y 8.4."""
    PUNTUAL = "PUNTUAL"
    PERIODICA = "PERIODICA"  # periódica o recurrente
    CONTINUA = "CONTINUA"  # continua o en tiempo real


class Permanencia(str, Enum):
    """Arts. 3.9-3.12 y 8.5."""
    OCASIONAL = "OCASIONAL"  # excepcional, puntual o esporádica
    TEMPORAL = "TEMPORAL"  # menos de 3 años
    PROLONGADA = "PROLONGADA"  # desde 3 años


class AlcanceGeografico(str, Enum):
    """Arts. 3.1-3.5 y 8.6."""
    LOCAL = "LOCAL"  # una provincia, cantón o ciudad
    NACIONAL = "NACIONAL"  # más de una provincia, cantón o ciudad
    GLOBAL_O_TRANSFRONTERIZO = "GLOBAL_O_TRANSFRONTERIZO"


class SupuestoDirecto(str, Enum):
    """Art. 14: calificación directa y obligatoria, sin aplicar el MTGE.

    El texto numera dos veces «14.5»; se distinguen como 14.5.a (crédito) y 14.5.b (menores),
    decisión aprobada por el propietario (governance/tareas/MTGE-01.md).
    """
    SALUD_O_CATEGORIAS_ESPECIALES = "14.1"
    PERFILAMIENTO_CON_EFECTOS_JURIDICOS = "14.2"
    VIDEOVIGILANCIA_EN_ACCESO_PUBLICO = "14.3"
    BIOMETRICOS_O_GEOLOCALIZACION = "14.4"
    CREDITO_SOLVENCIA_O_RIESGO_ECONOMICO = "14.5.a"
    NINAS_NINOS_Y_ADOLESCENTES = "14.5.b"
    TRANSFERENCIAS_SISTEMATICAS = "14.6"
    MENSAJERIA_O_COURIER = "14.7"


@dataclass(frozen=True)
class EntradaCalculoMTGE:
    actividad_rat_id: str
    titulares_12_meses: int  # art. 3.8: titulares únicos del tratamiento en 12 meses
    tipos_datos_por_titular: int  # art. 3.13 y 8.2
    categorias_datos: CategoriasDatos
    frecuencia: Frecuencia
    permanencia: Permanencia
    alcance: AlcanceGeografico
    supuestos_directos: tuple[SupuestoDirecto, ...] = ()


@dataclass(frozen=True)
class ResultadoMTGE:
    actividad_rat_id: str
    puntaje_mtge: float  # art. 9: suma de las seis variables (se informa también en los casos directos)
    desglose: dict[str, float]
    es_gran_escala: bool
    criterio_activacion: str  # CALIFICACION_DIRECTA_ART_14 | PUNTAJE_ART_10 | NO_ALCANZA_UMBRAL
    supuestos_directos: tuple[str, ...]
    # Art. 12: efectos vinculantes cuando el tratamiento es de gran escala.
    detona_eipd_obligatoria: bool  # 12.1
    detona_dpo_obligatorio: bool  # 12.2
    incluir_en_rat: bool  # 12.3
    medidas_reforzadas: bool  # 12.4
    rationale: str = field(default="")
