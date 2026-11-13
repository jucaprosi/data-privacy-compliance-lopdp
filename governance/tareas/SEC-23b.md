+++
id = "SEC-23b"
titulo = "El asistente pasa la organización autenticada al tope de inferencia"
ola = "backlog"
estado = "pendiente"
sala = "ai_copilot"
depende_de = ["SEC-23", "IA-07"]
propiedad = ["features/ai_copilot/services/implementation_assistant.py", "tests/test_sec23b_asistente_org.py"]
crea = ["tests/test_sec23b_asistente_org.py"]
arbitro = "pytest tests/test_sec23b_asistente_org.py + suites del asistente; mutación documentada"
rastros = ["¤seguridad-tenant"]
+++

# SEC-23b · El asistente pasa la organización autenticada al tope de inferencia

Decisión del CTO (2026-11-13). Tras SEC-23 (identidad del token) e IA-07 (firma de `responder_implementacion`), el router pasa el tenant autenticado como `org_id`, y la compuerta de inferencia cuenta el tope de esa organización. Hasta entonces, IA-07 deja `org_id=None` y el respaldo local.

Si hay que cambiar `api/routers/implementation_assistant.py`, la ficha amplía su propiedad cuando SEC-23 esté cerrada.

**Mutación:** pasar `org_id=None` con un tenant autenticado → falla la prueba que espera el consumo del tope de esa organización.
