"""Motor de evaluación adaptativa y scoring multidimensional para Diagnóstico en 60 min."""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from features.diagnostico.domain.models import (
    FichaOrganizacion,
    PreguntaDiagnostico,
    RespuestaDiagnostico,
    ScoringDiagnostico,
    NivelEvidencia,
)

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
