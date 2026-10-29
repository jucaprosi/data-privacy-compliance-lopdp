# Especificaciones ejecutables (Spec-Driven Development)
`¤sdd`

Una especificación fija **qué** construye una tarea con el detalle suficiente para que dos agentes distintos produzcan el mismo contrato: nombres de tablas y columnas, rutas, cuerpos, códigos de error, reglas formales y criterios de aceptación. La ficha (`governance/tareas/<ID>.md`) sigue diciendo **quién, cuándo y con qué propiedad**; la especificación no la sustituye.

## Precedencia

`INVARIANTS.md` > `PRD.md` > especificación > ficha > código. Si una especificación contradice algo de rango superior, la tarea **se detiene** y lo informa al coordinador; no se elige en silencio.

## Contenido obligatorio

Cada `governance/especificaciones/<ID>.md` tiene, en este orden, estos seis apartados (los comprueba `scripts/verificar_especificaciones.py`):

1. `## 1. Datos` — tablas nuevas o cambiadas con tipo, nulabilidad, restricciones, RLS y permisos de `lopdp_app`; o «sin datos persistentes».
2. `## 2. API` — método, ruta, roles, cuerpo de entrada, respuesta y cada código HTTP con su `code`; o «sin API nueva».
3. `## 3. Reglas` — reglas de negocio como predicados o fórmulas, sin «según corresponda».
4. `## 4. Interfaz` — pantallas, estados y textos visibles; o «sin interfaz».
5. `## 5. Aceptación` — escenarios `Dado / Cuando / Entonces`; cada uno nombra la prueba que lo fija.
6. `## 6. Trazabilidad` — ficha, apartados del PRD, invariantes y decisiones abiertas.

## Convenciones del repositorio que toda especificación respeta

- Identificadores: `VARCHAR` con UUID v4 en texto, generado por el servidor. `tenant_id VARCHAR NOT NULL REFERENCES tenants(id)`.
- Fechas: `TIMESTAMPTZ` puestas por el servidor (`now()`); fechas civiles en `DATE`. Los límites de año se calculan en `America/Guayaquil`.
- Tablas por organización: `ENABLE` y `FORCE ROW LEVEL SECURITY`, política `USING` y `WITH CHECK` por `tenant_id = current_setting('app.current_tenant_id')`; `lopdp_app` sin `BYPASSRLS` y con el mínimo privilegio.
- Identidad y organización salen del token (`get_current_tenant`, `get_current_user`); nunca del cuerpo.
- Errores de negocio: `ErrorNegocio` con un código del catálogo de `app_core/errors.py`. Cuerpo de respuesta: `{"detail": str, "code": str, "action_required": str | null}`. Validación de entrada: 422 de FastAPI (`{"detail": [...]}`).
- Auditoría: `app_core.audit.registrar_evento(session, tenant_id, entity_type, entity_id, action, user_id, payload)` sobre `audit_events` (append-only).
- Cruces entre salas solo por `features/<sala>/<sala>_service.py`.
- Frontend: llamadas por `fetchAutenticado`, roles por `/organizacion/me/roles`, colores solo con variables del tema.
