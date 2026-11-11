+++
id = "RM-25b"
titulo = "Evidencia: la validación final exige la primera, un rol dpo o auditor y dos personas distintas (contraer)"
ola = "backlog"
estado = "pendiente"
sala = "roadmap"
depende_de = ["RM-25a", "DIAG-12"]
propiedad = ["alembic/versions/20261112_evidencia_doble_validacion_exigir.py", "features/roadmap/services/evidencia_engine.py", "api/routers/roadmaps.py", "features/roadmap/services/tareas_validadas_engine.py", "tests/test_diag12_estados.py", "tests/test_rm25b_validacion_final.py"]
crea = ["alembic/versions/20261112_evidencia_doble_validacion_exigir.py", "tests/test_rm25b_validacion_final.py"]
arbitro = "pytest tests/test_rm25b_validacion_final.py tests/test_diag12_estados.py contra PostgreSQL 16 local con lopdp_app y RLS + suite completa: aprobar sin primera validación da 409 PRIMERA_VALIDACION_PENDIENTE; un implementador da 403; el mismo coordinador como validador final da 409; un INSERT o UPDATE directo a approved sin primera validación lo rechaza el CHECK; DIAG-12 no cuenta una tarea que aprobó un DPO sin primera validación; mutaciones documentadas: quitar el CHECK o quitar la condición de rol en la consulta hace fallar su prueba"
rastros = ["¤roadmap"]
+++

# RM-25b · Evidencia: la validación final exige la primera, un rol dpo o auditor y dos personas distintas (contraer)

Diseño del Arquitecto ADPA, 2026-11-11 (doble validación de la evidencia: primera validación del Coordinador, validación final del DPO o Auditor; invariante 14 de EVY), medido leyendo origin/main; no se ejecutaron pruebas. DIAG-12 entra con «dpo o auditor, distinto de quien subió»; la primera validación llega después y endurece esa consulta sin cambiar la regla.

## Entrega
- Va **después** de que RM-25a esté al 100 % y de que la revisión estable sea posterior, con el mismo brief de despliegue que DER-06b (compuerta humana del brief de revisiones).
- Migración `20261112_evidencia_doble_validacion_exigir`: `CHECK (validation_status <> 'approved' OR primera_validacion_por IS NOT NULL) NOT VALID` (deja en paz las filas históricas y exige el paso en las nuevas); `down_revision` sobre la cabeza real.
- `evidencia_engine.py`: la validación final exige que haya primera validación (409 `PRIMERA_VALIDACION_PENDIENTE`), el rol `dpo`, y que quien valida sea distinto de quien subió y de quien hizo la primera validación. El PATCH de `roadmaps.py` queda en `require_role("dpo")` con prueba de 403 para `implementador`; el rechazo puede seguir siendo de cualquiera de los dos pasos.
- `tareas_validadas_engine.py` (de DIAG-12, que debe estar `hecha`): la consulta usa los roles guardados (`primera_validacion_rol = 'coordinador'` y `validado_rol = 'dpo'`), no los roles vigentes. `tests/test_diag12_estados.py`: el caso nuevo.
- **Pendiente del CTO:** (a) `implementador` deja de validar (hoy puede; choca con el invariante 14 de EVY); (b) las evidencias `approved` antiguas sin primera validación: propuesta del Arquitecto, que no cuenten las validadas después del despliegue de esta ficha y que las anteriores cuenten marcadas como «validación simple»; (c) el rol `auditor` no existe todavía en `Role` ni en el CHECK `ck_utr_role` (lo crea ORG-22, pendiente): mientras tanto esta ficha acepta solo `dpo`, sin depender de ORG-22.

## Pruebas
Aprobar sin primera validación da 409; un `implementador` da 403; el mismo coordinador como validador final da 409; el CHECK rechaza un INSERT o UPDATE directo a `approved` sin primera validación; DIAG-12 no cuenta una tarea que aprobó un DPO sin primera validación. Mutaciones: quitar el CHECK, o quitar la condición de rol en la consulta; cada una hace fallar su prueba.

**Ajuste 2026-11-11 (decisiones del CTO, aplicadas por el Arquitecto):** (a) `implementador` sale del PATCH: queda `require_role("dpo")`, con prueba de 403. (b) En su migración, las `approved` sin primera validación quedan marcadas «pendiente de validación final» con una columna booleana `requiere_revalidacion` (no con un estado nuevo, para no romper `ESTADO_VALIDACION`); no hay promoción automática. Prueba: una evidencia aprobada antes no cuenta en DIAG-12 hasta que se revalida. La consulta de `tareas_validadas_engine.py` devuelve además `nivel_acreditado` y excluye las `requiere_revalidacion`.
