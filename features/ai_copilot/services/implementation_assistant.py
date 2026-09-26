# ¤¤frontend-architect
"""Respuestas trazables a las brechas, con DLP y recomendaciones reproducibles."""
import unicodedata

from features.ai_copilot.domain.assistant_models import (
    ConsultaAsistente, Fundamento, PlanImplementacion, RespuestaAsistente,
)
from features.ai_copilot.domain.sanitizer import LLMDataSanitizer
from features.ai_copilot.services.assistant_provider import enriquecer_implementacion

AVISO = (
    "Los pasos, responsables y revisiones son recomendaciones de implementación. "
    "El fundamento legal se muestra por separado. La asistencia no sustituye al DPD "
    "ni acredita el cierre: requiere evidencia y validación del responsable."
)


# ¤sanitizar-consulta
def sanitizar_consulta(consulta: ConsultaAsistente) -> ConsultaAsistente:
    datos = LLMDataSanitizer().sanitize_dict(consulta.model_dump())
    # La entrada ya fue validada. Los tokens DLP pueden ser más largos que el
    # dato reemplazado; reconstruir sin repetir max_length evita convertir una
    # consulta válida en un 500 después de protegerla.
    return ConsultaAsistente.model_construct(
        pregunta=datos["pregunta"],
        brechas=[type(b).model_construct(**segura) for b, segura in zip(consulta.brechas, datos["brechas"])],
        historial=[type(m).model_construct(**seguro) for m, seguro in zip(consulta.historial, datos["historial"])],
        brecha_id=datos["brecha_id"], estado=datos["estado"],
    )


# ¤normalizar
def normalizar(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower())
                   if unicodedata.category(c) != "Mn")


# ¤enfoque-local
def enfoque_local(pregunta: str) -> str:
    q = normalizar(pregunta)
    for enfoque, claves in (
        ("evidencias", ("evidencia", "demostrar", "documento", "comprobar", "plantilla")),
        ("responsable", ("responsable", "quien", "asignar")),
        ("seguimiento", ("seguimiento", "revision", "mantener", "periodic", "ya implement", "cerrar")),
        ("fundamento", ("articulo", "fundamento", "ley", "legal", "consentimiento")),
        ("pasos", ("paso", "implementar", "como", "hacer")),
    ):
        if any(clave in q for clave in claves):
            return enfoque
    return "plan"


# ¤citas
def citas(fundamentos: list[Fundamento]) -> str:
    return "; ".join(f"{f.articulo} — {f.titulo} ({f.version})" for f in fundamentos)


# ¤texto-plan
def texto_plan(plan: PlanImplementacion, enfoque: str, estado: str) -> str:
    partes = [
        f"Veamos la brecha P{plan.pregunta_id}: {plan.control}.",
        f"La prioridad es {plan.severidad} y está en estado: {estado}.",
    ]
    if enfoque in ("plan", "pasos"):
        partes += ["Pasos recomendados:"] + [f"{i}. {p}" for i, p in enumerate(plan.pasos, 1)]
    if enfoque in ("plan", "responsable"):
        partes += [f"Responsable sugerido: {plan.responsable_sugerido}"]
    if enfoque in ("plan", "evidencias"):
        partes += ["Evidencias a preparar:"] + [f"• {e}" for e in plan.evidencias]
    if enfoque in ("plan", "seguimiento", "evidencias"):
        partes += [f"Criterio de cierre: {plan.criterio_cierre}", f"Seguimiento: {plan.seguimiento}"]
    if enfoque == "fundamento":
        partes += [f"{f.articulo}: {f.resumen}" for f in plan.fundamento]
    partes += [f"Fundamento: {citas(plan.fundamento)}"]
    return "\n".join(partes)


# ¤prioridad-estado
def enfoque_por_estado(estado: str, pregunta: str) -> str:
    if estado == "Por iniciar":
        return "pasos"
    if estado == "Implementación":
        return "evidencias"
    if estado == "Seguimiento":
        return "seguimiento"
    return enfoque_local(pregunta)


