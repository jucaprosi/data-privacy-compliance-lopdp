"""Modelos de dominio del Módulo 1: Diagnóstico de la Empresa."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Mapping, Optional

class EstadoConformidad(str, Enum):
    CONFORME = "CONFORME"
    PARCIAL = "PARCIAL"
    NO_CONFORME = "NO_CONFORME"
    NO_VERIFICADO = "NO_VERIFICADO"
    NO_APLICABLE = "NO_APLICABLE"

class NivelEvidencia(str, Enum):
    """Nivel de evidencia 0 a 4 de la escala SMARTCIDI (DIAG-08)."""
    E0_VERBAL = "E0_VERBAL"
    E1_INFORMAL = "E1_INFORMAL"
    E2_DOCUMENTAL = "E2_DOCUMENTAL"
    E3_OPERATIVA = "E3_OPERATIVA"
    E4_REVISADA = "E4_REVISADA"

    @property
    def nivel(self) -> int:
        return int(self.value[1])

# === DIAG-08 ===
# Escala SMARTCIDI (hojas «Niveles de Madurez» y «Catálogos» del archivo de assessment).
NIVELES_ASIGNADOS: dict[int, tuple[str, str]] = {
    1: ("Inicial / Reactivo", "No existe o se gestiona informalmente"),
    2: ("Básico / Repetible", "Prácticas aisladas o documentos iniciales"),
    3: ("Definido / Documentado", "Políticas, matrices, procedimientos y responsables definidos"),
    4: ("Gestionado / Demostrable", "Se aplica, se revisa, tiene seguimiento y métricas"),
    5: ("Optimizado / Mejora continua", "Integrado a gobierno, riesgos y seguridad, con mejora demostrable"),
}

NIVELES_EVIDENCIA: dict[int, str] = {
    0: "Verbal: sin evidencia",
    1: "Informal: correo, captura, práctica no formalizada",
    2: "Documental: política, matriz, procedimiento, contrato",
    3: "Operativa: registros de aplicación",
    4: "Revisada: auditada o revisada por la dirección",
}

NIVEL_ASIGNADO_MIN, NIVEL_ASIGNADO_MAX = 1, 5
NIVEL_EVIDENCIA_MIN, NIVEL_EVIDENCIA_MAX = 0, 4
ESCALA_SELLADA = "smartcidi_1_5"
ESCALA_ANTERIOR = "anterior"
# === fin DIAG-08 ===

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
    dominio_id: str # Dimensión D01 a D10
    enunciado: str
    referencia_normativa: str
    es_nucleo: bool = True
    condicion_activacion: Optional[str] = None
    evidencia_esperada: str = ""
    control: str = ""
    criticidad: int = 3
    tamano_minimo: str = "micro"
    es_estructural: bool = False
    ejemplo: str = ""

@dataclass
class RespuestaDiagnostico:
    id_pregunta: str
    respuesta_afirmativa: bool
    nivel_evidencia: NivelEvidencia = NivelEvidencia.E0_VERBAL
    pendiente_validacion: bool = False
    rationale: str = ""
    nivel_asignado: Optional[int] = None # 1 a 5; None = sin responder con la escala nueva

@dataclass
class ScoringDiagnostico:
    """Vectores ortogonales del diagnóstico; la madurez va por dimensión, sin cifra global."""
    porcentaje_conformidad_juridica: float
    cobertura_evidencia_porcentaje: float
    brechas_criticas_abiertas: int
    preguntas_respondidas_total: int
    duracion_minutos_estimada: int
    por_dimension: List["ResultadoDimension"] = field(default_factory=list)

class EstadoCumplimiento(str, Enum):
    """Estado declarado por el evaluador para un control del assessment."""
    CONFORME = "Conforme"
    PARCIAL = "Parcial"
    NO_CONFORME = "No Conforme"
    PENDIENTE = "Pendiente"


# === DIAG-08 ===
def estado_desde_nivel_asignado(nivel_asignado: Optional[int]) -> EstadoCumplimiento:
    """R3: el estado lo deriva el servidor del nivel asignado; nunca es una entrada."""
    if nivel_asignado is None:
        return EstadoCumplimiento.PENDIENTE
    if nivel_asignado <= 1:
        return EstadoCumplimiento.NO_CONFORME
    if nivel_asignado <= 3:
        return EstadoCumplimiento.PARCIAL
    return EstadoCumplimiento.CONFORME
# === fin DIAG-08 ===

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
    """Control habilitador cuyo deterioro topa el nivel de su dimensión."""
    pregunta_id: int
    nombre: str
    dimension_id: str
    accion_prioritaria: str

@dataclass
class RespuestaControl:
    """Respuesta a un control de la matriz de assessment (entrada del agregador)."""
    pregunta_id: int
    cumple: EstadoCumplimiento = EstadoCumplimiento.PENDIENTE # derivado; el motor no lo lee
    evidencia_nivel: int = 0 # 0 (verbal) a 4 (revisada)
    nivel_asignado: Optional[int] = None # 1 a 5; None computa como pendiente (R6)
    criticidad: int = 3 # 1 a 5
    es_critica: bool = False
    dimension_id: Optional[str] = None # D01 a D10
    dominio_id: Optional[str] = None # G01 a G16 (se resuelve a dimensión si falta dimension_id)
    control: str = ""
    pendiente_validacion: bool = False


# Estado de un resultado sellado antes de la escala SMARTCIDI -> nivel asignado. Solo se aplica al
# leerlo; no reescribe el sellado ni vale para las respuestas vivas, donde NULL sigue siendo pendiente.
_NIVEL_ASIGNADO_ANTERIOR = {"No Conforme": 1, "Parcial": 3, "Conforme": 5}


def _campo(fila: Any, nombre: str, defecto: Any = None) -> Any:
    valor = fila.get(nombre, defecto) if isinstance(fila, Mapping) else getattr(fila, nombre, defecto)
    return defecto if valor is None else valor


def respuesta_control_desde_fila(
    fila: Any,
    *,
    evidencia_nivel: Optional[int] = None,
    criticidad: Optional[int] = None,
    dimension_id: Optional[str] = None,
    control: Optional[str] = None,
    anterior: bool = False,
) -> RespuestaControl:
    """Única conversión de una fila (guardada o sellada) a la entrada del motor.

    El estado `cumple` se deriva siempre del nivel asignado (R3); ninguna sala lo mapea por su cuenta.
    Los parámetros sustituyen al campo de la fila cuando la fuente autoritativa es otra (p. ej. el banco).
    Con `anterior=True` la fila viene de un resultado sellado antes de la escala: sin `nivel_asignado`, se
    deriva del estado (No Conforme = 1, Parcial = 3, Conforme = 5) y la evidencia 1 a 3 pasa a 2 a 4, la
    misma correspondencia de la migración.
    """
    asignado = _campo(fila, "nivel_asignado")
    if asignado is None and anterior:
        asignado = _NIVEL_ASIGNADO_ANTERIOR.get(str(_campo(fila, "estado", "")))
    if evidencia_nivel is None:
        sellado = _campo(fila, "nivel_sellado")
        evidencia_nivel = int(sellado if sellado is not None else _campo(fila, "nivel_evidencia", 0))
        if anterior and evidencia_nivel > 0:
            evidencia_nivel = min(evidencia_nivel + 1, NIVEL_EVIDENCIA_MAX)
    asignado = int(asignado) if asignado is not None else None
    return RespuestaControl(
        pregunta_id=int(_campo(fila, "pregunta_id")),
        cumple=estado_desde_nivel_asignado(asignado),
        evidencia_nivel=int(evidencia_nivel),
        nivel_asignado=asignado,
        criticidad=int(criticidad if criticidad is not None else _campo(fila, "criticidad", 3)),
        es_critica=bool(_campo(fila, "es_critica", False)),
        dimension_id=dimension_id if dimension_id is not None else _campo(fila, "dimension"),
        control=control if control is not None else str(_campo(fila, "control", "")),
    )


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
    # Topes de nivel aplicados dentro de la dimensión (R4).
    ajuste_por_brecha_estructural: bool = False
    ajuste_por_evidencia_insuficiente: bool = False

@dataclass
class ResultadoAssessment:
    """Resultado del assessment por dimensión; no combina dimensiones en cifra alguna (R5)."""
    dimensiones: List[ResultadoDimension] = field(default_factory=list)
    brechas: List[BrechaDetectada] = field(default_factory=list)
    brechas_criticas: int = 0
    brechas_altas: int = 0
    controles_estructurales_degradados: int = 0
    total_evaluados: int = 0
    total_aplicables: int = 0
    cobertura_porcentaje: float = 0.0
    # Controles bloqueantes (criticidad 5) con nivel efectivo por debajo de 3.
    controles_bloqueantes_degradados: int = 0
    # Controles de criticidad alta cuya evidencia no llega al mínimo exigible.
    controles_sin_evidencia_suficiente: int = 0
