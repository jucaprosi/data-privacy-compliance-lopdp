+++
id = "IA-03b"
titulo = "Evidencia de humo de la compuerta de inferencia con Vertex AI real (la corre el propietario)"
ola = "backlog"
estado = "en_curso"
sala = "inferencia"
depende_de = ["IA-03"]
propiedad = ["governance/operaciones/EVIDENCIA_HUMO_VERTEX.md", "governance/operaciones/BRIEF_PROPIETARIO_VERTEX.md"]
crea = ["governance/operaciones/EVIDENCIA_HUMO_VERTEX.md"]
arbitro = "evidencia humana, no es un árbitro de CI: el propietario corre VERTEX_HUMO=1 python -m pytest tests/test_ia03_humo_vertex.py con las credenciales de la cuenta de servicio y entrega la salida al CTO; el Tech Lead la registra en governance/operaciones/EVIDENCIA_HUMO_VERTEX.md"
rastros = ["¤gemini-vertex", "¤arbitro"]
+++

# IA-03b · Evidencia de humo de la compuerta de inferencia con Vertex AI real

Hija de `IA-03` (cierre del CTO, 2026-11-13). **Sin agente:** la corre el propietario; no hay código que escribir.

**Por qué.** `IA-03` dejó la compuerta, sus pruebas con cliente falso y la prueba `tests/test_ia03_humo_vertex.py` (opt-in, omitida sin `VERTEX_HUMO=1`). Lo que el CI no puede comprobar es la llamada real: el parse estructurado con Gemini, y que `gemini-2.5-flash` y `gemini-2.5-pro` estén disponibles en `us-central1` para este proyecto.

## Entrega
- El propietario sigue `governance/operaciones/BRIEF_PROPIETARIO_VERTEX.md` (API habilitada y `roles/aiplatform.user` a `sa-evydentia-backend`) y corre la prueba de humo.
- El Tech Lead registra en `governance/operaciones/EVIDENCIA_HUMO_VERTEX.md`: fecha, modelo, región, los dos esquemas validados (`PropuestaModelo` y `PlanMitigacionResponse`) y el resultado. Si algo falla, abre una ficha de ajuste del esquema o del adaptador sin cambiar la API de la compuerta.

## Límites
- Es evidencia y la cierra una persona. Ningún agente escribe en Google Cloud ni en la base.
- `IA-04` a `IA-11` se programan contra la compuerta con el cliente falso y **no se usan con Vertex real en producción hasta que esta ficha esté hecha**.
