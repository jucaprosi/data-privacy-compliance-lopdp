"""MARCA-03 · Nombre único EVYDENTIA en la plantilla de correo de notificaciones.

`¤interfaz`

Valores simulados; correos .invalid.
"""
from features.notificaciones.domain.models import Destinatario, TareaAsignadaItem
from features.notificaciones.services.plantillas_engine import renderizar_correo_lote_asignaciones

DESTINATARIO = Destinatario(user_id="u-marca03", email="titular@ejemplo.invalid", nombre="Persona Simulada", tenant_id="t-marca03")
TAREAS = [TareaAsignadaItem(task_id="tarea-1", titulo="Tarea simulada", control_ref="C-01", prioridad="alta")]


def _correo() -> str:
    asunto, texto, html = renderizar_correo_lote_asignaciones(DESTINATARIO, TAREAS, "https://app.ejemplo.invalid")
    return "\n".join((asunto, texto, html))


def test_la_plantilla_contiene_evydentia():
    assert "EVYDENTIA" in _correo()


def test_la_plantilla_no_contiene_jubys():
    assert "jubys" not in _correo().lower()
