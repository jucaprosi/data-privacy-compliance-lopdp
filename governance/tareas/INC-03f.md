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

## Textos cerrados por UX/UI (2026-11-13)
Diseñado contra `governance/especificaciones/INC-03f.md`; UX/UI no corrió pantalla.

**Insignias (R1, sin cambios).** «Abierto» · «Cerrado» · «Cerrado, notificación pendiente». Siempre texto e icono, no solo color. La tercera, en ámbar, con la línea «Falta registrar la decisión de notificar.»

**Botones (R4).** «Cerrar» y «Reabrir» como texto visible. Nombre accesible: «Cerrar el incidente {título}» / «Reabrir el incidente {título}».

**Diálogo de cierre.**
- Título: «¿Cerrar el incidente {título}?»
- Ayuda: «Indica por qué lo cierras. El motivo queda en la bitácora del incidente.»
- Campo: «Motivo del cierre» (textarea, máx. 2000).
- Aviso del mínimo, siempre visible bajo el campo y unido con aria-describedby: «Escribe al menos 10 caracteres.» Contador: «{n} de 10 caracteres como mínimo». Se cuentan sin espacios al inicio ni al final; con 10 o más pasa a «{n} caracteres».
- Botones: «Cancelar» (foco inicial) y «Cerrar el incidente». El de confirmar está deshabilitado con menos de 10 (R2) y, con el foco, se lee por qué (aria-describedby al aviso).
- Mientras envía: «Cerrando…», con aria-busy.

**Diálogo de reapertura.**
- Título: «¿Reabrir el incidente {título}?»
- Ayuda: «Indica por qué lo reabres. El motivo queda en la bitácora del incidente.»
- Campo: «Motivo de la reapertura». Mismo aviso y contador.
- Botones: «Cancelar» (foco inicial) y «Reabrir el incidente». Mientras envía: «Reabriendo…».

**Éxito** (role=status, tras cerrar el diálogo; el foco vuelve a la fila):
- «Incidente cerrado. El motivo quedó en la bitácora.»
- «Incidente reabierto. El motivo quedó en la bitácora.»
- Si el cierre deja la notificación pendiente: «Incidente cerrado. Falta registrar la decisión de notificar.»

**Errores (mensajes fijos por código; nunca el texto del servidor).**
- 403: «No tienes permiso para cambiar el estado de este incidente.»
- 404 INCIDENTE_NO_ENCONTRADO: «No encontramos este incidente. Actualizamos la lista.» (y recarga la lista).
- 422: «El motivo no es válido. Escribe entre 10 y 2000 caracteres.» (en el campo, dentro del diálogo).
- 409 INCIDENTE_YA_CERRADO: «Este incidente ya estaba cerrado. Actualizamos su estado.»
- 409 INCIDENTE_YA_ABIERTO: «Este incidente ya estaba abierto. Actualizamos su estado.»
- 409 DECISION_NOTIFICAR_PENDIENTE (INC-02, #773): «Antes de cerrar, registra si hay que notificar esta vulneración. Hazlo en el paso 7 del asistente, «Decisión de notificar».» Con el enlace «Ir a la decisión de notificar» (nombre accesible igual). El diálogo se cierra sin perder el motivo escrito si el usuario vuelve.
- Otros: «No pudimos cambiar el estado del incidente. Inténtalo de nuevo.»
- 403 y otros, como role=alert dentro del diálogo; 404 y 409, como role=alert en la lista, porque el diálogo se cierra y se recarga. 401: manejo global.

**Roles (R3).** El DPO y el auditor ven la insignia sin botones ni línea explicativa; la insignia basta.

**Estados de la lista.** Sin cambios de INC-01; vacío: «Aún no hay vulneraciones registradas.»

**Accesibilidad para Playwright.**
| Elemento | Rol | Nombre |
| :--- | :--- | :--- |
| Insignia | texto en la fila (no status) | Abierto / Cerrado / Cerrado, notificación pendiente |
| Botón | button | Cerrar el incidente {título} / Reabrir el incidente {título} |
| Diálogo | dialog (aria-modal) | ¿Cerrar el incidente {título}? / ¿Reabrir el incidente {título}? |
| Campo | textbox | Motivo del cierre / Motivo de la reapertura |
| Confirmar | button | Cerrar el incidente / Reabrir el incidente |
| Enlace del 409 | link | Ir a la decisión de notificar |

Foco atrapado; Escape cierra; contraste 4.5:1; tokens del tema; sin ¤ ni ¦; a 375 px el diálogo ocupa el ancho sin desbordar.

**Criterios añadidos** (además de los de §5): la insignia pendiente lleva texto, no solo color; el 409 DECISION_NOTIFICAR_PENDIENTE muestra el texto fijo y el enlace; ningún mensaje visible coincide con el texto del servidor simulado.
