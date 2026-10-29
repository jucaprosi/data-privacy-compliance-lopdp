# DPO-02 · Informe anual del DPO e inscripción ante la SPDP
`¤sdd` `¤dpo-cockpit` `¤dpo-informe-anual`

## 1. Datos

Migración `20261030_dpo_inscripcion`, dos tablas por organización, ambas append-only.

**`dpo_inscripciones`**

| Columna | Tipo | Restricción |
| :--- | :--- | :--- |
| `id` | `VARCHAR` | PK, UUID v4 del servidor |
| `tenant_id` | `VARCHAR` | `NOT NULL REFERENCES tenants(id)` |
| `inscrito` | `BOOLEAN` | `NOT NULL` |
| `fecha_inscripcion` | `DATE` | `NULL` |
| `numero_tramite` | `VARCHAR(64)` | `NULL` |
| `registrado_por` | `VARCHAR` | `NOT NULL` (token) |
| `registrado_en` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` |

`CHECK (inscrito = false OR (fecha_inscripcion IS NOT NULL AND numero_tramite IS NOT NULL))`. El estado vigente es la fila de mayor `registrado_en`.

**`dpo_informes_anuales`**

| Columna | Tipo | Restricción |
| :--- | :--- | :--- |
| `id` | `VARCHAR` | PK |
| `tenant_id` | `VARCHAR` | `NOT NULL REFERENCES tenants(id)` |
| `anio` | `SMALLINT` | `NOT NULL CHECK (anio >= 2021)` |
| `generado_por` | `VARCHAR` | `NOT NULL` (token) |
| `generado_en` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` |
| `contenido` | `JSONB` | `NOT NULL` (forma en el apartado 2) |
| `huella_bitacora` | `VARCHAR(64)` | `NULL`; `sha256_hash` de la última entrada del año, o nulo si no hubo |

RLS `ENABLE` y `FORCE` por `tenant_id` en ambas. `lopdp_app`: solo `SELECT` e `INSERT` (un `UPDATE` o `DELETE` falla con 42501).

## 2. API

Rutas nuevas en `api/routers/dpo_informe_anual.py`, prefijo `/dpo`.

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `POST /dpo/informes-anuales` | `dpo` | `{"anio": int}` | `201 InformeAnual` |
| `GET /dpo/informes-anuales?anio=` | `dpo`, `admin_organizacion`, `coordinador`, `implementador` | `anio` opcional | `200 {"informes": [InformeAnual]}`, más reciente primero |
| `GET /dpo/informes-anuales/{id}/descarga` | los mismos | — | `200 application/pdf`, `Content-Disposition: attachment; filename="informe-dpo-<anio>.pdf"` |
| `GET /dpo/inscripcion` | `dpo`, `admin_organizacion` | — | `200 {"vigente": Inscripcion \| null, "historial": [Inscripcion]}` |
| `POST /dpo/inscripcion` | `admin_organizacion` | `{"inscrito": bool, "fecha_inscripcion": "YYYY-MM-DD" \| null, "numero_tramite": str \| null}` | `201 Inscripcion` |

`InformeAnual` = `{id, anio, generado_en, generado_por, huella_bitacora, contenido: {total: int, por_tipo: {<TipoDictamenDPO>: int}, vinculantes: int, primera_fecha: str | null, ultima_fecha: str | null}}`. `por_tipo` lleva siempre las siete claves de `TipoDictamenDPO`, con 0 si no hubo.

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla; cualquiera que no sea `dpo` al generar |
| 404 | `INFORME_NO_ENCONTRADO` | `id` inexistente en la organización |
| 422 | `INSCRIPCION_INCOMPLETA` | `inscrito = true` sin fecha o sin número de trámite |
| 422 | `ANIO_FUERA_DE_RANGO` | `anio < 2021` o mayor que el año en curso |

## 3. Reglas

- **R1 · Año.** Una entrada de la bitácora pertenece al año `a` si `fecha_emision ∈ [a-01-01 00:00, (a+1)-01-01 00:00)` en `America/Guayaquil`.
- **R2 · Contenido.** `total = |E_a|`; `por_tipo[t] = |{e ∈ E_a : e.tipo = t}|`; `vinculantes = |{e ∈ E_a : e.es_vinculante}|`; `primera_fecha` y `ultima_fecha` = mínimo y máximo de `fecha_emision` en `E_a`. Solo entradas de la organización del token.
- **R3 · Huella.** `huella_bitacora` = `sha256_hash` de la entrada de `E_a` con mayor `fecha_emision`; va impresa en el pie del PDF.
- **R4 · Regenerar.** Generar otra vez el mismo año crea un informe nuevo; los anteriores no se modifican.
- **R5 · Sin plazos.** No calcula vencimientos ni obligaciones con fecha (aplazados por decisión del propietario; LEG-03, REG-01).
- **R6 · Auditoría.** `registrar_evento(entity_type='dpo_informe_anual' | 'dpo_inscripcion', action='generado' | 'registrado')`.

## 4. Interfaz

`DpoCockpitModule.tsx` suma dos pestañas:

- **Informe anual:** selector de año (2021 al año en curso), botón «Generar informe» visible solo para `dpo`, lista de informes del año con fecha, autor y «Descargar». Sin informes: «Aún no se ha generado el informe de este año».
- **Inscripción SPDP:** estado vigente («Inscrito el <fecha>, trámite <número>» o «No inscrito») e historial. Formulario solo para `admin_organizacion`; el número de trámite y la fecha solo se piden si marca «Inscrito».

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** 4 entradas en 2025 y 2 en 2026, **cuando** el `dpo` genera el informe 2025, **entonces** `total = 4` y `por_tipo` suma 4. Mutación: incluir otro año hace fallar la prueba. | `test_informe_solo_del_anio` |
| **Dado** una entrada del 31-dic-2025 a las 23:30 de Guayaquil, **entonces** cuenta en 2025, no en 2026. | `test_limite_de_anio_guayaquil` |
| **Dado** un `coordinador`, **cuando** pide generar, **entonces** 403; **y** puede listar y descargar. | `test_solo_dpo_genera` |
| **Dado** `inscrito = true` sin número de trámite, **entonces** 422 `INSCRIPCION_INCOMPLETA`. | `test_inscripcion_incompleta` |
| **Dado** una inscripción registrada, **cuando** `lopdp_app` intenta `UPDATE` o `DELETE`, **entonces** 42501. | `test_inscripcion_append_only` |
| **Dado** datos de la organización A, **cuando** se consulta en el contexto de B con `lopdp_app`, **entonces** 0 filas. | `test_rls_dpo_02` |
| **Dado** el módulo DPO abierto por un `admin_organizacion`, **entonces** ve el formulario de inscripción y no ve «Generar informe». | `frontend/tests/dpo/pestanas.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/DPO-02.md`. PRD: Módulo 4 (panel del DPO, informe anual, inscripción). Invariante: `INV_LOPDP_DPO_INDEPENDENCE` (el DPO genera su propio informe; no edita ni aprueba nada de la organización).
- Datos de origen: tabla `dpo_dictamenes` (DPO-01, `20261027_dpo_bitacora`), tipos de `features/dpo_cockpit/domain/models.py`.
- Decisión abierta: datos exactos que la SPDP pide para la inscripción (*); se verifican en LEG-03.
