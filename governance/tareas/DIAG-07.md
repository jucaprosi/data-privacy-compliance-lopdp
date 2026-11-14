+++
id = "DIAG-07"
titulo = "Responden el administrador y los encargados del diagnóstico; el DPO revisa con la grilla declarado/verificado, objeta y sella"
ola = "D"
estado = "en_curso"
sala = "diagnostico, frontend"
depende_de = ["DIAG-04", "DIAG-05", "ADPA-05", "ADPA-06", "ADPA-07", "ADPA-11", "DIAG-07a", "DIAG-07b", "DIAG-14", "EVI-01b", "EVI-02", "FE-07", "FE-16", "DIAG-09", "DIAG-03", "TEST-02", "DIAG-11", "FE-26", "EVI-01"]
propiedad = ["alembic/versions/20261101_diagnostico_objeciones.py", "features/diagnostico/services/objeciones_engine.py", "features/diagnostico/diagnostico_service.py#DIAG-07", "api/routers/diagnostico_respuestas.py", "api/routers/diagnostico_resultados.py", "tests/test_diagnostico_quien_responde.py", "tests/matriz/DIAG-07.py", "frontend/src/components/diagnostico/GrillaRevision.tsx", "frontend/src/lib/diagnostico/objeciones.ts", "frontend/tests/diagnostico/revision.spec.ts", "features/diagnostico/domain/errores.py#DIAG-07", "app_core/pasillo/diagnostico.py#DIAG-07", "tests/test_diagnostico_respuestas.py", "tests/test_diagnostico_resultados.py", "frontend/tests/diagnostico/solo-dpo.spec.ts", "frontend/src/lib/diagnostico/roles.ts", "app_core/pasillo/roadmap.py#DIAG-07", "app_core/pasillo/organizacion.py#DIAG-07", "app_core/pasillo/regulacion_rag.py#DIAG-07", "frontend/src/components/DiagnosticCanvas.tsx#DIAG-07", "frontend/src/components/layout/menus/index.ts#DIAG-07", "frontend/src/components/layout/pantallas/index.tsx#DIAG-07", "frontend/src/lib/diagnostico/clienteRespuestas.ts", "frontend/tests/diagnostico/simulador.ts", "frontend/tests/diagnostico/escala.spec.ts", "frontend/tests/diagnostico/escala-activa.spec.ts", "frontend/tests/diagnostico/no-aplica.spec.ts", "frontend/tests/diagnostico/persistencia.spec.ts", "frontend/tests/diagnostico/prueba-y-real.spec.ts", "frontend/tests/diagnostico/sellado.spec.ts", "frontend/tests/diagnostico/guardar-como-admin.spec.ts", "frontend/src/components/diagnostico/NotaSoloDpo.tsx", "api/routers/preanalisis.py", "frontend/src/lib/preanalisis/cliente.ts", "frontend/src/components/preanalisis/PanelPreanalisis.tsx", "frontend/tests/assessmentDashboard.spec.ts", "frontend/tests/pmv/sin-subida.spec.ts", "frontend/tests/pmv/sin-subida-activa.spec.ts", "frontend/tests/purga/purga-normativa-activa.spec.ts", "frontend/src/components/DiagnosticCanvas.tsx#EVI-01", "frontend/src/components/DiagnosticCanvas.tsx#DIAG-05"]
crea = ["frontend/tests/diagnostico/guardar-como-admin.spec.ts"]
arbitro = "pytest tests/test_diagnostico_quien_responde.py contra un PostgreSQL 16 local en contenedor (incluido RLS con lopdp_app) + suite completa + vigilantes + Playwright de frontend/tests/diagnostico + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤diagnostico", "¤dpo-independencia"]
+++

# DIAG-07 · Responden el administrador y los encargados; el DPO revisa, objeta y sella

**Decisión del propietario (2026-10-28), que sustituye a la de DIAG-03 del 2026-10-27.** El diagnóstico lo conduce el DPO, pero **no responde**: responde el `admin_organizacion` o la persona que él designe como encargada de un dominio (DIAG-04). El diagnóstico ocurre antes de implementar la LOPDP, cuando aún no hay responsables de área: por eso el encargado es cualquier persona con rol vigente, no un rol concreto. El DPO revisa lo declarado con la grilla «declarado / verificado», puede **objetar** una respuesta y es el único que **sella**. Fundamento: el delegado supervisa y no ejecuta (Doctrina 2, `INV_LOPDP_DPO_INDEPENDENCE`; Reglamento del Delegado, Res. SPDP-SPD-2025-0028-R).

