# RM-25b · Evidencia: la validación final exige la primera, un rol dpo o auditor y dos personas distintas
`¤sdd` `¤roadmap` `¤arbitro`

## 1. Datos

Migración `rm25b_evidencia_exigir.py`, sin fecha (sustituye a `20261112_evidencia_doble_validacion_exigir.py`); `down_revision` = la cabeza de `main` al implementar (FUSION_ALEMBIC). Es la tercera migración de su tanda. Es el paso «contraer» de RM-25a, que añadió en `task_evidence` las columnas `primera_validacion_por`, `primera_validacion_en`, `primera_validacion_rol`, `validado_rol` y `nivel_acreditado`.

- `task_evidence.requiere_revalidacion BOOLEAN NOT NULL DEFAULT false`.
- La migración marca `requiere_revalidacion = true` en las evidencias `approved` que no tienen primera validación. **Antes imprime el recuento** de las filas que va a marcar. No cambia su `validation_status` ni promueve ninguna.
- CHECK `ck_evidence_aprobada_con_primera`: `validation_status <> 'approved' OR primera_validacion_por IS NOT NULL OR requiere_revalidacion`. Se crea `NOT VALID` y se valida en la misma migración, porque las filas históricas ya quedan cubiertas por la marca.
- CHECK `ck_evidence_validadores_distintos`: quien hace la validación final no es quien hizo la primera.
- `lopdp_app` ya tiene `UPDATE` sobre la tabla: no cambian los permisos.

## 2. API

| Método y ruta | Roles | Cambio |
| :--- | :--- | :--- |
| `PATCH /roadmaps/tasks/{task_id}/evidence/{evidence_id}` (aprobar) | `dpo`, `auditor` | antes `coordinador`, `dpo`, `implementador` |
| `PATCH …` (rechazar) | `coordinador`, `dpo`, `auditor` | el rechazo sigue pudiendo hacerse en cualquiera de los dos pasos |
| `POST …/primera-validacion` (RM-25a) | `coordinador` | sin cambio |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | un `implementador` intenta validar |
| 409 | `PRIMERA_VALIDACION_PENDIENTE` | aprobar una evidencia sin primera validación |
| 409 | `VALIDADOR_REPETIDO` | quien aprueba es quien subió la evidencia o quien hizo la primera validación |

Los códigos se registran en el catálogo de la sala roadmap.

## 3. Reglas

- **R1 · Dos pasos.** La validación final solo procede sobre una evidencia con primera validación registrada.
- **R2 · Roles.** La primera validación es del `coordinador`; la final, del `dpo` o del `auditor`. El `implementador` deja de validar (decisión del CTO, 2026-11-11).
- **R3 · Tres personas distintas.** Quien sube, quien hace la primera validación y quien hace la final son personas distintas. Lo exigen el servicio y los CHECK de la base.
- **R4 · Sin validación simple.** Una evidencia con una sola validación no suma al nivel de ningún control. Las `approved` anteriores a esta ficha quedan con `requiere_revalidacion` y se muestran como «pendiente de validación final». No hay promoción automática: se revalidan por los dos pasos, y al hacerlo se quita la marca.
- **R5 · DIAG-12 cuenta por los roles guardados.** `tareas_validadas_engine.py` cuenta una tarea solo si su evidencia tiene `primera_validacion_rol = 'coordinador'`, `validado_rol IN ('dpo', 'auditor')` y no tiene `requiere_revalidacion`. Usa los roles guardados en la fila, no los que la persona tenga hoy. Devuelve además `nivel_acreditado`.
- **R6 · El nivel.** El control toma el máximo entre el nivel del diagnóstico real y el `nivel_acreditado` (0 a 4) que fija el DPO o el auditor en la validación final.
- **R7 · Despliegue.** Va después de que RM-25a esté desplegada y de que la revisión estable sea posterior. El brief de despliegue sigue el de DER-06b e incluye el recuento de evidencias que quedarán por revalidar.
- **R-ADPA · Ortogonalidad ZERAG (`RM-25b`).** Todo dentro de la sala roadmap.

## 4. Interfaz

Sin pantalla nueva en esta ficha. Las evidencias marcadas se listan como «pendiente de validación final»; si hace falta cambiar un texto o un botón, pasa por UX/UI en una ficha de frontend.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una evidencia sin primera validación, **cuando** el DPO la aprueba, **entonces** 409 `PRIMERA_VALIDACION_PENDIENTE`. | `test_final_exige_primera` |
| **Dado** un `implementador`, **cuando** valida, **entonces** 403. Mutación: devolverle el rol hace fallar la prueba. | `test_implementador_no_valida` |
| **Dado** quien hizo la primera validación, o quien subió la evidencia, **cuando** hace la final, **entonces** 409 `VALIDADOR_REPETIDO`. | `test_tres_personas_distintas` |
| **Dado** un `INSERT` o `UPDATE` directo a `approved` sin primera validación y sin la marca, **entonces** lo rechaza el CHECK. Mutación: quitar el CHECK hace fallar la prueba. | `test_check_aprobada_con_primera` |
| **Dado** evidencias `approved` anteriores sin primera validación, **cuando** corre la migración, **entonces** quedan con `requiere_revalidacion`, su estado no cambia y el recuento impreso coincide. Mutación: promoverlas hace fallar la prueba. | `test_migracion_marca_sin_promover` |
| **Dado** una tarea cuya evidencia aprobó un DPO sin primera validación, o que tiene la marca, **entonces** DIAG-12 no la cuenta. Mutación: quitar la condición de rol de la consulta hace fallar la prueba. | `test_diag12_solo_doble_validacion` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_evidencia_exigir` |

En `tests/test_rm25b_validacion_final.py` y `tests/test_diag12_estados.py`, contra el PostgreSQL 16 local con `lopdp_app`, sin `import yaml`.

## 6. Trazabilidad

- Ficha: `governance/tareas/RM-25b.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Diseño del Arquitecto ADPA del 2026-11-11 y decisiones del CTO del mismo día. Invariante 14 de EVYDENTIA.
- Depende de RM-25a y DIAG-12 (hechas) y de ORG-22 (en curso), que crea el rol `auditor`. Orden con RET-02, que también posee `api/routers/roadmaps.py` y `features/roadmap/services/evidencia_engine.py`: RM-25b va después.
- **Propiedad que falta en la ficha**, medida en `origin/main` 4eca5af2: el archivo del catálogo de errores de la sala (`features/roadmap/domain/errores.py#RM-25b`, por sembrar) y `tests/matriz/RM-25b.py` (crea), porque cambian los roles de una ruta. La migración cambia de nombre: hay que actualizar `propiedad` y `crea`.
- **Bloqueo del árbitro:** `scripts/verificar_especificaciones.py` rechaza el sufijo «b». Esta especificación no pasa hasta que el árbitro admita sufijos.
