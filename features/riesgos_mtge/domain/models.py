"""Modelos de dominio del Módulo 2B: Riesgos y Motor MTGE Gran Escala."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import uuid

def gen_id() -> str:
    return str(uuid.uuid4())

class AlcanceGeografico(str, Enum):
    LOCAL_CANTONAL = "LOCAL_CANTONAL"
    PROVINCIAL = "PROVINCIAL"
    NACIONAL = "NACIONAL"
    INTERNACIONAL = "INTERNACIONAL"

@dataclass
class EntradaCalculoMTGE:
    actividad_rat_id: str
    numero_titulares: int
    volumen_datos_por_titular: int # número de atributos o campos
    trata_datos_sensibles: bool
    frecuencia_permanente: bool
    alcance: AlcanceGeografico
    es_caso_directo_salud_masiva: bool = False
    es_caso_directo_perfilamiento_ia: bool = False

@dataclass
class ResultadoMTGE:
    actividad_rat_id: str
    puntaje_mtge: float
    es_gran_escala: bool
    detona_dpo_obligatorio: bool
    detona_eipd_obligatoria: bool
    criterio_activacion: str # UMBRAL_PUNTAJE, CASO_DIRECTO_SALUD, CASO_DIRECTO_IA, NO_ALCANZA
    rationale: str
