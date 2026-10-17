+++
id = "SEC-04"
titulo = "Evidencia filtrada por rol en la API"
ola = "D"
estado = "pendiente"
sala = "roadmap"
depende_de = ["RM-13"]
propiedad = ["features/roadmap/services/evidencia_engine.py", "api/routers/roadmaps.py", "tests/test_evidencia_filtro_rol.py"]
arbitro = "pytest tests/test_evidencia_filtro_rol.py tests/test_matriz_permisos.py + suite completa"
rastros = ["¤seguridad", "¤rbac-tenant", "¤evidencias"]
+++

# SEC-04 · Evidencia filtrada por rol en la API

**Objetivo.** La matriz del PRD (§5.2) dice que el `responsable_area` ve solo la evidencia que subió él. Hoy `GET /roadmaps/tasks/{id}/evidence` devuelve toda la evidencia de la tarea a cualquier rol con membresía, y solo la interfaz (FE-04) la oculta: quien llame a la API directamente la recibe completa.

## Entrega
- `evidencia_engine.list_evidence` recibe el rol y el usuario de quien consulta, como parámetros opcionales para no cambiar la firma pública de la compuerta, y para `responsable_area` devuelve solo las filas cuyo `uploaded_by` es su usuario. Los demás roles siguen viendo toda la evidencia del tenant.
- El router pasa el contexto ya verificado (`ctx["role"]`, `ctx["user_id"]`).
- Pruebas con base de datos (rama de Neon propia): cada uno de los cinco roles, evidencia de dos usuarios en la misma tarea y evidencia de otro tenant que nunca aparece. Cada prueba mata una mutación que ninguna otra mata.
- Revisar y dejar anotado si otra consulta expone evidencia sin ese filtro; si la hay fuera de la propiedad, repórtala como tarea, no la cambies.

## Límites
- No cambia la firma pública de ninguna compuerta ni toca el frontend: FE-04 ya filtra en pantalla y sigue siendo correcto.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
