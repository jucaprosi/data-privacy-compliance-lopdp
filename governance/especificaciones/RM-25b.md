# RM-25b · Evidencia: la validación final exige la primera, un rol dpo o auditor y dos personas distintas
`¤sdd` `¤roadmap` `¤arbitro`

## 1. Datos

Migración `alembic/versions/rm25b_evidencia_exigir.py`, de la sala `roadmap` (`alembic/salas.py`, CI-28). Es la primera migración de esa sala: `down_revision = BASE_COMUN` (`"ret02_clave_objeto"`) y `branch_labels = ("roadmap",)`. Las siguientes migraciones de `roadmap` cuelgan de `roadmap@head`. Es el paso «contraer» de RM-25a, que añadió en `task_evidence` las columnas `primera_validacion_por`, `primera_validacion_en`, `primera_validacion_rol`, `validado_rol` y `nivel_acreditado`.

- `task_evidence.requiere_revalidacion BOOLEAN NOT NULL DEFAULT false`.
- La migración marca `requiere_revalidacion = true` en las evidencias `approved` que no tienen primera validación. **Antes imprime el recuento** de las filas que va a marcar. No cambia su `validation_status` ni promueve ninguna.
- CHECK `ck_evidence_aprobada_con_primera`: `validation_status <> 'approved' OR primera_validacion_por IS NOT NULL OR requiere_revalidacion`. Se crea `NOT VALID` y se valida en la misma migración, porque las filas históricas ya quedan cubiertas por la marca.
- CHECK `ck_evidence_validadores_distintos`: quien hace la validación final no es quien hizo la primera.
- `lopdp_app` ya tiene `UPDATE` sobre la tabla: no cambian los permisos.

## 2. API

| Método y ruta | Roles | Cambio |
| :--- | :--- | :--- |
| `PATCH /roadmaps/tasks/{task_id}/evidence/{evidence_id}` (dependencia de roles y matriz) | `coordinador`, `dpo`, `auditor` | antes `coordinador`, `dpo`, `implementador`; la ruta no se parte en aprobar y rechazar, porque RM-27 consume ese contrato |
| `PATCH …` (aprobar) | `dpo`, `auditor` | el motor (`evidencia_engine.py`) rechaza al `coordinador` |
| `PATCH …` (rechazar) | `coordinador`, `dpo`, `auditor` | el rechazo sigue pudiendo hacerse en cualquiera de los dos pasos |
| `POST …/primera-validacion` (RM-25a) | `coordinador` | acepta también una evidencia `approved` con `requiere_revalidacion` (R4); el resto, sin cambio |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | un `implementador` intenta validar |
| 403 | `ROL_SIN_VALIDACION_FINAL` | un `coordinador` intenta aprobar; se comprueba antes que los dos 409 |
| 409 | `PRIMERA_VALIDACION_PENDIENTE` | aprobar una evidencia sin primera validación |
| 409 | `VALIDADOR_REPETIDO` | quien aprueba es quien subió la evidencia o quien hizo la primera validación |

Los códigos se registran en la sección `#RM-25b` del catálogo de la sala (`features/roadmap/domain/errores.py`). Al aprobar, el motor comprueba en este orden: rol (`ROL_SIN_VALIDACION_FINAL`), primera validación (`PRIMERA_VALIDACION_PENDIENTE`) y personas distintas (`VALIDADOR_REPETIDO`). El docstring de `tests/matriz/RM-25b.py` explica que la matriz da paso al `coordinador` por el rechazo y que el motor le impide aprobar.

## 3. Reglas

- **R1 · Dos pasos.** La validación final solo procede sobre una evidencia con primera validación registrada.
- **R2 · Roles.** La primera validación es del `coordinador`; la final, del `dpo` o del `auditor`. El `implementador` deja de validar (decisión del CTO, 2026-11-11).
- **R3 · Tres personas distintas.** Quien sube, quien hace la primera validación y quien hace la final son personas distintas. Lo exigen el servicio y los CHECK de la base.
- **R4 · Sin validación simple.** Una evidencia con una sola validación no suma al nivel de ningún control. Las `approved` anteriores a esta ficha quedan con `requiere_revalidacion` y se muestran como «pendiente de validación final». No hay promoción automática: se revalidan por los dos pasos, y al hacerlo se quita la marca.
- **R5 · DIAG-12 cuenta por los roles guardados.** `tareas_validadas_engine.py` cuenta una tarea solo si su evidencia tiene `primera_validacion_rol = 'coordinador'`, `validado_rol IN ('dpo', 'auditor')` y no tiene `requiere_revalidacion`. Usa los roles guardados en la fila, no los que la persona tenga hoy. Devuelve además `nivel_acreditado`.
- **R6 · El nivel.** El control toma el máximo entre el nivel del diagnóstico real y el `nivel_acreditado` (0 a 4) que fija el DPO o el auditor en la validación final. `TaskEvidenceValidationRequest` (`features/roadmap/domain/models.py`) añade `nivel_acreditado: int | None` (0 a 4); al aprobar es obligatorio y sin él la petición se rechaza (422); al rechazar se ignora.
- **R4b · Revalidar.** Una evidencia `approved` con `requiere_revalidacion` admite de nuevo la primera validación del `coordinador` (`evidencia_doble_validacion_engine.py`, RM-25a) y después la final; al aprobarla, la marca se quita.
- **R3b · Lecturas confirmadas (2026-11-19).** `ck_evidence_validadores_distintos` solo se exige con `validation_status = 'approved'`: quien hizo la primera validación puede rechazar después. Al aprobar, cualquier rol que no sea `dpo` ni `auditor`, también `rol = None` en llamadas internas, recibe 403 `ROL_SIN_VALIDACION_FINAL`. Al aprobar, quien subió la evidencia recibe 409 `VALIDADOR_REPETIDO`; en el rechazo se conserva el cuatro ojos anterior.
- **R7 · Despliegue.** Va después de que RM-25a esté desplegada y de que la revisión estable sea posterior. El brief de despliegue sigue el de DER-06b e incluye el recuento de evidencias que quedarán por revalidar.
- **R-ADPA · Ortogonalidad ZERAG (`RM-25b`).** Todo dentro de la sala roadmap.

