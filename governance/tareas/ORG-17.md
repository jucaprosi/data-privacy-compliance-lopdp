+++
id = "ORG-17"
titulo = "Inventario de activos y sistemas, soportes y personas mínimas de la organización"
ola = "D"
estado = "hecha"
sala = "organizacion, frontend"
depende_de = ["ORG-07", "FE-22", "ORG-16", "RM-21", "ADPA-05", "ADPA-06", "CI-04", "CI-16", "BIB-106", "BIB-118", "BIB-119", "TEST-03"]
propiedad = ["alembic/versions/*_inventario_activos.py", "features/organizacion/services/inventario_engine.py", "features/organizacion/organizacion_service.py#ORG-17", "api/routers/organizacion_inventario.py", "tests/test_organizacion_inventario.py", "tests/matriz/ORG-17.py", "frontend/src/components/organizacion/inventario/**", "frontend/tests/organizacion/inventario.spec.ts", "frontend/src/components/layout/menus/ORG-17.ts", "frontend/src/components/layout/pantallas/ORG-17.tsx", "features/organizacion/domain/errores.py#ORG-17", "app_core/pasillo/organizacion.py#ORG-17", "app_core/pasillo/biblioteca.py#ORG-17", "frontend/playwright.config.ts"]
arbitro = "pytest tests/test_organizacion_inventario.py contra un PostgreSQL 16 local en contenedor con lopdp_app + suite completa + Playwright de frontend/tests/organizacion/inventario.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤rbac-tenant", "¤inventario"]
+++

# ORG-17 · Inventario de activos y sistemas, soportes y personas mínimas de la organización

**Origen.** Menú 3 «Inventario» y conflicto D-6 de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md` (fase 2 del documento maestro). En backlog hasta que el propietario lo lance.

## Entrega
- Activos y sistemas, soportes (físicos y digitales) y personas mínimas (nombre, cargo, área, correo; la cédula solo si la firma la exige, cifrada), por organización, vinculables a tratamientos del RAT por la compuerta de `rat`.
- Pantallas en el menú Inventario (`frontend/src/components/layout/menus/ORG-17.ts` y `frontend/src/components/layout/pantallas/ORG-17.tsx`).
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10: la que se fusione después se vuelve a encadenar). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra un PostgreSQL 16 local en contenedor; nunca producción (`ep-late-hall`).

## Límites
- «Titulares» no es una base de titulares: solo colectivos y registros de consentimiento (D-6), fuera de esta tarea.


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#ORG-17` (ADR 0001).
- **Errores de negocio en la capa de dominio**: Todo error de negocio lanza `ErrorNegocio` importado desde `app_core.errors` (nunca desde `api.errores`) y registra sus códigos en `features/<sala>/domain/errores.py#ORG-17` sin modificar `app_core/errors.py`.

**Ampliación 2026-11-10 (Tech Lead):** ORG-17 asume `frontend/playwright.config.ts` solo para añadir `"**/organizacion/inventario.spec.ts"` a `SOLO_DESARROLLO` (su spec usa `fijarAjustes`, que el build de producción elimina; lo exige test_ci16). Mismo precedente que BIB-118.
