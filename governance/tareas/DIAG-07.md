+++
id = "DIAG-07"
titulo = "Responden el administrador y los encargados del diagnóstico; el DPO revisa con la grilla declarado/verificado, objeta y sella"
ola = "D"
estado = "pendiente"
sala = "diagnostico, frontend"
depende_de = ["DIAG-04", "DIAG-05"]
propiedad = ["alembic/versions/20261101_diagnostico_objeciones.py", "features/diagnostico/services/objeciones_engine.py", "features/diagnostico/diagnostico_service.py#DIAG-07", "api/routers/diagnostico_respuestas.py#DIAG-07", "api/routers/diagnostico_resultados.py#DIAG-07", "tests/test_diagnostico_quien_responde.py", "tests/matriz/DIAG-07.py", "frontend/src/components/diagnostico/GrillaRevision.tsx", "frontend/src/lib/diagnostico/objeciones.ts", "frontend/tests/diagnostico/revision.spec.ts"]
arbitro = "pytest tests/test_diagnostico_quien_responde.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + vigilantes + Playwright de frontend/tests/diagnostico + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤diagnostico", "¤dpo-independencia"]
+++

# DIAG-07 · Responden el administrador y los encargados; el DPO revisa, objeta y sella

**Decisión del propietario (2026-10-28), que sustituye a la de DIAG-03 del 2026-10-27.** El diagnóstico lo conduce el DPO, pero **no responde**: responde el `admin_organizacion` o la persona que él designe como encargada de un dominio (DIAG-04). El diagnóstico ocurre antes de implementar la LOPDP, cuando aún no hay responsables de área: por eso el encargado es cualquier persona con rol vigente, no un rol concreto. El DPO revisa lo declarado con la grilla «declarado / verificado», puede **objetar** una respuesta y es el único que **sella**. Fundamento: el delegado supervisa y no ejecuta (Doctrina 2, `INV_LOPDP_DPO_INDEPENDENCE`; Reglamento del Delegado, Res. SPDP-SPD-2025-0028-R).

**Contrato:** `governance/especificaciones/DIAG-07.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- `PUT /diagnostico/respuestas` (sección `#DIAG-07` del router, que DIAG-05 ya reescribe): escriben `admin_organizacion` en cualquier dimensión y el encargado asignado (DIAG-04) en las suyas; `dpo`, `implementador` y `coordinador` reciben 403. Sus filas de la matriz en `tests/matriz/DIAG-07.py`.
- **Objeciones:** el `dpo` objeta una respuesta con motivo antes de sellar; la respuesta queda `objetada` hasta que el respondiente la vuelve a guardar. No se puede sellar con objeciones abiertas.
- **Grilla de revisión** (`GrillaRevision.tsx`): por pregunta, lo declarado, la evidencia, el nivel que el DPO verifica (`nivel_sellado`) y la objeción; solo el `dpo` edita la columna de verificación.
- Nota en DIAG-03: su decisión del 2026-10-27 queda sustituida por esta.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10: la que se fusione después se vuelve a encadenar). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- El `dpo` recibe 403 al guardar respuestas y 200 al objetar y sellar; el administrador guarda en cualquier dimensión; el encargado solo en la suya (403 fuera de ella).
- No se sella con una objeción abierta (409).
- Mutación documentada: dejar que el `dpo` escriba respuestas y comprobar que la prueba del 403 falla.

## Límites
- No cambia el scoring ni el sellado (DIAG-03) salvo la condición de «sin objeciones abiertas».
- No toca `DiagnosticCanvas.tsx` (DIAG-05 y EVI-01): la grilla es un componente nuevo.
