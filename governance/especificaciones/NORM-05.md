# NORM-05 · El backend no adopta el rol del monitoreo
`¤sdd` `¤vigilancia-spdp` `¤inteligencia-normativa` `¤seguridad` `¤arbitro` `¤monitoreo-job`

## 1. Datos

Hechos medidos en `origin/main` 3725bbd0.

**Concesiones.** `lopdp_normativa` (NOLOGIN) lo crea `alembic/versions/norm01_inteligencia_normativa.py:80-87`, con `SELECT, INSERT, UPDATE` sobre `normativa_resoluciones` y `normativa_monitoreo_logs`, y `SELECT, INSERT` sobre `normativa_versiones`. Ninguna migración ni script lo concede a nadie. El Job lo recibe en su usuario `lopdp_monitor_normativo` (brief de NORM-04).

**Quién adopta `lopdp_normativa`:**

| Lugar | Proceso | Situación |
| :--- | :--- | :--- |
| `revision.py:144` (`registrar_revision`, NORM-02) | backend | **falla** si `lopdp_app` no es miembro: `UPDATE normativa_resoluciones SET estado, revisada_por, revisada_en, nota_revision` |
| `monitoreo.py:94,114,128` (NORM-01) | Job (NORM-04) y **disparo manual del backend** | El disparo manual `POST /api/v1/normativa/monitoreo` (`router:103-106`) corre `disparar_monitoreo` dentro del backend. Falla por el rol y, tras NORM-04 R1, también por el almacén, que solo escribe en un Job. |
| `inteligencia_normativa_service.py:373-381` (`_anotar_avisos`, NORM-02b) | dentro de la corrida | Va con la corrida: en el Job funciona. |
| `trabajo_monitoreo.py:30` (NORM-04) | Job | Correcto. |

- **NORM-03 no sigue el patrón.** `impacto.py:163,205` escribe `normativa_analisis_impacto` como `lopdp_app`, con `GRANT SELECT, INSERT, UPDATE … TO lopdp_app` (`20261104_norm03_analisis_impacto.py:57`). No cambia.
- **Por qué las pruebas no lo vieron.** `test_norm02_centro_vigilancia.py` no se conecta como `lopdp_app`, y `test_norm01…:399-409` hace `SET ROLE lopdp_normativa` desde el dueño.
- **Alembic.** La rama de la sala `inteligencia_normativa` tiene la etiqueta en `20261104_norm03_analisis_impacto.py:18`. Su cabeza se lee con `alembic heads`.

**Migración nueva** `alembic/versions/norm05_revision_sin_rol_monitoreo.py`:
- `down_revision` = la cabeza de `inteligencia_normativa@head` (FUSION_ALEMBIC §2), sin `branch_labels`;
- `GRANT UPDATE (estado, revisada_por, revisada_en, nota_revision) ON normativa_resoluciones TO lopdp_app`;
- `GRANT SELECT ON normativa_resoluciones TO lopdp_app`, si no lo tiene ya (se comprueba en la migración, que lo deja idempotente);
- el `downgrade` revoca exactamente eso;
- ningún `GRANT lopdp_normativa TO …`.

## 2. API

| Ruta | Cambio |
| :--- | :--- |
| `POST /api/v1/normativa/resoluciones/{id}/revision` (NORM-02) | Sin cambio de contrato. Deja de fallar en producción. |
| `POST /api/v1/normativa/monitoreo` | Misma respuesta 202 `{"estado": "aceptado"}`. Ahora lanza una ejecución del Job `evydentia-monitoreo-normativo` (R3). Si no puede lanzarla, 503 `NORMATIVA_TRABAJO_NO_DISPONIBLE` sin detalle. |

## 3. Reglas

- **R1 · La revisión como `lopdp_app`.** `registrar_revision` deja de llamar a `_como_normativa` y de importarlo. Escribe con la conexión del backend y solo las cuatro columnas de §1, y la validación del estado y de la nota no cambia.
- **R2 · El backend nunca adopta `lopdp_normativa`.** Ningún camino del proceso del backend hace `SET ROLE lopdp_normativa`. La prueba lo comprueba conectada como `lopdp_app`: `SET LOCAL ROLE lopdp_normativa` da error, `INSERT` en `normativa_versiones` y en `normativa_monitoreo_logs` da error, y `UPDATE` de otra columna de `normativa_resoluciones` (por ejemplo `titulo`) da error.
- **R3 · El disparo manual lanza el Job.** `lanzador_trabajo.lanzar()`:
  - llama a la API de Cloud Run v2, `projects/<PROJECT_ID>/locations/us-central1/jobs/evydentia-monitoreo-normativo:run`, con las credenciales por defecto del backend;
  - toma el nombre del Job de `NORMATIVA_TRABAJO_MONITOREO`;
  - con la variable vacía o fuera de Cloud Run (`K_SERVICE`), lanza `TrabajoNoDisponible` sin llamar a nada;
  - la sección `#NORM-05` del router sustituye la llamada en segundo plano a `disparar_monitoreo` por `lanzar()`.

  La ejecución lanzada corre con `origen = "programado"` (NORM-04 R3). La bitácora la distingue por la hora y por quién disparó, que se registra en el log del backend sin datos personales. El origen `manual` deja de usarse para corridas nuevas y sigue siendo válido en la historia.
