+++
id = "DIAG-06"
titulo = "Comparativo de un assessment con la línea base, por dimensión y dominio"
ola = "D"
estado = "pendiente"
sala = "diagnostico, frontend"
depende_de = ["DIAG-03", "FE-22", "FE-24"]
propiedad = ["features/diagnostico/services/comparativo_engine.py", "features/diagnostico/diagnostico_service.py#DIAG-06", "api/routers/diagnostico_comparativo.py", "tests/test_diagnostico_comparativo.py", "frontend/src/components/diagnostico/Comparativo.tsx", "frontend/src/lib/diagnostico/comparativo.ts", "frontend/tests/diagnostico/comparativo.spec.ts", "frontend/src/components/layout/menus/DIAG-06.ts", "frontend/src/components/layout/pantallas/DIAG-06.tsx"]
arbitro = "pytest tests/test_diagnostico_comparativo.py contra una rama Neon de revisión + suite completa + Playwright de frontend/tests/diagnostico/comparativo.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada (INV_LOPDP_MULTIDIMENSIONAL_METRICS)"
rastros = ["¤diagnostico", "¤diagnostico-comparativo", "¤tablero-dimensiones"]
+++

# DIAG-06 · Comparativo de un assessment con la línea base, por dimensión y dominio

**Origen.** Apartado 6 (DIAG) y submenú Diagnóstico › Comparativo de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

## Entrega
- Comparar dos resultados guardados (DIAG-03) de la misma organización: la línea base (el primero, o el que se marque) y otro. Diferencia por dimensión y por dominio, y brechas cerradas, nuevas y que siguen.
- Sin cifra única (D-1): nunca un «avance global».
- Pantalla Diagnóstico › Comparativo (`frontend/src/components/layout/menus/DIAG-06.ts` y `frontend/src/components/layout/pantallas/DIAG-06.tsx`), con los componentes de FE-24.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10: la que se fusione después se vuelve a encadenar). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Brechas cerradas, nuevas y que siguen son correctas en un caso construido; no se comparan resultados de dos organizaciones (RLS).
- Mutación documentada: invertir línea base y actual y comprobar que la prueba falla.
