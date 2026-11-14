# INC-03f · Insignia de estado y botones Cerrar y Reabrir en la bitácora de incidentes
`¤sdd` `¤incidentes` `¤rbac-tenant`

## 1. Datos

Sin tablas ni migraciones: es el frontend de INC-03. Usa lo que la API ya devuelve en `main`:

- la lista de incidentes trae, por incidente, `estado` (`abierto` o `cerrado`) y `estado_detalle`, que incluye `decision_notificacion` cuando el cierre quedó con la decisión de notificar pendiente;
- un incidente sin eventos de estado llega como `abierto`.

Archivos: `frontend/src/components/IncidentPlaybook.tsx` (existente) y dos nuevos, `frontend/src/lib/incidentes/estado.ts` y `frontend/tests/incidentes/estado.spec.ts`.

## 2. API

No se crea ninguna ruta. El cliente nuevo `estado.ts` llama, con `fetchAutenticado`, a las dos rutas de INC-03:

| Método y ruta | Entrada | Respuesta que maneja la pantalla |
| :--- | :--- | :--- |
| `POST /api/v1/incidentes/{id}/cerrar` | `{motivo}` | 200 con el estado nuevo |
| `POST /api/v1/incidentes/{id}/reabrir` | `{motivo}` | 200 con el estado nuevo |

| Código HTTP | `code` | Qué hace la pantalla |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | muestra que no tiene permiso; no debería ocurrir, porque los botones no se muestran |
| 404 | `INCIDENTE_NO_ENCONTRADO` | muestra el mensaje y recarga la lista |
| 409 | `INCIDENTE_YA_CERRADO`, `INCIDENTE_YA_ABIERTO` | muestra el mensaje del código y recarga el estado |
| 422 | (validación) | muestra que el motivo no es válido |

## 3. Reglas

- **R1 · Insignia.** «Abierto» o «Cerrado» según `estado`. Cuando el cierre lleva `decision_notificacion = 'pendiente'`, la insignia dice «Cerrado, notificación pendiente».
- **R2 · Motivo.** Cerrar y Reabrir abren un diálogo con un campo de motivo. El botón de confirmar queda deshabilitado mientras el motivo, sin espacios al inicio ni al final, tenga menos de 10 caracteres. El límite superior es el de la API (2000).
- **R3 · Quién ve los botones.** Solo los roles que registran (`ROLES_QUE_REGISTRAN` de `frontend/src/lib/incidentes/roles.ts`, que se importa y no se edita). El DPO y el auditor ven la insignia y no ven los botones. La pantalla no decide el permiso: la API lo vuelve a exigir.
- **R4 · Un botón por estado.** Un incidente abierto muestra Cerrar; uno cerrado muestra Reabrir.
- **R5 · Conflicto.** Ante un 409, la pantalla muestra el mensaje que corresponde al código y vuelve a pedir el estado. No reintenta sola.
- **R6 · Presentación.** Colores con las variables del tema (`--ui-*`, `badge-render-*`). Ningún token de gobernanza en la interfaz. Los textos son los que entregue UX/UI.
- **R7 · Límites.** No se toca `frontend/src/components/incidentes/` (INC-02), ni `cliente.ts`, ni `roles.ts`.
- **R-ADPA · Ortogonalidad ZERAG (`INC-03f`).** Solo frontend; las llamadas van por `fetchAutenticado`.

## 4. Interfaz

Operación › Vulneraciones, en la bitácora (`IncidentPlaybook.tsx`): cada incidente muestra su insignia de estado y, para quien registra, el botón Cerrar o Reabrir. El botón abre el diálogo de motivo. Pasa por UX/UI antes de lanzarse.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un incidente abierto, uno cerrado y uno cerrado con la notificación pendiente, **entonces** las tres insignias son distintas y la tercera dice que la notificación está pendiente. Mutación: ignorar `'pendiente'` hace fallar la prueba. | `frontend/tests/incidentes/estado.spec.ts` · insignias |
| **Dado** el diálogo de cierre con un motivo de 9 caracteres o de solo espacios, **entonces** confirmar está deshabilitado; con 10, se habilita. Mutación: quitar el mínimo hace fallar la prueba. | `frontend/tests/incidentes/estado.spec.ts` · motivo mínimo |
| **Dado** un usuario `dpo`, **entonces** ve la insignia y no ve Cerrar ni Reabrir; un `implementador` sí los ve. Mutación: mostrar los botones al DPO hace fallar la prueba. | `frontend/tests/incidentes/estado.spec.ts` · roles |
| **Dado** un cierre al que la API responde 409 `INCIDENTE_YA_CERRADO`, **entonces** la pantalla muestra ese mensaje y recarga el estado. Mutación: ignorar el 409 hace fallar la prueba. | `frontend/tests/incidentes/estado.spec.ts` · conflicto |
| **Dado** el frontend, **entonces** `tsc --noEmit` y `npm run build` pasan. | `frontend/tests/incidentes/estado.spec.ts` · compilación |

## 6. Trazabilidad

- Ficha: `governance/tareas/INC-03f.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Depende de INC-03, FE-17 e INC-01 (hechas). Especificación del backend: la ficha `INC-03`.
- Propiedad, medida en `origin/main` 4eca5af2: `IncidentPlaybook.tsx` es de INC-01 y FE-17 (hechas); `estado.ts` y `estado.spec.ts` son nuevos. Ninguna ficha abierta los posee. INC-02, en curso, posee `frontend/src/components/incidentes/`, que esta ficha no toca.
- **Bloqueo del árbitro:** `scripts/verificar_especificaciones.py` solo admite nombres `LETRAS-número` y rechaza el sufijo «f». Esta especificación no pasa hasta que el árbitro admita sufijos.