**Contrato:** `governance/especificaciones/DIAG-07.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- `PUT /diagnostico/respuestas` (sección `#DIAG-07` del router, que DIAG-05 ya reescribe): escriben `admin_organizacion` en cualquier dimensión y el encargado asignado (DIAG-04) en las suyas; `dpo`, `implementador` y `coordinador` reciben 403. Sus filas de la matriz en `tests/matriz/DIAG-07.py`.
- **Evidencia del diagnóstico:** el administrador y los encargados **no la suben**: entregan los documentos al `dpo`, que los sube y vincula hasta el sello del diagnóstico real (EVI-01, `INV_LOPDP_DIAG_EVIDENCE_DPO_UNTIL_SEAL`). Entre el diagnóstico de prueba y el real (`DIAG-11`), el administrador puede entregar información nueva y corregir respuestas; el sello del real tampoco admite objeciones abiertas. La grilla muestra esa evidencia; esta tarea no crea ninguna ruta de subida.
- **Objeciones:** el `dpo` objeta una respuesta con motivo antes de sellar; la respuesta queda `objetada` hasta que el respondiente la vuelve a guardar. No se puede sellar con objeciones abiertas.
- **Grilla de revisión** (`GrillaRevision.tsx`): por pregunta, lo declarado, la evidencia, el nivel que el DPO verifica (`nivel_sellado`) y la objeción; la columna de verificación es de solo lectura: muestra el `nivel_sellado` calculado; no hay nivel editable mientras el CTO no lo decida.
- Nota en DIAG-03: su decisión del 2026-10-27 queda sustituida por esta.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10: la que se fusione después se vuelve a encadenar). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra un PostgreSQL 16 local en contenedor; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- El `dpo` recibe 403 al guardar respuestas y 200 al objetar y sellar; el administrador guarda en cualquier dimensión; el encargado solo en la suya (403 fuera de ella).
- No se sella con una objeción abierta (409).
- Mutación documentada: dejar que el `dpo` escriba respuestas y comprobar que la prueba del 403 falla.

## Límites
- No cambia el scoring ni el sellado (DIAG-03) salvo la condición de «sin objeciones abiertas».
- No toca `DiagnosticCanvas.tsx` (DIAG-05 y EVI-01): la grilla es un componente nuevo.


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#DIAG-07` (ADR 0001).
- **Errores de negocio en la capa de dominio**: Todo error de negocio lanza `ErrorNegocio` importado desde `app_core.errors` (nunca desde `api.errores`) y registra sus códigos en `features/<sala>/domain/errores.py#DIAG-07` sin modificar `app_core/errors.py`.

**Decisión del Arquitecto (2026-11-10):** DIAG-07 toma entero `api/routers/diagnostico_respuestas.py` (es la única ficha viva que lo posee; DIAG-05 y ADPA-05, dueñas de las marcas del archivo, están hechas) y edita `_escritura` y `put_respuestas` directamente, sin marcas. **Advertencia de diseño:** el encargado asignado puede tener cualquier rol salvo `dpo` (implementador, coordinador, responsable_area…); el gate del router acepta cualquier rol vigente salvo `dpo` y la decisión por dimensión la toma el motor: el administrador escribe en todas y el encargado asignado solo en las suyas. Si el gate fuese `require_role("admin_organizacion")` se rompe la ficha. Pruebas, cada una con su mutación: el `dpo` recibe 403 (mutación: aceptar `dpo`); un implementador asignado a D03 escribe en D03 y recibe 403 en D04 (mutación: quitar la comprobación de dimensión); el administrador escribe en todas; una respuesta que mezcla una dimensión propia y una ajena se rechaza entera. DIAG-12 y DIAG-07 comparten secciones en `diagnostico_service.py` y `app_core/pasillo/roadmap.py`: cada una escribe solo dentro de sus marcas. `api/routers/diagnostico_resultados.py` lo posee ORG-23 entero y depende de DIAG-07.

**Cambio 2026-11-11 (Arquitecto ADPA, expandir y contraer):** esta ficha pasa a pendiente hasta el final y depende de DIAG-07a, DIAG-07b y EVI-01b. Es la fase «contraer»: el gate de `PUT /diagnostico/respuestas` pasa a cualquier rol vigente salvo `dpo` con decisión por dimensión en el motor; toma enteros `diagnostico_respuestas.py` y `diagnostico_resultados.py` (ORG-23, también entera de este último, depende de DIAG-07), y reescribe los tests y specs cuyo asunto es quién responde (`solo-dpo.spec.ts` y los de 403 por rol) además de `tests/test_diagnostico_respuestas.py` y `tests/test_diagnostico_resultados.py`. Orden: DIAG-07a → DIAG-07b → DIAG-07 → NEON-02.

**Ajuste 2026-11-11 (CTO y Arquitecto):** DIAG-07c desaparece como ficha aparte y se funde aquí. DIAG-07 toma además `roles.ts` (añade `puedeGuardarRespuestas`, sin cambiar `puedeSellar`), `clienteRespuestas.ts`, `simulador.ts`, los siete specs de `frontend/tests/diagnostico` con `roles: ["dpo"]` (escala, escala-activa, no-aplica, persistencia, prueba-y-real, sellado y solo-dpo; vuelve a medir la lista al empezar) y `DiagnosticCanvas.tsx#DIAG-07`, con la línea `const puedeResponder = roles !== null && puedeSellar(roles)` envuelta por sus marcas (ya sembradas); los siete specs pasan a administrador en el mismo PR. Depende de EVI-01b (única otra dueña viva de `DiagnosticCanvas.tsx#EVI-01` y de tres de esos specs); DIAG-15, dueña entera de ese archivo, depende de DIAG-07 y de EVI-01b. El bloqueo del sello con objeciones abiertas usa el candado advisory transaccional del sellado, no `FOR SHARE`, con una prueba de concurrencia de dos sesiones y su mutación. Árbitro añadido: Playwright `guardar-como-admin.spec.ts` (el administrador ve los controles de respuesta habilitados y guarda; el implementador los ve deshabilitados), `tsc --noEmit` y `npm run build`.

## Decisiones del Tech Lead (2026-11-13)
- Cambio de regla intencional: responden el administrador y los encargados de cada dominio, y el DPO revisa y sella. Por eso DIAG-07 toma `NotaSoloDpo.tsx` (DIAG-14, hecha) con el texto del UX/UI.