- **R4 · Sin escritura del backend en el corpus.** R1 a R3 no conceden al backend ninguna escritura en el bucket ni en las tablas de versiones y bitácora. Cumple la decisión 5 de `BRIEF_PROPIETARIO_BUCKET_NORMATIVO.md`.
- **R-ADPA · Ortogonalidad ZERAG (`NORM-05`).** Solo los archivos de la propiedad. `monitoreo.py`, `trabajo_monitoreo.py` y la sección `#NORM-04` son de NORM-04, que está `en_curso`, y no se tocan. Este PR de gobernanza solo siembra las dos secciones vacías `=== NORM-05 ===`.

## 4. Interfaz

Sin cambios. El botón del Centro de vigilancia sigue recibiendo 202.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** una conexión como `lopdp_app`, **entonces** `registrar_revision` cambia el estado y la nota. Mutación m1: dejar `_como_normativa` da rojo. | `test_norm05_privilegios_backend.py` |
| **Dado** `lopdp_app`, **entonces** `INSERT` en `normativa_versiones` y en `normativa_monitoreo_logs`, `UPDATE titulo` y `SET ROLE lopdp_normativa` dan error. Mutación m2: conceder `UPDATE` de toda la tabla en la migración da rojo. | ídem |
| **Dado** `POST /monitoreo` con un lanzador doble, **entonces** 202 y una llamada a `:run` con el nombre del Job, sin llamar a `disparar_monitoreo`. Mutación m3: volver a `disparar_monitoreo` da rojo. | ídem |
| **Dado** `NORMATIVA_TRABAJO_MONITOREO` vacía, **entonces** 503 `NORMATIVA_TRABAJO_NO_DISPONIBLE` sin llamadas. Mutación m4: llamar igual da rojo. | ídem |
| **Dado** el grafo de Alembic, **entonces** una sola cabeza por sala. Mutación m5: colgar la migración de la cabeza de otra sala da rojo. | `test_alembic_cabeza_por_sala.py` |
| **Dado** `test_bitacora_y_disparo_manual` (`tests/test_norm02_centro_vigilancia.py`, que pasa a la propiedad de esta ficha), **entonces** inyecta un doble de `lanzador_trabajo.lanzar` y comprueba 202 y una sola llamada al lanzador, en lugar de `lanzadas == ["manual"]`. La bitácora no cambia. Sin el doble y sin `NORMATIVA_TRABAJO_MONITOREO`, como en el CI, el mismo `POST` da 503 `NORMATIVA_TRABAJO_NO_DISPONIBLE`, y la prueba lo comprueba en un caso aparte. | `test_norm02_centro_vigilancia.py` |
| **Dado** las demás pruebas de NORM-02 y las suites de NORM-01, NORM-02b y NORM-03, **entonces** siguen en verde. | existentes |

## 6. Trazabilidad

- **PRD:** §4, Módulo 6.1, «Ejecución y reparto de privilegios»; ley fundacional 13.
- **Rastro:** `¤monitoreo-job` (alta en VPA_MAP por PRD-04). Los archivos que crea esta ficha llevan `# ¤monitoreo-job` en la cabecera, junto a sus rastros de sala.
- Hallazgo del CTO y medición del Arquitecto (2026-11-24). Diseño de NORM-01 (decisión 5).
- Depende de NORM-01, NORM-02, NORM-03 y NORM-04 (Job y nombre).
- **Brief del propietario,** tras fusionar y desplegar:
  - conceder a `sa-evydentia-backend` `roles/run.invoker` (o `run.jobs.run`) **solo sobre** el Job `evydentia-monitoreo-normativo`;
  - fijar `NORMATIVA_TRABAJO_MONITOREO=evydentia-monitoreo-normativo` en el backend;
  - migrar con `alembic upgrade heads`;
  - confirmar con la consulta de miembros que `lopdp_app` no es miembro de `lopdp_normativa`.

  Brief: `C:\Users\Juan Carlos\compartido\evydentia\briefs\NORM-05-propietario.md`.
