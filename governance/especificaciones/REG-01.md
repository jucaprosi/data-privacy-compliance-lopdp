# REG-01 · Paquete normativo como dato
`¤sdd` `¤regulation-code` `¤plataforma`

## 1. Datos

Migración `*_paquetes_normativos`. Tablas **globales** (sin `tenant_id`; no son datos de ningún cliente), escritura solo del operador de la plataforma (`operadores_plataforma`, ORG-09):

**`paquetes_normativos`**: `id VARCHAR PK, codigo VARCHAR(16) UNIQUE ('LOPDP', 'NIIF18'), nombre, version VARCHAR(16), estado VARCHAR(10) CHECK (estado IN ('borrador','publicado','retirado')), publicado_en TIMESTAMPTZ NULL, creado_por, creado_en`. Un `codigo` tiene a lo sumo un `publicado`.

**`parametros_normativos`**: `id, paquete_id, clave VARCHAR(64), valor TEXT, unidad VARCHAR(10) NULL CHECK (unidad IN ('habiles','calendario')), articulo TEXT, fuente_url TEXT, verificado BOOLEAN NOT NULL DEFAULT false, UNIQUE (paquete_id, clave)`. Claves mínimas: `plazo_derechos_dias`, `plazo_vulneracion_encargado_dias`, `plazo_vulneracion_autoridad_dias`, `plazo_vulneracion_titulares_dias`, `autoridad`, `canal_notificacion`.

**`requisitos_normativos`**: `id, paquete_id, codigo VARCHAR(16), articulo, texto, obligatoriedad VARCHAR(12) CHECK (IN ('obligatorio','recomendado')), aplica_a TEXT[] (responsable, encargado, publico, privado)`.

**`controles_comunes`**: `id, codigo VARCHAR(5) ('P1'..'P80'), dimension VARCHAR(3), ponderacion NUMERIC(4,2)`; **`requisito_control`**: `(requisito_id, control_id)`.

`lopdp_app`: `SELECT` en todas; `INSERT/UPDATE` solo en una sesión con `app.current_operador_id` fijado (misma técnica que ORG-09).

## 2. API

Router `api/routers/paquetes_normativos.py`, prefijo `/plataforma/paquetes`; escritura exige operador de la plataforma (`plataforma_service`), lectura cualquier usuario autenticado.

| Método y ruta | Entrada | Respuesta |
| :--- | :--- | :--- |
| `GET /plataforma/paquetes` | — | `200 {"paquetes": [Paquete]}` |
| `GET /plataforma/paquetes/{codigo}/parametros` | — | `200 {"parametros": [Parametro]}` del paquete `publicado` |
| `POST /plataforma/paquetes/{codigo}/versiones` | `{version}` | `201 Paquete` en `borrador`, copia de la publicada |
| `PUT /plataforma/paquetes/{id}/parametros/{clave}` | `{valor, unidad?, articulo, fuente_url, verificado}` | `200 Parametro` |
| `POST /plataforma/paquetes/{id}/publicar` | — | `200 {"paquete": Paquete, "impacto": {"plantillas": [str], "organizaciones": int}}` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | `NO_ES_OPERADOR` | escritura sin operador de plataforma |
| 409 | `PARAMETRO_NO_VERIFICADO` | publicar con algún parámetro `verificado = false` |
| 409 | `PAQUETE_NO_BORRADOR` | editar o publicar uno que no está en `borrador` |
| 422 | `UNIDAD_REQUERIDA` | un `plazo_*` sin `unidad` |

## 3. Reglas

- **R1 · Verificado o no se activa.** `publicar(p) ⇒ ∀ x ∈ parametros(p) : x.verificado` (los valores con (*) no entran a producción; LEG-03 los verifica).
- **R2 · Versión inmutable.** Un paquete `publicado` no se edita; cambiarlo es crear una versión nueva y publicarla; la anterior pasa a `retirado`. Los resultados sellados conservan `version_normativa` (DIAG-03) y no se recalculan (`INV_LOPDP_REGULATION_AS_CODE_DIFF`).
- **R3 · Diff de impacto.** Al publicar, `impacto` lista las plantillas de la Biblioteca cuyo `paquete_normativo` coincide (`biblioteca_service`) y cuenta las organizaciones con resultados de la versión anterior.
- **R4 · Unidad de plazos.** Toda clave `plazo_*` lleva `unidad`; el cálculo de vencimientos (derechos, vulneraciones) lee `valor` y `unidad` del paquete publicado y nunca una constante del código.
- **R5 · Dos paquetes.** `LOPDP` y `NIIF18` conviven; el selector «Normativa» del frontend lee `GET /plataforma/paquetes`.

## 4. Interfaz

Configuración › Paquetes normativos (`frontend/src/app/plataforma/paquetes/`), visible solo al operador: lista de paquetes y versiones; editor de parámetros con artículo, fuente y casilla «Verificado»; botón «Publicar» deshabilitado con la lista de parámetros sin verificar; vista previa del impacto.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un borrador con un parámetro `verificado = false`, **cuando** se publica, **entonces** 409 `PARAMETRO_NO_VERIFICADO`. Mutación: publicar sin la comprobación hace fallar la prueba. | `test_publicar_exige_verificados` |
| **Dado** `plazo_derechos_dias` sin unidad, **entonces** 422 `UNIDAD_REQUERIDA`. | `test_plazo_con_unidad` |
| **Dado** un paquete publicado, **cuando** se edita, **entonces** 409 `PAQUETE_NO_BORRADOR`; **y** crear una versión copia sus parámetros. | `test_version_inmutable` |
| **Dado** un usuario sin operador, **cuando** escribe, **entonces** 403; **y** puede leer. | `test_solo_operador_escribe` |
| **Dado** la pantalla con dos parámetros sin verificar, **entonces** «Publicar» está deshabilitado y los lista. | `frontend/tests/plataforma/paquetes.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/REG-01.md` (backlog; espera a LEG-03). PRD: apartado 6 («Paquete normativo como dato»), criterio 18. Invariante: `INV_LOPDP_REGULATION_AS_CODE_DIFF`. Contraste: O-5, O-9, D-9.
- Decisión abierta: las preguntas del assessment (banco de RM-19) y las plantillas se incorporan al paquete en una tarea posterior; aquí entran parámetros, requisitos y controles comunes.
