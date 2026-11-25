# NORM-07 · Fecha de vigencia y disparo de la propuesta
`¤sdd` `¤monitoreo-job` `¤arbitro`

## 1. Datos

Hechos medidos en `origin/main` ed575cd2:
- `normativa_resoluciones` no guarda la fecha de entrada en vigencia.
- `registrar_revision` (`services/revision.py:136`) escribe como `lopdp_app`, y solo puede hacer UPDATE de cuatro columnas (`norm05_revision_sin_rol_monitoreo.py:32`).
- `revisar_estado` lo ejecuta un operador de la plataforma (`api/routers/inteligencia_normativa.py:115`, `require_operador`).
- La sala no tiene aún rama de Alembic propia: esta es su primera migración, que cuelga de `BASE_COMUN` (`ret02_clave_objeto`) con `branch_labels = ("inteligencia_normativa",)`.

Migración `20261125_norm07_fecha_vigencia.py`: `ALTER TABLE normativa_resoluciones ADD COLUMN fecha_vigencia date` (nula) y `GRANT UPDATE (fecha_vigencia)` a `lopdp_app`, con su `downgrade`.

## 2. API

- `POST /normativa/resoluciones/{id}/revision` acepta `fecha_vigencia` opcional (`AAAA-MM-DD`).
- La lectura de la resolución devuelve `fecha_vigencia`.

## 3. Reglas

- **R1 · Fecha opcional.** Al revisar, el operador puede dar la fecha de entrada en vigencia. Si no la da, se conserva la que hubiera. Se guarda con la revisión, en el mismo UPDATE.
- **R2 · Disparo.** Si el estado revisado es `reformada` o `derogada`, o `vigente` cuando la resolución ya tenía antes un estado distinto (BIB-406 R1), después de confirmar la revisión se llama a `proponer_por_resolucion(id_resolucion, estado, actor)` de `app_core/pasillo/biblioteca.py`, con el operador como actor. Si la propuesta falla, la revisión queda hecha y el fallo se registra en la bitácora.
- **R3 · Lectura.** `app_core/pasillo/inteligencia_normativa.py` expone `fecha_vigencia_de(id_resolucion)`, que leen BIB-407 y NOTIF-02.
- **R-SP · Sin prohibiciones** (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`NORM-07`).** Solo los archivos de la propiedad. Otras salas se usan solo por sus pasillos (`app_core/pasillo/`). Las pruebas no usan `import yaml`.

## 4. Interfaz

En `PanelResolucion.tsx`, junto al estado y la nota, un `<input type="date">` con su `<label>` «Fecha de entrada en vigencia (opcional)» y ayuda por `aria-describedby`: «Déjala en blanco si la norma no la indica. Se usa para los avisos de revisión de plantillas.». Si la resolución ya la tiene, aparece rellena. Error de formato: «Escribe una fecha válida.». Vacía, los avisos usan «La norma no indica fecha de vigencia.» (NOTIF-02 R2).

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** una revisión con `fecha_vigencia`, **entonces** queda guardada y el pasillo la devuelve. Mutación m1: no escribirla da rojo. | `tests/test_norm07_fecha_vigencia.py` |
| **Dado** una revisión `reformada`, **entonces** se llama una vez a `proponer_por_resolucion` con el operador como actor; con `observada`, ninguna. Mutación m2: llamarla también con `observada` da rojo. | ídem |
| **Dado** los privilegios de `lopdp_app`, **entonces** puede hacer UPDATE de las cuatro columnas de NORM-05 y de `fecha_vigencia`, y de nada más. Mutación m3: conceder UPDATE de toda la tabla da rojo. | `tests/test_norm05_privilegios_backend.py` |
| **Dado** el grafo, **entonces** la sala tiene una sola cabeza y solo importa la biblioteca por su pasillo. | `tests/test_alembic_cabeza_por_sala.py`, `tests/test_adpa_bulkhead.py` |

## 6. Trazabilidad

- **PRD:** Monitoreo normativo (PRD-04) y Módulo 7.
- Brief del CTO `ARQUITECTO_UXUI_PROPUESTAS_IA_PLANTILLAS` v1, v2 y v3 (2026-11-25), base `origin/main` ed575cd2, con las decisiones D1 a D7 del CTO y la propuesta de pantallas y textos del UX/UI (2026-11-25).
