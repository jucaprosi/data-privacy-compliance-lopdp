+++
id = "ORG-15"
titulo = "Cartera de organizaciones por pertenencia, con semáforos por dimensión y sin abrir la RLS"
ola = "D"
estado = "pendiente"
sala = "organizacion, frontend"
depende_de = ["ORG-13", "ORG-14", "FE-21", "FE-22", "FE-24", "RM-21"]
propiedad = ["features/organizacion/services/cartera_engine.py", "features/organizacion/organizacion_service.py#ORG-15", "api/routers/organizacion_cartera.py", "tests/test_organizacion_cartera.py", "tests/matriz/ORG-15.py", "frontend/src/app/cartera/**", "frontend/src/lib/cartera/**", "frontend/tests/cartera/**", "frontend/src/components/layout/menus/ORG-15.ts"]
arbitro = "pytest tests/test_organizacion_cartera.py y tests/test_organizaciones_por_persona.py contra una rama Neon de revisión con lopdp_app, con la prueba de INV_LOPDP_PORTFOLIO_BY_MEMBERSHIP (la cartera lista solo organizaciones con rol vigente) + suite completa + Playwright de frontend/tests/cartera + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤rbac-tenant", "¤cartera", "¤tablero-dimensiones"]
+++

# ORG-15 · Cartera de organizaciones por pertenencia, con semáforos por dimensión y sin abrir la RLS

**Origen.** Optimización O-4 y menú 1 «Inicio» de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`. Fija el invariante **`INV_LOPDP_PORTFOLIO_BY_MEMBERSHIP`** (lo redacta Soporte en `INVARIANTS.md`; esta tarea aporta su prueba).

## Entrega
- **Fase 1 de O-4:** el servidor arma la cartera iterando `mis_organizaciones` (ORG-13) y, por cada una, fija el contexto de esa organización (`fijar_contexto_rls`) en su propia consulta. Nada de `BYPASSRLS` ni consultas sin tenant.
- Por organización: nombre, roles de la persona, las cuatro dimensiones como semáforo, brechas críticas abiertas, hallazgos abiertos (RM-21) y tareas vencidas. Sin datos personales ni cifra única (D-1).
- `GET /organizacion/cartera` (`AUTO_REGISTRO = True`), Sus filas de la matriz en `tests/matriz/ORG-15.py`.
- Pantalla `frontend/src/app/cartera/` (Inicio › Tablero de cartera), con los componentes de `frontend/src/components/tableros/` (FE-24); elegir una fila entra en esa organización con el cambio de FE-21. Entrada en el menú Inicio en `frontend/src/components/layout/menus/ORG-15.ts` y `frontend/src/components/layout/pantallas/ORG-15.tsx`.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10: la que se fusione después se vuelve a encadenar). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- `INV_LOPDP_PORTFOLIO_BY_MEMBERSHIP`: una persona con rol vigente en A y B ve A y B; tras revocar su rol en B, B desaparece; nunca aparece una organización sin rol.
- Cada fila se calcula con el contexto RLS de su organización (con `lopdp_app`, un dato de B no aparece en la fila de A).
- Mutación documentada: listar todas las organizaciones del operador en lugar de las de la persona y comprobar que la prueba falla.

## Límites
- La proyección de cartera (fase 2 de O-4, más de unas decenas de organizaciones) queda para cuando haga falta.
- Archivar y restaurar organizaciones y el calendario único de plazos no entran (plazos aplazados).