## 4. Interfaz

Sin pantalla nueva en esta ficha. Las evidencias marcadas se listan como «pendiente de validación final»; si hace falta cambiar un texto o un botón, pasa por UX/UI en una ficha de frontend.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una evidencia sin primera validación, **cuando** el DPO la aprueba, **entonces** 409 `PRIMERA_VALIDACION_PENDIENTE`. | `test_final_exige_primera` |
| **Dado** un `implementador`, **cuando** valida, **entonces** 403. Mutación: devolverle el rol hace fallar la prueba. | `test_implementador_no_valida` |
| **Dado** un `coordinador`, **cuando** aprueba, **entonces** 403 `ROL_SIN_VALIDACION_FINAL`, antes de cualquier 409. Mutación: quitar la comprobación hace fallar la prueba. | `test_coordinador_no_aprueba` |
| **Dado** quien hizo la primera validación, o quien subió la evidencia, **cuando** hace la final, **entonces** 409 `VALIDADOR_REPETIDO`. | `test_tres_personas_distintas` |
| **Dado** un `INSERT` o `UPDATE` directo a `approved` sin primera validación y sin la marca, **entonces** lo rechaza el CHECK. Mutación: quitar el CHECK hace fallar la prueba. | `test_check_aprobada_con_primera` |
| **Dado** evidencias `approved` anteriores sin primera validación, **cuando** corre la migración, **entonces** quedan con `requiere_revalidacion`, su estado no cambia y el recuento impreso coincide. Mutación: promoverlas hace fallar la prueba. | `test_migracion_marca_sin_promover` |
| **Dado** una tarea cuya evidencia aprobó un DPO sin primera validación, o que tiene la marca, **entonces** DIAG-12 no la cuenta. Mutación: quitar la condición de rol de la consulta hace fallar la prueba. | `test_diag12_solo_doble_validacion` |
| **Dado** una evidencia `approved` con `requiere_revalidacion`, **cuando** el coordinador hace la primera validación y el DPO la final, **entonces** queda aprobada y sin la marca. Mutación: rechazar la primera validación sobre `approved` hace fallar la prueba. | `test_revalidar_aprobada_marcada` |
| **Dado** la validación final sin `nivel_acreditado`, o con un valor fuera de 0 a 4, **entonces** 422; con un valor válido, DIAG-12 lo devuelve. | `test_final_exige_nivel_acreditado` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_evidencia_exigir` |

En `tests/test_rm25b_validacion_final.py` y `tests/test_diag12_estados.py`, contra el PostgreSQL 16 local con `lopdp_app`, sin `import yaml`.

## 6. Trazabilidad

- Ficha: `governance/tareas/RM-25b.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Diseño del Arquitecto ADPA del 2026-11-11 y decisiones del CTO del mismo día. Invariante 14 de EVYDENTIA.
- Depende de RM-25a y DIAG-12 (hechas) y de ORG-22 (en curso), que crea el rol `auditor`. Orden con RET-02, que también posee `api/routers/roadmaps.py` y `features/roadmap/services/evidencia_engine.py`: RM-25b va después.
- **Propiedad**, medida en `origin/main` 020bc051: la sección `features/roadmap/domain/errores.py#RM-25b`, `tests/matriz/RM-25b.py` y la migración `alembic/versions/rm25b_evidencia_exigir.py` (las dos últimas también en `crea`), más las pruebas de fichas hechas que fijan la regla anterior. Ampliada otra vez el 2026-11-19 con `tests/matriz/roles/auditor.py#RM-25b`, `tests/test_roadmap_cierre_recordatorios.py`, `tests/test_bib_208_fichas.py`, `evidencia_doble_validacion_engine.py` y `features/roadmap/domain/models.py`.
