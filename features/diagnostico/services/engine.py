"""Motor de evaluación adaptativa y scoring por dimensión para Diagnóstico en 60 min."""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from features.diagnostico.domain.models import (
    FichaOrganizacion,
    PreguntaDiagnostico,
    RespuestaDiagnostico,
    RespuestaControl,
    ScoringDiagnostico,
    NivelEvidencia,
)
from features.diagnostico.services.dimensiones_sgpdp import agregar_resultado_por_dimension

_PATH_BANCO_JSON = Path(__file__).resolve().parent.parent / "domain" / "banco_preguntas.json"

_ORDEN_TALLAS = ("micro", "pequena", "mediana", "corporativo")
_RANGO_TALLA = {t: i for i, t in enumerate(_ORDEN_TALLAS)}

def normalizar_tamano(tamano: Optional[str]) -> str:
    """Normaliza cualquier etiqueta o clave de tamaño a la clave canónica del servidor."""
    t = (tamano or "").strip().lower()
    if "micro" in t:
        return "micro"
    if "peque" in t:
        return "pequena"
    if "media" in t:
        return "mediana"
    if "corp" in t:
        return "corporativo"
    return "corporativo"

def _resolver_texto_por_talla(base: str, variantes: Optional[Dict[str, str]], talla: str) -> str:
    if not variantes:
        return base
    rango_obj = _RANGO_TALLA.get(talla, 3)
    elegido = base
    for t in _ORDEN_TALLAS:
        if _RANGO_TALLA[t] > rango_obj:
            break
        if t in variantes and variantes[t]:
            elegido = variantes[t]
    return elegido

def cargar_banco_preguntas_raw() -> List[dict]:
    """Carga los 80 controles canónicos desde el JSON del servidor."""
    with open(_PATH_BANCO_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def generar_banco_preguntas_diagnostico(tamano: Optional[str] = None) -> List[PreguntaDiagnostico]:
    """Devuelve las preguntas del banco canónico adaptadas a la talla.
    
    Si se especifica tamaño, resuelve el enunciado y la evidencia esperada para esa talla.
    Si no se especifica, usa el enunciado base y evidencia base de cada control.
    """
    raw_data = cargar_banco_preguntas_raw()
    talla_norm = normalizar_tamano(tamano) if tamano else "corporativo"
    
    preguntas: List[PreguntaDiagnostico] = []
    for item in raw_data:
        enunciado = _resolver_texto_por_talla(
            item["enunciado"], item.get("enunciadoPorTamano"), talla_norm
        )
        evidencia = _resolver_texto_por_talla(
            item["evidenciaEsperada"], item.get("evidenciaPorTamano"), talla_norm
        )
        preguntas.append(
            PreguntaDiagnostico(
                id_pregunta=str(item["id"]),
                dominio_id=item["dimensionId"],
                enunciado=enunciado,
                referencia_normativa=item["referenciaNormativa"],
                es_nucleo=True,
                evidencia_esperada=evidencia,
                control=item.get("control", ""),
                criticidad=item.get("criticidad", 3),
                tamano_minimo=item.get("tamanoMinimo", "micro"),
                es_estructural=item.get("esEstructural", False),
                ejemplo=item.get("ejemplo", ""),
            )
        )
    return preguntas

def filtrar_preguntas_visibles(ficha: FichaOrganizacion) -> List[PreguntaDiagnostico]:
    """Aplica la poda ontológica por tamaño según tamanoMinimo.
    
    Invariante: Nunca supera 80 preguntas visibles.
    """
    talla = normalizar_tamano(ficha.tamano)
    rango_ficha = _RANGO_TALLA.get(talla, 3)
    
    todas = generar_banco_preguntas_diagnostico(tamano=talla)
    visibles: List[PreguntaDiagnostico] = []
    for p in todas:
        rango_min = _RANGO_TALLA.get(p.tamano_minimo, 0)
        if rango_ficha >= rango_min:
            visibles.append(p)
            
    if len(visibles) > 80:
        visibles = visibles[:80]
        
    return visibles

def calcular_scoring_multidimensional(respuestas: List[RespuestaDiagnostico]) -> ScoringDiagnostico:
    """Calcula los vectores ortogonales del diagnóstico; la madurez va por dimensión (DIAG-08)."""
    if not respuestas:
        return ScoringDiagnostico(
            porcentaje_conformidad_juridica=0.0,
            cobertura_evidencia_porcentaje=0.0,
            brechas_criticas_abiertas=0,
            preguntas_respondidas_total=0,
            duracion_minutos_estimada=0,
        )

    total_preguntas = len(respuestas)
    afirmativas = sum(1 for r in respuestas if r.respuesta_afirmativa)
    evidencias_validas = sum(
        1 for r in respuestas if r.respuesta_afirmativa and r.nivel_evidencia != NivelEvidencia.E0_VERBAL
    )
    brechas_criticas = total_preguntas - afirmativas

    banco = {str(p["id"]): p for p in cargar_banco_preguntas_raw()}
    entradas = [
        RespuestaControl(
            pregunta_id=int(r.id_pregunta),
            nivel_asignado=r.nivel_asignado,
            evidencia_nivel=r.nivel_evidencia.nivel,
            criticidad=banco.get(str(r.id_pregunta), {}).get("criticidad", 3),
            dimension_id=banco.get(str(r.id_pregunta), {}).get("dimensionId"),
        )
        for r in respuestas
    ]
    por_dimension = [d for d in agregar_resultado_por_dimension(entradas).dimensiones if d.items_aplicables > 0]

    return ScoringDiagnostico(
        porcentaje_conformidad_juridica=round((afirmativas / total_preguntas) * 100.0, 1),
        cobertura_evidencia_porcentaje=round((evidencias_validas / total_preguntas) * 100.0, 1),
        brechas_criticas_abiertas=brechas_criticas,
        preguntas_respondidas_total=total_preguntas,
        duracion_minutos_estimada=min(60, int(total_preguntas * 0.8)),
        por_dimension=por_dimension,
    )
