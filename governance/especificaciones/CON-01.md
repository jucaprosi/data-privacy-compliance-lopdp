# CON-01 · Sala Conservación y Bloqueo (LOPDP art. 10 lit. i)
`¤sdd` `¤conservacion` `¤rat` `¤adpa`

## 1. Datos

Tabla `politicas_conservacion` (RLS ENABLE y FORCE por `tenant_id`), migración `alembic/versions/20260429_01_con01_politicas_conservacion.py`:
- `id` (UUID PK), `tenant_id` (VARCHAR(64) NOT NULL), `actividad_rat_id` (VARCHAR(64) NOT NULL), `plazo_meses` (INTEGER NOT NULL, `> 0`), `accion_vencimiento` (`'BLOQUEO' | 'ANONIMIZACION' | 'SUPRESION'`), `fecha_proxima_revision` (DATE NOT NULL), `estado` (`'ACTIVA' | 'BLOQUEADA' | 'EJECUTADA'`), `acta_ejecucion_hash` (VARCHAR(64) NULL), `creado_en` (TIMESTAMPTZ).

Constante única del umbral: `DIAS_POR_VENCER = 30` en `features/conservacion/conservacion_service.py`, sección `CON-01`. Su valor es **ESTIMADO**: no sale de la ley, que no fija un aviso previo, sino de la propuesta de UX/UI aceptada por el CTO (2026-11-15).

## 2. API

| Método y ruta | Roles | Respuesta |
| :--- | :--- | :--- |
| `GET /api/v1/conservacion/politicas` | `ROLES_CONSULTA`: admin_organizacion, implementador, dpo, coordinador y auditor | `200` lista con `semaforo` (`vigente`, `por_vencer`, `vencida`, o nulo si ya está ejecutada) |
| `POST /api/v1/conservacion/politicas` | `ROLES_EJECUCION`: admin_organizacion e implementador | `201` |
| `POST /api/v1/conservacion/politicas/{politica_id}/ejecutar` | `ROLES_EJECUCION` | `200` con `acta_ejecucion_hash` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 404 | `CONSERVACION_POLITICA_NO_ENCONTRADA` | la política no existe en la organización |
| 404 | `CONSERVACION_ACTIVIDAD_NO_ENCONTRADA` | el tratamiento no está en el RAT de la organización |
| 409 | `CONSERVACION_YA_EJECUTADA` | la política no está `ACTIVA` |
| 422 | `CONSERVACION_PLAZO_INVALIDO` | `plazo_meses < 1` |

## 3. Reglas

- **R1 · Vinculación con el RAT por el pasillo.** Al crear una política, la sala comprueba que `actividad_rat_id` es un tratamiento de la organización por `app_core/pasillo/rat.py#CON-01`.
- **R2 · La plataforma registra; la organización ejecuta.** La plataforma no bloquea, anonimiza ni suprime datos. «Ejecutar» registra la decisión y emite el acta: una vez por política, con la fila bloqueada (`FOR UPDATE`).
  - El acta es el JSON canónico (claves ordenadas, sin espacios) de `politica_id`, `tenant_id`, `actividad_rat_id`, `plazo_meses`, `accion_vencimiento`, `estado_resultante` y `ejecutada_en` (UTC, ISO 8601). No contiene datos personales.
  - `acta_ejecucion_hash` es el sha256 de esos bytes.
  - El evento de auditoría `politica_ejecutada` lleva el acta completa y su hash en el `payload`, así que cualquiera puede recalcular la huella.
  - El estado pasa a `BLOQUEADA` (acción `BLOQUEO`) o a `EJECUTADA` (`ANONIMIZACION` o `SUPRESION`).
  - Un segundo intento da 409 `CONSERVACION_YA_EJECUTADA`. La acción sobre los datos la hace la organización en sus sistemas.
- **R3 · Semáforo y alertas.** Para una política `ACTIVA`, con `d = fecha_proxima_revision − hoy` en días:
  - `vencida` si `d ≤ 0`;
  - `por_vencer` si `0 < d ≤ DIAS_POR_VENCER`;
  - `vigente` en otro caso.

  Las vencidas llegan al panel del DPO por `app_core/pasillo/conservacion.py#CON-01` y `app_core/pasillo/dpo_cockpit.py#CON-01`.
- **R4 · Roles.** Crean y registran la ejecución `admin_organizacion` e `implementador`. El DPO, el coordinador y el auditor solo leen. Las rutas están en la matriz parametrizada: `tests/matriz/CON-01.py` declara el prefijo `/api/v1/conservacion` en `PREFIJOS` y sus filas (ORG-22c, R5).
- **R-ADPA · Ortogonalidad ZERAG (`CON-01`).** Otras salas, solo por `app_core/pasillo/<sala>.py#CON-01` (`ImportsCruzados = ∅`). Los códigos de `ErrorNegocio` se registran en `features/conservacion/domain/errores.py#CON-01`.

## 4. Interfaz

Pantalla `frontend/src/components/layout/pantallas/CON-01.tsx`, registrada en las secciones `CON-01` de `frontend/src/components/layout/pantallas/index.tsx` y de `frontend/src/components/layout/menus/index.ts`. Es la convención de `main`: las pantallas viven en `components/layout/pantallas/` y las marcas `// --- INICIO CON-01 ---` ya existen en los dos índices. Ningún archivo está pendiente de cesión.

Ubicación: Inventario › «Conservación de datos». Botones «Registrar bloqueo», «Registrar anonimización» y «Registrar supresión», con el diálogo y la casilla de confirmación. Cita al pie: «LOPDP, art. 10, lit. i». Los demás textos son los de la ficha, cerrados por UX/UI. Ningún texto presenta la acción sobre los datos como algo que hace la plataforma.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un tratamiento activo en el RAT, **cuando** se crea una política con `plazo_meses = 24` y `accion_vencimiento = 'BLOQUEO'` y se ejecuta, **entonces** queda `BLOQUEADA` con `acta_ejecucion_hash`, y un segundo intento devuelve 409 `CONSERVACION_YA_EJECUTADA`. | `test_ciclo_politica_conservacion_y_bloqueo` |
| **Dado** el evento `politica_ejecutada`, **entonces** el sha256 del acta de su `payload` es igual a `acta_ejecucion_hash`. Mutación: dejar `ejecutada_en` fuera del `payload` hace fallar la prueba. | `test_acta_recalculable_desde_auditoria` |
| **Dado** fechas de revisión a 31, 30, 1 y 0 días, **entonces** el semáforo es `vigente`, `por_vencer`, `por_vencer` y `vencida`. Mutación: escribir 30 fuera de `DIAS_POR_VENCER` hace fallar la prueba que la cambia. | `test_semaforo_umbral_por_vencer` |
| **Dado** un `dpo`, **cuando** crea o ejecuta, **entonces** 403; **cuando** lista, 200. | `tests/test_matriz_permisos.py` |
| **Dado** dos organizaciones A y B, **cuando** B lista, **entonces** no ve las políticas de A. | `test_conservacion_rls_aislamiento_tenant` |
| **Dado** la pantalla, **entonces** el botón de registrar se habilita solo con la casilla marcada, el DPO no ve botones y ningún texto cita el art. 20. | `frontend/tests/conservacion/con01.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/CON-01.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD §7.1 (`conservacion`). LOPDP art. 10 lit. i) «Conservación», clave `LOPDP-art-10-lit-i` en `governance/artefactos/CITAS_LEGALES_VERIFICADAS.md`.
- Depende de ORG-22c, que da a cada archivo de la matriz su propio `PREFIJOS`.
