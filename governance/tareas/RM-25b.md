+++
id = "RM-25b"
titulo = "Evidencia: la validación final exige la primera, un rol dpo o auditor y dos personas distintas (contraer)"
ola = "backlog"
estado = "pendiente"
sala = "roadmap"
depende_de = ["RM-25a", "DIAG-12", "ORG-22"]
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
- `evidencia_engine.py`: la validación final exige que haya primera validación (409 `PRIMERA_VALIDACION_PENDIENTE`), un rol `dpo` o `auditor`, y que quien valida sea distinto de quien subió y de quien hizo la primera validación. El PATCH de `roadmaps.py` queda en `require_role("dpo", "auditor")`; el rechazo puede seguir siendo de cualquiera de los dos pasos.
- `tareas_validadas_engine.py` (de DIAG-12, que debe estar `hecha`): la consulta usa los roles guardados (`primera_validacion_rol = 'coordinador'` y `validado_rol IN ('dpo', 'auditor')`), no los roles vigentes. `tests/test_diag12_estados.py`: el caso nuevo.
- **Pendiente del CTO:** (a) `implementador` deja de validar (hoy puede; choca con el invariante 14 de EVY); (b) las evidencias `approved` antiguas sin primera validación: propuesta del Arquitecto, que no cuenten las validadas después del despliegue de esta ficha y que las anteriores cuenten marcadas como «validación simple»; (c) el rol `auditor` **no existe** todavía en las pertenencias (lo crea ORG-22, pendiente): por eso esta ficha depende de ORG-22; si el CTO decide validar solo con `dpo`, se quita esa dependencia y la condición `auditor`.

## Pruebas
Aprobar sin primera validación da 409; un `implementador` da 403; el mismo coordinador como validador final da 409; el CHECK rechaza un INSERT o UPDATE directo a `approved` sin primera validación; DIAG-12 no cuenta una tarea que aprobó un DPO sin primera validación. Mutaciones: quitar el CHECK, o quitar la condición de rol en la consulta; cada una hace fallar su prueba.
