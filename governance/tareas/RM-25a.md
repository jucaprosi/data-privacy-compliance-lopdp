+++
id = "RM-25a"
titulo = "Evidencia con primera validación del Coordinador: columnas, ruta y rol guardado (expandir, sin exigir)"
ola = "backlog"
estado = "pendiente"
sala = "roadmap"
depende_de = ["ADPA-04", "ENT-02", "RM-00", "RM-01", "RM-17", "RM-19", "SEC-04"]
propiedad = ["alembic/versions/20261111_evidencia_doble_validacion.py", "features/roadmap/services/evidencia_doble_validacion_engine.py", "features/roadmap/services/evidencia_engine.py", "features/roadmap/roadmap_service.py#RM-25a", "features/roadmap/domain/models.py", "api/routers/roadmaps_validacion.py", "main.py#RM-25a", "tests/test_rm25a_primera_validacion.py"]
crea = ["alembic/versions/20261111_evidencia_doble_validacion.py", "features/roadmap/services/evidencia_doble_validacion_engine.py", "api/routers/roadmaps_validacion.py", "tests/test_rm25a_primera_validacion.py"]
arbitro = "pytest tests/test_rm25a_primera_validacion.py contra un PostgreSQL 16 local en contenedor con lopdp_app y RLS + suite completa: el coordinador registra la primera validación (200), quien subió la evidencia no puede (409), un dpo o un implementador no pueden (403) y el validado_rol queda guardado; mutación documentada: quitar require_role hace fallar el 403"
rastros = ["¤roadmap"]
+++

# RM-25a · Evidencia con primera validación del Coordinador: columnas, ruta y rol guardado (expandir, sin exigir)

Diseño del Arquitecto ADPA, 2026-11-11 (doble validación de la evidencia: primera validación del Coordinador, validación final del DPO o Auditor; invariante 14 de EVY), medido leyendo origin/main; no se ejecutaron pruebas. DIAG-12 entra con «dpo o auditor, distinto de quien subió»; la primera validación llega después y endurece esa consulta sin cambiar la regla.

## Entrega
- **Migración** `20261111_evidencia_doble_validacion` (id de 32 caracteres como máximo; **de una en una con FUSION_ALEMBIC**: su `down_revision` es la cabeza real de `origin/main` al empezar, medida con `ScriptDirectory.get_heads()`): columnas **nulas** en `task_evidence`: `primera_validacion_por` (FK `users`), `primera_validacion_en`, `primera_validacion_rol` y `validado_rol`. `lopdp_app` recibe UPDATE de esas columnas si los permisos van por columna (medirlo). No se añade un estado nuevo: `validation_status` es String con CHECK y el `ESTADO_VALIDACION` del frontend no cambia.
- `features/roadmap/services/evidencia_doble_validacion_engine.py` (nuevo), exportado por `roadmap_service.py#RM-25a`: `registrar_primera_validacion` (solo `coordinador`, distinto de quien subió) y la validación final, que guarda `validado_rol`.
- `evidencia_engine.py:82` (validación en un solo paso): el PATCH viejo sigue funcionando y ya rellena `validado_rol`. **Todavía no exige nada.**
- `api/routers/roadmaps_validacion.py` (nuevo): `POST /tasks/{id}/evidence/{eid}/primera-validacion` con `require_role("coordinador")`; el registro del router es la línea de `main.py#RM-25a`.
- `features/roadmap/domain/models.py`: campos opcionales.
- Ninguna ficha viva posee `evidencia_engine.py`, `roadmaps.py` ni `EvidenciaPanel.tsx`; la única de la compuerta es ORG-15 por su sección. Mide de nuevo al repartir, junto con `domain/models.py`.

## Pruebas
El coordinador registra la primera validación (200); quien subió la evidencia no puede (409); un `dpo` o un `implementador` no pueden (403); el `validado_rol` queda guardado. Mutación: quitar `require_role` hace fallar el 403.
