"""Catálogo canónico de las 10 dimensiones ponderadas del SGPDP y su agregación.

Escala SMARTCIDI (DIAG-08): nivel asignado 1 a 5 y nivel de evidencia 0 a 4 por control.
    nivel efectivo  = MIN(nivel asignado, nivel evidencia sellado + 1)
    riesgo          = (5 - nivel efectivo) * criticidad del control
    score dimensión = SUMA((nivel efectivo / 5) * criticidad) / SUMA(criticidad) * 100
    nivel dimensión = rangos 0-39 → 1, 40-59 → 2, 60-74 → 3, 75-89 → 4, 90-100 → 5

El resultado es por dimensión: ninguna cifra combina dimensiones en un puntaje, nivel o
porcentaje de la organización (INV_LOPDP_MULTIDIMENSIONAL_METRICS). El score de dimensión
se pondera por criticidad y su denominador abarca todos los controles aplicables: un control
sin responder (nivel asignado nulo) computa como cero, no se excluye.

Regla estructural: los controles habilitadores (inventario de tratamientos, RAT,
clasificación de datos sensibles y verificación de identidad) sostienen la
demostrabilidad del resto de su dimensión. Si alguno queda por debajo del umbral, el
nivel de esa dimensión se degrada con tope en Nivel 2 aunque su score sea alto.
"""
from typing import Dict, List, Optional

from features.diagnostico.domain.models import (
    BrechaDetectada,
    ControlEstructural,
    DimensionSGPDP,
    NIVELES_ASIGNADOS,
    NivelMadurez,
    RespuestaControl,
    ResultadoAssessment,
    ResultadoDimension,
    SeveridadBrecha,
)

# Las 10 dimensiones ponderadas. La suma de pesos es exactamente 1.00.
DIMENSIONES_SGPDP: List[DimensionSGPDP] = [
    DimensionSGPDP("D01", "Gobierno y responsabilidad proactiva", 0.12, ["G01", "G13"]),
    DimensionSGPDP("D02", "Inventario, RAT, finalidades y legitimación", 0.14, ["G02", "G03"]),
    DimensionSGPDP("D03", "Transparencia e información al titular", 0.08, ["G03"]),
    DimensionSGPDP("D04", "Derechos de titulares", 0.08, ["G04"]),
    DimensionSGPDP("D05", "Procesos críticos y ciclo de vida de datos", 0.10, ["G05", "G11"]),
    DimensionSGPDP("D06", "Encargados, proveedores y transferencias", 0.10, ["G09", "G10"]),
    DimensionSGPDP("D07", "Seguridad de datos personales", 0.14, ["G08"]),
    DimensionSGPDP("D08", "Incidentes y vulneraciones", 0.08, ["G12"]),
    DimensionSGPDP("D09", "Riesgos, EIPD, LIA y privacidad desde el diseño", 0.11, ["G06", "G07", "G15", "G16"]),
    DimensionSGPDP("D10", "Capacitación, cultura, auditoría y mejora continua", 0.05, ["G14"]),
]

DIMENSION_POR_ID: Dict[str, DimensionSGPDP] = {d.id: d for d in DIMENSIONES_SGPDP}

DIMENSION_POR_DEFECTO = "D01"

# Controles estructurales habilitadores del SGPDP.
CONTROLES_ESTRUCTURALES: List[ControlEstructural] = [
    ControlEstructural(
        pregunta_id=9,
        nombre="Inventario de tratamientos",
        dimension_id="D02",
        accion_prioritaria="Levantar o actualizar el inventario de tratamientos con dueños por proceso.",
    ),
    ControlEstructural(
        pregunta_id=10,
        nombre="Registro de Actividades de Tratamiento (RAT)",
        dimension_id="D02",
        accion_prioritaria="Construir o actualizar el RAT sobre procesos reales con evidencia de validación.",
    ),
    ControlEstructural(
        pregunta_id=13,
        nombre="Datos sensibles y de mayor riesgo",
        dimension_id="D02",
        accion_prioritaria="Clasificar datos sensibles y definir controles reforzados por tratamiento.",
    ),
    ControlEstructural(
        pregunta_id=28,
        nombre="Verificación de identidad",
        dimension_id="D04",
        accion_prioritaria="Definir criterios de verificación de identidad y representación.",
    ),
]

