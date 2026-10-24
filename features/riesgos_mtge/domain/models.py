"""Tipos del motor MTGE según la Res. SPDP-SPD-2026-0005-R."""
from dataclasses import dataclass
from enum import Enum

class Titulares12Meses(str, Enum):
    HASTA_1000 = "HASTA_1000"; HASTA_10000 = "HASTA_10000"; HASTA_100000 = "HASTA_100000"; MAS_DE_100000 = "MAS_DE_100000"
class TiposDatos(str, Enum):
    HASTA_10 = "HASTA_10"; HASTA_30 = "HASTA_30"; HASTA_100 = "HASTA_100"; MAS_DE_100 = "MAS_DE_100"
class CategoriasDatos(str, Enum):
    BASICAS = "BASICAS"; UNA_ESPECIAL = "UNA_ESPECIAL"; MULTIPLES_ESPECIALES_O_VULNERABLES_O_PENALES = "MULTIPLES_ESPECIALES_O_VULNERABLES_O_PENALES"
class Frecuencia(str, Enum):
    PUNTUAL = "PUNTUAL"; PERIODICA_O_RECURRENTE = "PERIODICA_O_RECURRENTE"; CONTINUA_O_TIEMPO_REAL = "CONTINUA_O_TIEMPO_REAL"
class Permanencia(str, Enum):
    OCASIONAL = "OCASIONAL"; TEMPORAL_MENOS_DE_3_ANOS = "TEMPORAL_MENOS_DE_3_ANOS"; PROLONGADA_DESDE_3_ANOS = "PROLONGADA_DESDE_3_ANOS"
class AlcanceGeografico(str, Enum):
    LOCAL = "LOCAL"; NACIONAL = "NACIONAL"; GLOBAL_O_TRANSFRONTERIZO = "GLOBAL_O_TRANSFRONTERIZO"
class SupuestoDirecto(str, Enum):
    SALUD_O_CATEGORIAS_ESPECIALES = "14.1"; PERFILAMIENTO_AUTOMATIZADO_EFECTOS_JURIDICOS = "14.2"; VIDEOVIGILANCIA_SISTEMATICA_PUBLICA = "14.3"; BIOMETRICOS_O_GEOLOCALIZACION = "14.4"; CREDITO_SOLVENCIA_RIESGO_ECONOMICO = "14.5.a"; NINAS_NINOS_Y_ADOLESCENTES = "14.5.b"; TRANSFERENCIAS_SISTEMATICAS = "14.6"; MENSAJERIA_Y_COURIER = "14.7"

@dataclass(frozen=True)
class EntradaCalculoMTGE:
    actividad_rat_id: str; titulares_12_meses: Titulares12Meses; tipos_datos: TiposDatos; categorias_datos: CategoriasDatos; frecuencia: Frecuencia; permanencia: Permanencia; alcance: AlcanceGeografico; supuestos_directos: tuple[SupuestoDirecto, ...] = ()
@dataclass(frozen=True)
class ResultadoMTGE:
    actividad_rat_id: str; puntaje_mtge: float; es_gran_escala: bool; detona_dpo_obligatorio: bool; detona_eipd_obligatoria: bool; incluir_en_rat: bool; medidas_reforzadas: bool; criterio_activacion: str; desglose: dict[str, float]; supuestos_directos: tuple[str, ...]; rationale: str
