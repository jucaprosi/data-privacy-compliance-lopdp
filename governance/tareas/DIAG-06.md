+++
id = "DIAG-06"
titulo = "Comparativo de un assessment con la línea base, por dimensión y dominio"
ola = "D"
estado = "pendiente"
sala = "diagnostico, frontend"
depende_de = ["DIAG-03", "FE-22", "FE-24", "DIAG-08", "ADPA-05", "DIAG-11"]
propiedad = ["features/diagnostico/services/comparativo_engine.py", "features/diagnostico/diagnostico_service.py#DIAG-06", "api/routers/diagnostico_comparativo.py", "tests/test_diagnostico_comparativo.py", "frontend/src/components/diagnostico/Comparativo.tsx", "frontend/src/lib/diagnostico/comparativo.ts", "frontend/tests/diagnostico/comparativo.spec.ts", "frontend/src/components/layout/menus/DIAG-06.ts", "frontend/src/components/layout/pantallas/DIAG-06.tsx", "features/diagnostico/domain/errores.py#DIAG-06"]
arbitro = "pytest tests/test_diagnostico_comparativo.py contra un PostgreSQL 16 local en contenedor + suite completa + Playwright de frontend/tests/diagnostico/comparativo.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada (INV_LOPDP_MULTIDIMENSIONAL_METRICS)"
rastros = ["¤diagnostico", "¤diagnostico-comparativo", "¤tablero-dimensiones"]
+++

# DIAG-06 · Comparativo de un assessment con la línea base, por dimensión y dominio

**Origen.** Apartado 6 (DIAG) y submenú Diagnóstico › Comparativo de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

## Entrega
- **Decisión del propietario (2026-11-05):** el diagnóstico se hace una sola vez y tiene dos sellos como máximo (`DIAG-11`). Esta tarea compara el **diagnóstico de prueba** con el **diagnóstico real** de la misma organización: diferencia por dimensión y por dominio, y brechas cerradas, nuevas y que siguen. Si solo hay uno sellado, la pantalla lo dice y no compara. La comparación de los estados con el diagnóstico real es de `DIAG-12`, que reutiliza `comparativo_engine.py` desde su sala.
- Sin cifra única (D-1): nunca un «avance global».
- Pantalla Diagnóstico › Comparativo (`frontend/src/components/layout/menus/DIAG-06.ts` y `frontend/src/components/layout/pantallas/DIAG-06.tsx`), con los componentes de FE-24.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10: la que se fusione después se vuelve a encadenar). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra un PostgreSQL 16 local en contenedor; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Brechas cerradas, nuevas y que siguen son correctas en un caso construido; no se comparan resultados de dos organizaciones (RLS).
- Mutación documentada: invertir línea base y actual y comprobar que la prueba falla.


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#DIAG-06` (ADR 0001).
- **Errores de negocio en la capa de dominio**: Todo error de negocio lanza `ErrorNegocio` importado desde `app_core.errors` (nunca desde `api.errores`) y registra sus códigos en `features/<sala>/domain/errores.py#DIAG-06` sin modificar `app_core/errors.py`.
