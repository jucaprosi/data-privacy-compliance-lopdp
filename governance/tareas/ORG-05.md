+++
id = "ORG-05"
titulo = "Un único camino de altas de roles; sin concesión a uno mismo"
ola = "D"
estado = "hecha"
sala = "organizacion"
depende_de = ["ORG-02", "RM-01", "RM-10", "SEC-03"]
propiedad = ["features/organizacion/services/roles_engine.py", "api/routers/organizacion.py", "tests/test_alta_unica_roles.py", "tests/test_organizacion_api.py", "features/organizacion/organizacion_service.py#ORG-05"]
arbitro = "pytest tests/test_alta_unica_roles.py tests/test_organizacion_api.py tests/test_matriz_permisos.py + suite completa"
rastros = ["¤rbac-tenant", "¤seguridad"]
+++

# ORG-05 · Un único camino de altas de roles; sin concesión a uno mismo

**Objetivo.** Hoy conviven dos caminos para dar `responsable_area`: el flujo de RM-10 (el `coordinador` solicita, el `implementador` aprueba y ejecuta, con rastro) y `POST /organizacion/roles` (el administrador asigna directo, sin solicitud y sin registro en `audit_events`). Dos caminos para lo mismo terminan en incoherencias, y el PRD (§5.3.1) dice que el alta de responsables tiene «un solo punto de creación y de auditoría».

## Entrega
- `POST /organizacion/roles` rechaza con 409 (y un mensaje que apunte al flujo) la concesión de `responsable_area` cuando la organización ya tiene un `implementador` activo; solo se permite directa durante el **arranque** (todavía no hay `implementador`), porque sin él el flujo no puede ejecutarse. Los demás roles siguen asignándose directo.
- Nadie puede concederse a sí mismo un rol operativo (`responsable_area`, `coordinador`, `implementador`): 409.
- Cada concesión y cada revocación directas dejan evento en `audit_events` (`role_granted`, `role_revoked`), con quién, a quién y qué rol. Hoy no lo dejan.
- Ajustar `tests/test_organizacion_api.py` (de ORG-00, ya integrada), que concede `responsable_area` directo con un `implementador` ya presente: pasa por el flujo de RM-10 o usa el arranque.
- Pruebas: cada caso del camino único, el arranque, la autoconcesión, el rastro de auditoría y que el flujo de RM-10 sigue funcionando.

## Límites
- No cambia el flujo de RM-10 ni las excepciones de ORG-02.
- No elimina `POST /organizacion/roles`: el administrador sigue asignando `admin_organizacion`, `implementador` y `dpo`.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