PREGUNTAS_ESTRUCTURALES = frozenset(c.pregunta_id for c in CONTROLES_ESTRUCTURALES)

# Escala 1-5 de la matriz de assessment; el umbral es el piso del score de la dimensión.
_UMBRALES_NIVEL = {1: 0.0, 2: 40.0, 3: 60.0, 4: 75.0, 5: 90.0}
NIVELES_MADUREZ: List[NivelMadurez] = [
    NivelMadurez(nivel, nombre, criterio, _UMBRALES_NIVEL[nivel])
    for nivel, (nombre, criterio) in NIVELES_ASIGNADOS.items()
]

NIVELES_MADUREZ_INDEX: Dict[int, NivelMadurez] = {n.nivel: n for n in NIVELES_MADUREZ}

# Cota superior del nivel de una dimensión con al menos un control estructural degradado.
NIVEL_TOPE_BRECHA_ESTRUCTURAL = 2

# Nivel efectivo por debajo del cual un control estructural se considera degradado.
UMBRAL_DEGRADACION_ESTRUCTURAL = 3.0

ETIQUETA_SIN_DATOS = "Sin evaluación suficiente"

UMBRAL_RIESGO_CRITICO = 15.0
UMBRAL_RIESGO_ALTO = 9.0

# Un control de criticidad máxima es bloqueante: su nivel efectivo bajo topa el
# nivel de su dimensión igual que un control estructural. Los cuatro estructurales del
# catálogo son un subconjunto de este criterio, no una lista aparte.
CRITICIDAD_BLOQUEANTE = 5

# Criticidad a partir de la cual la falta de evidencia pesa por sí sola, y cota
# de nivel que impone: un control de alta criticidad sostenido solo en la
# declaración no permite acreditar procesos gestionados.
CRITICIDAD_EVIDENCIA_EXIGIBLE = 4
UMBRAL_EVIDENCIA_EXIGIBLE = 2  # evidencia documental
NIVEL_TOPE_EVIDENCIA_INSUFICIENTE = 3

# Cobertura mínima para que el resultado sea emitible. Por debajo de este
# porcentaje el assessment no califica: informa nivel 0, no un nivel bajo.
COBERTURA_MINIMA_EMISION = 60.0


def _redondear(valor: float, decimales: int = 1) -> float:
    """Redondeo half-up determinista (evita el sesgo bancario de round())."""
    factor = 10 ** decimales
    escalado = valor * factor
    entero = int(escalado)
    resto = escalado - entero
    if resto >= 0.5:
        entero += 1
    elif resto <= -0.5:
        entero -= 1
    return entero / factor


def obtener_catalogo_dimensiones() -> List[DimensionSGPDP]:
    """Retorna las 10 dimensiones ponderadas del SGPDP."""
    return list(DIMENSIONES_SGPDP)


def obtener_controles_estructurales() -> List[ControlEstructural]:
    """Retorna los controles habilitadores que degradan el nivel global."""
    return list(CONTROLES_ESTRUCTURALES)


def dimension_de_dominio(dominio_id: str) -> str:
    """Resuelve la dimensión a la que pertenece un dominio JUBYS (G01-G16).

    Un dominio sin mapeo explícito se imputa a Gobierno para no perder el
    control del cómputo ponderado.
    """
    dominio = (dominio_id or "").strip().upper()
    for dim in DIMENSIONES_SGPDP:
        if dominio in dim.dominios_origen:
            return dim.id
    return DIMENSION_POR_DEFECTO


def _resolver_dimension(respuesta: RespuestaControl) -> str:
    if respuesta.dimension_id:
        candidata = respuesta.dimension_id.strip().upper()
        if candidata in DIMENSION_POR_ID:
            return candidata
    if respuesta.dominio_id:
        return dimension_de_dominio(respuesta.dominio_id)
    return DIMENSION_POR_DEFECTO


