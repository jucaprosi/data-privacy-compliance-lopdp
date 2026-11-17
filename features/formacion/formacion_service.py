# ¤adpa ¤implementacion
"""Compuerta pública de la sala Formación (PRD §7.1).

Andamiaje de ADPA-09: sin lógica; FOR-01 entrega la funcionalidad dentro de su sección.
"""
from __future__ import annotations

# === ADPA-09 ===
# Los códigos de error de esta sala viven en features/formacion/domain/errores.py y se registran al importarlo.
from features.formacion.domain import errores as _errores_sala  # noqa: F401
# === fin ADPA-09 ===

# === FOR-01 ===
from features.formacion.domain import errores  # noqa: F401
from features.formacion.schemas import (  # noqa: F401
    AccionCreate,
    AccionOut,
    CoberturaOut,
    ContenidoCreate,
    ContenidoOut,
    ExamenOut,
    ExamenSubmitRequest,
    ExamenSubmitResponse,
    IniciarExamenResponse,
    ParticipantesAddRequest,
    PreguntaCreate,
    PreguntaOut,
)
from features.formacion.services.acciones_engine import (
    anadir_participantes,
    crear_accion,
    listar_acciones,
    listar_participaciones_accion,
)
from features.formacion.services.cobertura_engine import calcular_cobertura
from features.formacion.services.contenidos_engine import (
    crear_contenido,
    crear_pregunta,
    listar_contenidos,
    listar_preguntas,
)
from features.formacion.services.examen_engine import (
    calificar_y_terminar_examen,
    iniciar_examen_participacion,
    obtener_examen_participacion,
)

__all__ = [
    "AccionCreate",
    "AccionOut",
    "CoberturaOut",
    "ContenidoCreate",
    "ContenidoOut",
    "ExamenOut",
    "ExamenSubmitRequest",
    "ExamenSubmitResponse",
    "IniciarExamenResponse",
    "ParticipantesAddRequest",
    "PreguntaCreate",
    "PreguntaOut",
    "errores",
    "crear_contenido",
    "listar_contenidos",
    "crear_pregunta",
    "listar_preguntas",
    "crear_accion",
    "listar_acciones",
    "anadir_participantes",
    "listar_participaciones_accion",
    "obtener_examen_participacion",
    "iniciar_examen_participacion",
    "calificar_y_terminar_examen",
    "calcular_cobertura",
]
# === fin FOR-01 ===
