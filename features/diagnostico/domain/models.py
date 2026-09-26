"""Modelos de dominio del Módulo 1: Diagnóstico de la Empresa."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

class EstadoConformidad(str, Enum):
    CONFORME = "CONFORME"
    PARCIAL = "PARCIAL"
    NO_CONFORME = "NO_CONFORME"
    NO_VERIFICADO = "NO_VERIFICADO"
    NO_APLICABLE = "NO_APLICABLE"

class NivelEvidencia(str, Enum):
    E0_SIN_EVIDENCIA = "E0_SIN_EVIDENCIA"
    E1_DOCUMENTADA = "E1_DOCUMENTADA"
    E2_IMPLEMENTADA = "E2_IMPLEMENTADA"
    E3_PROBADA = "E3_PROBADA"

@dataclass
class FichaOrganizacion:
    tenant_id: str
    sector: str
    tamano: str
    emplea_nube: bool = True
    trata_datos_salud: bool = False
    emplea_ia: bool = False
    videovigilancia: bool = False
    transferencias_internacionales: bool = False

@dataclass
class PreguntaDiagnostico:
    id_pregunta: str
    dominio_id: str # G01 a G16
    enunciado: str
    referencia_normativa: str
    es_nucleo: bool = True
    condicion_activacion: Optional[str] = None
    evidencia_esperada: str = ""

@dataclass
class RespuestaDiagnostico:
    id_pregunta: str
    respuesta_afirmativa: bool
    nivel_evidencia: NivelEvidencia = NivelEvidencia.E0_SIN_EVIDENCIA
    pendiente_validacion: bool = False
    rationale: str = ""

@dataclass
class ScoringDiagnostico:
    madurez_spdp: float # 0.0 a 3.0
    madurez_nivel_etiqueta: str # Caótico, Implícito, Temprano explícito, Maduro explícito
    porcentaje_conformidad_juridica: float
    cobertura_evidencia_porcentaje: float
    brechas_criticas_abiertas: int
    preguntas_respondidas_total: int
    duracion_minutos_estimada: int

class EstadoCumplimiento(str, Enum):
    """Estado declarado por el evaluador para un control del assessment."""
    CONFORME = "Conforme"
    PARCIAL = "Parcial"
    NO_CONFORME = "No Conforme"
    PENDIENTE = "Pendiente"

class SeveridadBrecha(str, Enum):
    CRITICO = "Crítico"
    ALTO = "Alto"
    MEDIO = "Medio"

@dataclass(frozen=True)
class DimensionSGPDP:
    """Dimensión ponderada del SGPDP que agrupa uno o varios dominios G01-G16."""
    id: str # D01 a D10
    nombre: str
    peso: float # La suma de los 10 pesos es exactamente 1.00
    dominios_origen: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class NivelMadurez:
    """Escalón 1-5 de la matriz de madurez del SGPDP."""
    nivel: int
    etiqueta: str
    descripcion: str
    umbral_minimo: float

@dataclass(frozen=True)
class ControlEstructural:
    """Control habilitador cuyo deterioro degrada el nivel de madurez global."""
    pregunta_id: int
    nombre: str
    dimension_id: str
    accion_prioritaria: str

@dataclass
class RespuestaControl:
    """Respuesta a un control de la matriz de assessment (entrada del agregador)."""
    pregunta_id: int
    cumple: EstadoCumplimiento = EstadoCumplimiento.PENDIENTE
    evidencia_nivel: int = 0 # 0 (E0) a 3 (E3)
    criticidad: int = 3 # 1 a 5
    es_critica: bool = False
    dimension_id: Optional[str] = None # D01 a D10
    dominio_id: Optional[str] = None # G01 a G16 (se resuelve a dimensión si falta dimension_id)
    control: str = ""
    pendiente_validacion: bool = False

@dataclass
class BrechaDetectada:
    pregunta_id: int
    control: str
    dimension_id: str
    dimension_nombre: str
    severidad: SeveridadBrecha
    nivel_efectivo: float
    riesgo: float
    es_estructural: bool

@dataclass
class ResultadoDimension:
    """Resultado agregado de una dimensión ponderada del SGPDP."""
    id: str
    nombre: str
    peso: float
    items_aplicables: int
    items_evaluados: int
    cobertura_porcentaje: float
    score: float # 0 a 100
    nivel: int # 0 (sin datos) o 1 a 5
    nivel_etiqueta: str
    brechas_criticas: int
    brechas_altas: int
    observacion: str

@dataclass
class ResultadoAssessment:
    """Resultado global ponderado sobre las 10 dimensiones del SGPDP."""
    score_ponderado: float # 0 a 100
    nivel_teorico: int
    nivel_teorico_etiqueta: str
    nivel_ajustado: int
    nivel_ajustado_etiqueta: str
    ajuste_por_brecha_estructural: bool
    dimensiones: List[ResultadoDimension] = field(default_factory=list)
    brechas: List[BrechaDetectada] = field(default_factory=list)
    brechas_criticas: int = 0
    brechas_altas: int = 0
    controles_estructurales_degradados: int = 0
    total_evaluados: int = 0
    total_aplicables: int = 0
    cobertura_porcentaje: float = 0.0
    # El nivel quedó topado en 3 por controles de alta criticidad sin evidencia
    # suficiente, aunque el score ponderado diera para más.
    ajuste_por_evidencia_insuficiente: bool = False
    # La cobertura no alcanza el mínimo de emisión: el resultado no califica.
    cobertura_insuficiente: bool = False
    # Controles bloqueantes (criticidad 5) con nivel efectivo por debajo de 3.
    controles_bloqueantes_degradados: int = 0
    # Controles de criticidad alta cuya evidencia no llega al mínimo exigible.
    controles_sin_evidencia_suficiente: int = 0