def nivel_desde_score(score_porcentual: float) -> NivelMadurez:
    """Traduce un score porcentual (0-100) al nivel de madurez que le corresponde."""
    resultado = NIVELES_MADUREZ[0]
    for nivel in NIVELES_MADUREZ:
        if score_porcentual >= nivel.umbral_minimo:
            resultado = nivel
    return resultado


def evidencia_acotada(respuesta: RespuestaControl) -> int:
    """Nivel de evidencia 0-4 tal cual, sin reescalar."""
    return max(0, min(4, int(respuesta.evidencia_nivel or 0)))


def calcular_nivel_efectivo(respuesta: RespuestaControl) -> float:
    """R1: nivel efectivo = MIN(nivel asignado, nivel de evidencia + 1).

    Sin evidencia no hay madurez alta: la evidencia acota el nivel alcanzable con
    independencia de lo que se declare. Un nivel asignado nulo computa como cero (R6).
    """
    asignado = respuesta.nivel_asignado
    if asignado is None:
        return 0.0
    return float(min(max(1, min(5, int(asignado))), evidencia_acotada(respuesta) + 1))


def _criticidad_efectiva(respuesta: RespuestaControl) -> int:
    if respuesta.criticidad:
        return max(1, min(5, int(respuesta.criticidad)))
    return 5 if respuesta.es_critica else 3


def _observacion_dimension(califica: bool, brechas_criticas: int, brechas_altas: int, score: float) -> str:
    if not califica:
        return ETIQUETA_SIN_DATOS
    if brechas_criticas > 0:
        return "Dimensión estructural prioritaria"
    if brechas_altas > 0:
        return "Requiere profundización"
    if score >= 90.0:
        return "Validar trazabilidad con el inventario y el RAT"
    return "Madurez reportada; confirmar con evidencia"


