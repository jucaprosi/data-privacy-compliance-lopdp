+++
id = "CAPA-01"
titulo = "Acciones correctivas (CAPA) guardadas en la base y visibles en la sala de auditoría"
ola = "D"
estado = "pendiente"
sala = "auditoria_capa, frontend"
depende_de = ["DPO-01", "LIM-01", "RAT-01"]
propiedad = ["alembic/versions/20261027_capa_tickets.py", "features/auditoria_capa/**", "api/routers/auditoria_capa.py", "tests/test_capa_persistencia.py", "frontend/src/components/modules/CapaModule.tsx", "frontend/src/components/CapaBoard.tsx", "frontend/src/app/actions/capaActions.ts", "frontend/src/types/capa.ts", "frontend/src/lib/capa/**", "frontend/src/app/dashboard/page.tsx", "frontend/tests/capa/**", "tests/test_sin_codigo_huerfano.py", "tests/test_api_gateway.py", "tests/test_sod_dpo.py"]
arbitro = "pytest tests/test_capa_persistencia.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/capa + suite Playwright completa + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤rbac-tenant", "¤evidencias"]
+++

# CAPA-01 · Acciones correctivas persistidas y visibles

**Hallazgo (2026-10-26).** El ciclo de acciones correctivas y preventivas está a medias:
- el servidor guarda los casos **en memoria** (`features/auditoria_capa/services/capa_engine.py`), que se borra al reiniciar, y sin aislamiento por organización en la base;
- crear y listar casos no comprueban el rol; cerrar sí aplica la separación de funciones (`validar_permiso_sod`);
- en el frontend hay dos pantallas y ninguna está montada:
  - `CapaModule.tsx` usa la API del servidor;
  - `CapaBoard.tsx` usa `capaActions.ts`, que escribe un archivo JSON en el servidor de Next: en Vercel no persiste y no separa organizaciones.

**Ciclo:** hallazgo (control, severidad y descripción), causa raíz, acción correctiva con responsable, y cierre verificado por una persona independiente con evidencia.

## Entrega
- **Migración Alembic** `20261027_capa_tickets` (id de revisión de 32 caracteres como máximo), con `down_revision` igual a la cabeza de `main` al empezar (hoy `20261025_biblioteca_base`, que va después de DPO-01; compruébalo con `alembic heads` y vuelve a comprobarlo antes de empujar: si otra migración entró a `main`, se encadena a ella). Tabla de casos por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`), con:
  - control (código `Pn` del banco de DIAG-02), severidad y descripción del hallazgo;
  - causa raíz y acción correctiva;
  - responsable, estado y fechas;
  - verificador del cierre y evidencia del cierre.
  - Permisos de `lopdp_app`: sin DELETE.
- **Servicio:** `capa_engine.py` deja la memoria y usa la base con la sesión del pedido.
- **Permisos en las rutas (decisión asumida, revisable):**
  - registran hallazgos `coordinador` y `dpo`;
  - consultan `admin_organizacion`, `coordinador`, `dpo` e `implementador`;
  - cierran `coordinador` o `admin_organizacion`, siempre que no sean el responsable de la acción;
  - el `dpo` no cierra (regla existente);
  - **identidad del servidor (lección de DPO-01):** quien registra y quien cierra es el usuario autenticado; se ignora cualquier `auditor_id` u otro id de persona enviado en el cuerpo. El responsable de la acción se elige entre los miembros activos de la organización (si no lo es, 422);
  - un caso cerrado no se modifica: la sentencia de actualización exige que el caso no esté cerrado (409 si ya lo estaba);
  - cada alta y cada cierre dejan un evento en `audit_events`.
- **Pantalla:**
  - `CapaModule.tsx` se monta en la sala «Historial de Auditoría» (`dashboard/page.tsx`, debajo de `AuditHistory`);
  - lista los casos de la organización, con formulario de alta para los roles que registran y acción de cierre para los que cierran;
  - las llamadas van en `frontend/src/lib/capa/` con `fetchAutenticado`; no se toca `frontend/src/lib/api.ts`;
  - colores solo con las variables del tema.
- Se retira `CapaModule.tsx` de la lista de excepción de `tests/test_sin_codigo_huerfano.py` (LIM-01).
- **Se retiran** `CapaBoard.tsx`, `capaActions.ts` y, si nada más los usa, los tipos de `frontend/src/types/capa.ts`.
- **Pruebas:**
  - el caso sobrevive a una sesión nueva;
  - un rol sin permiso no puede registrar ni cerrar (403);
  - el responsable de la acción no puede cerrarla;
  - el `dpo` no puede cerrar;
  - RLS entre organizaciones con `SET LOCAL ROLE lopdp_app`;
  - Playwright: la sala muestra los casos y el formulario según el rol, con la API simulada.
- `tests/test_api_gateway.py::test_capa_endpoints` (hoy crea y cierra sin identidad y con `auditor_id` en el cuerpo) se adapta como `test_rat_endpoints` y `test_dpo_cockpit_endpoints`: sin identidad no se registra ni se consulta.
- **La prueba debe correr también en la rama Neon `test` del CI:** la única base prohibida es producción (`ep-late-hall`), como en `test_rat_persistencia.py`. DPO-01 perdió un ciclo de CI por bloquear la rama del CI.
- **Prueba de mutación documentada:** permitir que el responsable cierre su propia acción y comprobar que la prueba falla.

## Notas para el propietario
- La migración debe aplicarse a la rama Neon `test` **antes** de que el CI del PR llegue a las pruebas, y a producción después de fusionar.

## Límites
- No crea un rol de auditor externo.
- No integra los casos con las tareas de la hoja de ruta; es otra tarea si se decide.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y los checks del PR están en verde. No modificó ningún archivo fuera de su propiedad.
