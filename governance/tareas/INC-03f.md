+++
id = "INC-03f"
titulo = "Insignia de estado y botones Cerrar y Reabrir en la bitácora de incidentes"
ola = "backlog"
estado = "pendiente"
sala = "frontend"
depende_de = ["INC-03", "FE-17", "INC-01"]
propiedad = ["frontend/src/components/IncidentPlaybook.tsx", "frontend/src/lib/incidentes/estado.ts", "frontend/tests/incidentes/estado.spec.ts"]
crea = ["frontend/src/lib/incidentes/estado.ts", "frontend/tests/incidentes/estado.spec.ts"]
arbitro = "Playwright frontend/tests/incidentes/estado.spec.ts + tsc --noEmit + npm run build; mutaciones m1 a m4"
rastros = ["¤incidentes", "¤rbac-tenant"]
+++

# INC-03f · Insignia de estado y botones Cerrar y Reabrir en la bitácora de incidentes

Diseño del Arquitecto ADPA (2026-11-13, medido contra main 3bb40557), pedido del CTO. **Pasa por UX/UI antes de lanzarse.** Frontend de `INC-03`: la API ya está en `main` (`POST /api/v1/incidentes/{id}/cerrar` y `/reabrir`; el `GET` de la lista devuelve `estado`).

## Entrega
- Insignia «Abierto» o «Cerrado», y «Cerrado, notificación pendiente» cuando `decision_notificacion = 'pendiente'`.
- Botones Cerrar y Reabrir con un diálogo de motivo: mínimo 10 caracteres sin contar espacios; el botón de confirmar queda deshabilitado por debajo.
- Si el servidor responde 409, se muestra su mensaje por código y se recarga el estado.
- Los botones solo se ven con `ROLES_REGISTRO`; el DPO y el auditor solo ven la insignia.
- Las llamadas van en `frontend/src/lib/incidentes/estado.ts` (nuevo), con `fetchAutenticado`. Los roles se leen de `roles.ts`, que se importa y no se edita.
- Colores con `--ui-*` y `badge-render-*`; ningún token de gobernanza en la interfaz.

## Pruebas (cada una con su mutación)
- **m1:** quitar el mínimo de 10 → falla la prueba del botón deshabilitado.
- **m2:** mostrar los botones al DPO → falla.
- **m3:** ignorar el 409 → falla la prueba que espera el mensaje.
- **m4:** la insignia ignora `'pendiente'` → falla.

## Límites
- No toca `frontend/src/components/incidentes/**` (INC-02), `frontend/src/lib/incidentes/cliente.ts` ni `roles.ts`.
- `IncidentPlaybook.tsx` y `frontend/src/lib/incidentes/**` son de INC-01 y FE-17 (hechas); el comodín de INC-01 cubre `estado.ts`, por eso va en `crea`.