def agregar_resultado_por_dimension(respuestas: List[RespuestaControl]) -> ResultadoAssessment:
    """Agrega el assessment en las 10 dimensiones, cada una con su nivel 1-5 y sus topes."""
    respuestas = respuestas or []

    por_dimension: Dict[str, List[RespuestaControl]] = {d.id: [] for d in DIMENSIONES_SGPDP}
    for r in respuestas:
        por_dimension[_resolver_dimension(r)].append(r)

    brechas: List[BrechaDetectada] = []
    controles_estructurales_degradados = 0
    controles_bloqueantes_degradados = 0
    controles_sin_evidencia_suficiente = 0
    dimensiones: List[ResultadoDimension] = []

    for dim in DIMENSIONES_SGPDP:
        del_dominio = por_dimension[dim.id]
        evaluadas = [r for r in del_dominio if r.nivel_asignado is not None]

        suma_ponderada = 0.0
        # Base ponderada: la criticidad de todo lo aplicable. Lo no respondido
        # suma al denominador y no al numerador, luego computa como cero.
        base_criticidad = float(sum(_criticidad_efectiva(r) for r in del_dominio))
        brechas_criticas = 0
        brechas_altas = 0
        estructural_degradado = False
        evidencia_insuficiente = False

        for item in del_dominio:
            nivel_efectivo = calcular_nivel_efectivo(item)
            criticidad = _criticidad_efectiva(item)
            # El control aporta en proporción a su criticidad: un control menor
            # cumplido no compensa uno crítico incumplido.
            suma_ponderada += (nivel_efectivo / 5.0) * criticidad

            riesgo = (5.0 - nivel_efectivo) * criticidad
            es_estructural = item.pregunta_id in PREGUNTAS_ESTRUCTURALES

            if es_estructural and nivel_efectivo < UMBRAL_DEGRADACION_ESTRUCTURAL:
                controles_estructurales_degradados += 1
                estructural_degradado = True
            if criticidad >= CRITICIDAD_BLOQUEANTE and nivel_efectivo < UMBRAL_DEGRADACION_ESTRUCTURAL:
                controles_bloqueantes_degradados += 1
                estructural_degradado = True
            if (
                criticidad >= CRITICIDAD_EVIDENCIA_EXIGIBLE
                and evidencia_acotada(item) < UMBRAL_EVIDENCIA_EXIGIBLE
            ):
                controles_sin_evidencia_suficiente += 1
                evidencia_insuficiente = True

            severidad: Optional[SeveridadBrecha] = None
            if riesgo >= UMBRAL_RIESGO_CRITICO:
                severidad = SeveridadBrecha.CRITICO
                brechas_criticas += 1
            elif riesgo >= UMBRAL_RIESGO_ALTO:
                severidad = SeveridadBrecha.ALTO
                brechas_altas += 1

            if severidad is not None:
                brechas.append(
                    BrechaDetectada(
                        pregunta_id=item.pregunta_id,
                        control=item.control or f"Control {item.pregunta_id}",
                        dimension_id=dim.id,
                        dimension_nombre=dim.nombre,
                        severidad=severidad,
                        nivel_efectivo=_redondear(nivel_efectivo, 2),
                        riesgo=_redondear(riesgo, 1),
                        es_estructural=es_estructural,
                    )
                )

        items_evaluados = len(evaluadas)
        items_aplicables = len(del_dominio)
        score = (
            _redondear((suma_ponderada / base_criticidad) * 100.0, 1)
            if base_criticidad > 0
            else 0.0
        )
        cobertura_dim = (
            _redondear((items_evaluados / items_aplicables) * 100.0, 1)
            if items_aplicables > 0
            else 0.0
        )
        # Una dimensión con cobertura insuficiente no reporta nivel bajo: no
        # reporta nivel. El dato faltante no es un hallazgo de madurez.
        dim_califica = cobertura_dim >= COBERTURA_MINIMA_EMISION

        nivel = nivel_desde_score(score).nivel
        if estructural_degradado:
            nivel = min(nivel, NIVEL_TOPE_BRECHA_ESTRUCTURAL)
        if evidencia_insuficiente:
            nivel = min(nivel, NIVEL_TOPE_EVIDENCIA_INSUFICIENTE)

        dimensiones.append(
            ResultadoDimension(
                id=dim.id,
                nombre=dim.nombre,
                peso=dim.peso,
                items_aplicables=items_aplicables,
                items_evaluados=items_evaluados,
                cobertura_porcentaje=cobertura_dim,
                score=score,
                nivel=nivel if dim_califica else 0,
                nivel_etiqueta=NIVELES_MADUREZ_INDEX[nivel].etiqueta if dim_califica else ETIQUETA_SIN_DATOS,
                brechas_criticas=brechas_criticas,
                brechas_altas=brechas_altas,
                observacion=_observacion_dimension(dim_califica, brechas_criticas, brechas_altas, score),
                ajuste_por_brecha_estructural=estructural_degradado,
                ajuste_por_evidencia_insuficiente=evidencia_insuficiente,
            )
        )

    evaluadas_totales = [r for r in respuestas if r.nivel_asignado is not None]
    cobertura_porcentaje = (
        _redondear((len(evaluadas_totales) / len(respuestas)) * 100.0, 1)
        if respuestas
        else 0.0
    )

    brechas.sort(
        key=lambda b: (
            0 if b.es_estructural else 1,
            0 if b.severidad == SeveridadBrecha.CRITICO else 1,
            -b.riesgo,
        )
    )

    return ResultadoAssessment(
        dimensiones=dimensiones,
        brechas=brechas,
        brechas_criticas=sum(1 for b in brechas if b.severidad == SeveridadBrecha.CRITICO),
        brechas_altas=sum(1 for b in brechas if b.severidad == SeveridadBrecha.ALTO),
        controles_estructurales_degradados=controles_estructurales_degradados,
        controles_bloqueantes_degradados=controles_bloqueantes_degradados,
        controles_sin_evidencia_suficiente=controles_sin_evidencia_suficiente,
        total_evaluados=len(evaluadas_totales),
        total_aplicables=len(respuestas),
        cobertura_porcentaje=cobertura_porcentaje,
    )