# ¤responder-implementacion
async def responder_implementacion(
    consulta: ConsultaAsistente, guias: dict[int, dict],
    fuentes: list[dict], corpus_version: str,
) -> RespuestaAsistente:
    consulta = sanitizar_consulta(consulta)
    seleccion = [b for b in consulta.brechas
                 if consulta.brecha_id is None or b.pregunta_id == consulta.brecha_id]
    prioridades = {"Crítico": 0, "Alto": 1, "Medio": 2}
    seleccion.sort(key=lambda b: (prioridades[b.severidad], b.pregunta_id))
    planes = []
    faltantes = []
    for brecha in seleccion:
        guia = guias.get(brecha.pregunta_id)
        if not guia or not guia.get("fundamento"):
            faltantes.append(brecha.pregunta_id)
            continue
        planes.append(PlanImplementacion(
            pregunta_id=brecha.pregunta_id,
            control=guia.get("control", brecha.control), severidad=brecha.severidad,
            **{k: guia[k] for k in ("pasos", "responsable_sugerido", "evidencias",
                                  "criterio_cierre", "seguimiento", "fundamento")},
        ))
    fundamentos = [Fundamento.model_validate(f) for f in fuentes]
    for plan in planes:
        fundamentos.extend(plan.fundamento)
    fundamentos = list({(f.url, f.articulo, f.version): f for f in fundamentos}.values())
    advertencias = [AVISO]
    if faltantes:
        advertencias.append("Sin fuente suficiente para los controles: " + ", ".join(map(str, faltantes)))
    if not fundamentos:
        return RespuestaAsistente(
            pregunta=consulta.pregunta, respuesta=(
                "No encontré una fuente aplicable en el corpus versionado. "
                "Selecciona una brecha del assessment o precisa el proceso y la consulta jurídica."
            ), modo="sin_fuente", fundamentos=[], planes=[], advertencias=advertencias,
            corpus_version=corpus_version,
        )
    # El proveedor recibe el mínimo necesario. La identidad de la organización,
    # documentos, evidencias e historial permanecen en la plataforma.
    limite_externo = 12
    planes_externos = planes[:limite_externo]
    contexto_minimo = {
        "pregunta": consulta.pregunta,
        "prioridad_usuario": {
            "brecha_id": consulta.brecha_id,
            "estado": consulta.estado,
            "instruccion": "Prioriza este estado al explicar el plan.",
        },
        "brechas": [{
            "pregunta_id": p.pregunta_id, "control": p.control,
            "severidad": p.severidad,
        } for p in planes_externos],
        "fundamentos": [f.model_dump() for f in fundamentos],
        "planes_base": [{
            "pregunta_id": p.pregunta_id, "pasos": p.pasos,
            "responsable_sugerido": p.responsable_sugerido,
            "evidencias_requeridas": p.evidencias,
            "criterio_cierre": p.criterio_cierre,
        } for p in planes_externos],
    }
    externo, modo, aviso = await enriquecer_implementacion(contexto_minimo)
    enfoque = (externo or {}).get("enfoque") or enfoque_por_estado(consulta.estado, consulta.pregunta)
    if aviso:
        advertencias.append(aviso)
    if len(planes) > limite_externo:
        advertencias.append(
            f"DeepSeek priorizó las primeras {limite_externo} brechas; las restantes conservan su guía local."
        )
    if externo:
        actualizaciones = {p["pregunta_id"]: p for p in externo["planes"]}
        planes = [p.model_copy(update=actualizaciones.get(p.pregunta_id, {})) for p in planes]
        respuesta = externo["respuesta"]
        if planes:
            respuesta += "\n\nLos planes verificables se muestran debajo con sus artículos y evidencias."
    elif planes:
        respuesta = "\n\n".join(texto_plan(p, enfoque, consulta.estado) for p in planes)
        respuesta += "\n\nSi algo no queda claro, pregúntame por los pasos, las evidencias, el responsable o el seguimiento."
    else:
        respuesta = "\n\n".join(
            f"{f.articulo} — {f.titulo}: {f.resumen}\nVersión: {f.version}\nFuente: {f.url}"
            for f in fundamentos
        )
    return RespuestaAsistente(
        pregunta=consulta.pregunta, respuesta=respuesta, modo=modo,
        fundamentos=fundamentos, planes=planes, advertencias=advertencias,
        corpus_version=corpus_version,
    )
