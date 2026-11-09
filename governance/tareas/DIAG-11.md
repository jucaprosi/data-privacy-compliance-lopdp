+++
id = "DIAG-11"
titulo = "Diagnóstico de prueba y diagnóstico real: el diagnóstico se sella dos veces como máximo y el real es la línea base"
ola = "D"
estado = "hecha"
sala = "diagnostico, frontend"
depende_de = ["DIAG-03", "DIAG-08", "ADPA-05", "ADPA-06", "ADPA-07", "DIAG-13", "ADPA-11", "ADPA-10"]
propiedad = ["alembic/versions/20261106_diagnostico_prueba_y_real.py", "features/diagnostico/services/resultados_engine.py", "features/diagnostico/diagnostico_service.py#DIAG-11", "api/routers/diagnostico_resultados.py#DIAG-11", "app_core/pasillo/diagnostico.py#DIAG-11", "features/diagnostico/domain/errores.py#DIAG-11", "tests/test_diag11_prueba_y_real.py", "frontend/tests/diagnostico/sellado.spec.ts", "frontend/tests/pmv/sin-subida-activa.spec.ts", "frontend/tests/pmv/sin-subida.spec.ts", "frontend/src/components/DiagnosticCanvas.tsx#DIAG-11", "frontend/tests/diagnostico/prueba-y-real.spec.ts"]
arbitro = "pytest tests/test_diag11_prueba_y_real.py tests/test_diagnostico_resultados.py contra una base de revisión (incluido RLS con lopdp_app) + suite completa + vigilantes + Playwright de frontend/tests/diagnostico/prueba-y-real.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤diagnostico", "¤dpo-independencia"]
+++

# DIAG-11 · Diagnóstico de prueba y diagnóstico real

**Decisión del propietario (2026-11-05).** El diagnóstico se hace una sola vez, pero puede cambiar una vez: el administrador puede entregar información que no había mostrado en el diagnóstico de prueba. Por eso hay como máximo **dos sellos** por organización:
1. **diagnóstico de prueba**;
2. **diagnóstico real**, que es la línea base.

Los dos son assessments de diagnóstico. Después del real, el assessment actual sale de los **estados** (`DIAG-12`); las 80 preguntas no se vuelven a contestar. Contrato: `PRD_EVYDENTIA_REVENTA_NUBE.md`, Módulo 1, e invariantes 58 y 59 de `INVARIANTS_EVYDENTIA_REVENTA_NUBE.md`.

**Hoy** el sellado de `DIAG-03` encadena sellos sin límite (`secuencia` 1, 2, 3…, en `features/diagnostico/services/resultados_engine.py`).

## Entrega
- **Migración** `20261106_diagnostico_prueba_y_real`: columna `tipo` en `diagnostico_resultados` (`prueba` o `real`), con una restricción que admite como máximo una fila de cada tipo por organización. Para las filas que ya existan, la de secuencia 1 queda como `prueba` y la de secuencia 2 como `real`. Si una organización tiene más de dos, la migración se detiene y lo informa para que decida el propietario.
- **Sellado** (`resultados_engine.py` y la sección `#DIAG-11` del router):
  - el primer sello es `prueba` y el segundo `real`; un tercero responde 409;
  - si el administrador no entrega información nueva, el DPO sella el real igual al de prueba (confirmado por el propietario, 2026-11-05);
  - se conserva la cadena de huellas de `DIAG-03`.
- **Respuestas:** después del sello del real, guardar respuestas responde 409.
- **Pasillo** `app_core/pasillo/diagnostico.py#DIAG-11`: la consulta `diagnostico_real_sellado(tenant_id) -> bool`, que usan `EVI-01` y `DIAG-12`.
- **Pantalla** (`DiagnosticCanvas.tsx#DIAG-11`): el botón dice «Sellar diagnóstico de prueba» o «Sellar diagnóstico real» según corresponda, y desaparece tras el real. La pantalla muestra en qué etapa está el diagnóstico.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`) y su pasillo; errores de negocio con `ErrorNegocio` y códigos en `features/diagnostico/domain/errores.py#DIAG-11`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar. Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una base de revisión; nunca producción.
- Colores solo con las variables del tema; sin tokens de gobernanza en la interfaz. Llamadas a la API por `fetchAutenticado`.

## Pruebas
- Primer sello `prueba`, segundo `real`, tercero 409; guardar respuestas tras el real, 409.
- `diagnostico_real_sellado` es falso antes del real y verdadero después; no ve otra organización (RLS).
- Mutación documentada: quitar el límite de dos sellos; la prueba del 409 debe fallar.

## Límites
- No cambia el cálculo de indicadores (`DIAG-08`) ni quién sella (`DIAG-07`).

## Nota de coordinación
`DIAG-13` (PMV) también posee `resultados_engine.py` y fija la política `EVIDENCIA_DIAGNOSTICO`: esta tarea va después y conserva esa política (en EVYDENTIA, `verificada`).

**Ampliación (Tech Lead y CTO, 2026-11-09).** En main, las cuatro secciones `#DIAG-11` de `diagnostico_service.py`, `diagnostico_resultados.py`, `app_core/pasillo/diagnostico.py` y `DiagnosticCanvas.tsx` no tienen marca y las tapan exenciones. El PR de código siembra sus marcas, igual que la opción b de DIAG-14, y en el mismo cambio quita **solo** esas cuatro líneas `DIAG-11|…` de `governance/tareas/_exenciones_propiedad.txt`, listadas en el cuerpo del PR como excepción declarada. El 409 de «guardar respuestas después del sellado real» va por la compuerta, como envoltorio en la sección del service, sin tocar `respuestas_engine.py`, y lleva una prueba por el router.

**Segunda ampliación (Tech Lead, 2026-11-09).** El botón «Guardar resultado definitivo» pasa a «Sellar diagnóstico de prueba» / «Sellar diagnóstico real». Tres specs de fichas hechas lo buscan por su nombre: `sellado.spec.ts` (DIAG-09; líneas 21, 29 y 52), `pmv/sin-subida-activa.spec.ts:84` y `pmv/sin-subida.spec.ts:127` (FE-26). DIAG-11 los asume y en ellos cambia solo el nombre del botón.

**Exenciones por sección (Tech Lead, 2026-11-09).** `_exenciones_propiedad.txt` lleva secciones `# --- INICIO <ID> ---` (el lector ignora los comentarios). DIAG-11 posee solo la suya, para que ADPA-08 pueda retirar la suya en la misma tanda.
