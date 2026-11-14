# INC-04 · La marca «notificación pendiente» del cierre dice la verdad
`¤sdd` `¤incidentes` `¤seguridad-tenant`

## 1. Datos

Sin migraciones. La columna `incidentes_eventos_estado.decision_notificacion` y su CHECK (`IS NULL OR = 'pendiente'`, de `inc03_incidentes_estado.py`) no cambian.

Medido en `origin/main`:
- `features/incidentes/services/estado_engine.py`, en `_cambiar_estado`, escribe `decision_notificacion = 'pendiente'` en todo cierre de un incidente con datos personales.
- La constante `DECISION_PENDIENTE` de `features/incidentes/domain/estado.py` está anotada como «ESTIMADO»: servía para cuando el cierre podía ir antes de que existiera la decisión de notificar de INC-02.
- Desde el #773, `exigir_decision_para_cierre` (INC-02, R7) impide cerrar un incidente con datos personales sin la sección 7, con 409 `DECISION_NOTIFICAR_PENDIENTE`.

Por eso hoy todo cierre nuevo con datos personales queda marcado «pendiente» aunque la decisión esté registrada, y la marca miente.

## 2. API

Ninguna ruta cambia. Cambia el valor de `decision_notificacion` en las respuestas de estado (`cerrar`, `reabrir`, la lista y el detalle):

| Caso | Antes | Después |
| :--- | :--- | :--- |
| Cierre nuevo con datos personales (ya tiene sección 7, por R7 de INC-02) | `'pendiente'` | `null` |
| Cierre anterior marcado `'pendiente'` cuyo incidente hoy tiene sección 7 | `'pendiente'` | `null` |
| Cierre anterior marcado `'pendiente'` cuyo incidente sigue sin sección 7 | `'pendiente'` | `'pendiente'` (verdadero) |
| Cierre sin datos personales, o incidente abierto | `null` | `null` |

## 3. Reglas

- **R1 · No se escribe una marca falsa.** `_cambiar_estado` deja de escribir `'pendiente'`: todo evento nuevo lleva `decision_notificacion = NULL`. La precondición de INC-02 (R7) garantiza que un cierre con datos personales ya tiene la decisión.
- **R2 · Lectura veraz de lo anterior.** Al leer el estado, la marca `'pendiente'` de un cierre se entrega solo si el incidente sigue sin ninguna versión de la sección 7. La comprobación usa `tiene_decision` de la sala de incidentes, que es la misma sala, así que no hace falta pasillo. Las filas guardadas no se modifican: la historia es inmutable y no hay backfill.
- **R3 · La constante.** `DECISION_PENDIENTE` se conserva solo para leer los eventos anteriores. Se quita la anotación «ESTIMADO» y se escribe por qué existe.
- **R4 · Auditoría.** `registrar_evento` del cierre deja de llevar `decision_notificacion: 'pendiente'` en los eventos nuevos.
- **R5 · Prueba ajena.** La mutación m9 de `tests/test_inc03_estado_incidente.py` (INC-03, hecha) afirma `'pendiente'` en un cierre con datos personales. Pasa a INC-04 con cesión explícita y se declara en la tabla de pruebas ajenas del PR: `test_m9_cierre_con_datos_personales_exige_la_decision | cerrado_con.decision_notificacion == "pendiente" → is None | R7 de INC-02 hace imposible el cierre sin decisión | R1`. La parte que exige el 409 sin decisión no cambia.
- **R-ADPA · Ortogonalidad ZERAG (`INC-04`).** Solo la sala de incidentes; sin llamadas a otras salas.

## 4. Interfaz

No aplica en esta ficha. La insignia de INC-03f sigue el valor de la API y queda correcta sin cambios.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un incidente con datos personales y su sección 7, **cuando** se cierra, **entonces** el estado tiene `decision_notificacion = null` y la fila guardada también. Mutación: volver a escribir `'pendiente'` hace fallar la prueba. | `test_cierre_con_decision_sin_marca` |
| **Dado** un evento de cierre anterior marcado `'pendiente'` y un incidente que ya tiene sección 7, **entonces** la API entrega `null`, y la fila sigue guardando `'pendiente'`. Mutación: entregar el valor guardado sin comprobar la sección 7 hace fallar la prueba. | `test_marca_anterior_con_decision_no_se_muestra` |
| **Dado** un evento anterior marcado `'pendiente'` y un incidente sin sección 7, **entonces** la API entrega `'pendiente'`. | `test_marca_anterior_sin_decision_se_conserva` |
| **Dado** un incidente sin datos personales, **entonces** el cierre sigue entregando `null`. | `test_sin_datos_personales_sin_cambio` |
| **Dado** registros de A, **cuando** se consulta el estado en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_estado_sin_cambio` |
| **Dado** la mutación m9 adaptada, **entonces** sigue exigiendo el 409 `DECISION_NOTIFICAR_PENDIENTE` sin decisión. | `tests/test_inc03_estado_incidente.py::test_m9_cierre_con_datos_personales_exige_la_decision` |

Las nuevas van en `tests/test_inc04_marca_notificacion.py`, contra el PostgreSQL 16 local con `lopdp_app`, sin `import yaml`.

## 6. Trazabilidad

- Ficha: `governance/tareas/INC-04.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Origen: la sesión de INC-02, mediante el Tech Lead (2026-11-13). Decisión del Arquitecto: el backend se corrige antes y la insignia de INC-03f sigue el valor de la API tal cual.
- Depende de INC-02 (#773, fusionado) e INC-03 (hecha). INC-03f depende de INC-04.
- **Propiedad**, medida en `origin/main`:
  - `features/incidentes/services/estado_engine.py` y `features/incidentes/domain/estado.py`. Son de INC-03 (hecha) y ninguna ficha abierta los posee;
  - `tests/test_inc03_estado_incidente.py`, con cesión y solo para la mutación m9;
  - `tests/test_inc04_marca_notificacion.py` (crea).
