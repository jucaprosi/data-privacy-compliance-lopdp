+++
id = "ORG-13"
titulo = "Una persona pertenece a varias organizaciones solo como DPO o implementador, y puede consultar las suyas"
ola = "D"
estado = "pendiente"
sala = "organizacion, plataforma"
depende_de = ["CAPA-01", "ORG-10", "ORG-11", "ORG-12"]
propiedad = ["alembic/versions/20261028_organizaciones_por_persona.py", "features/organizacion/services/roles_engine.py", "features/organizacion/organizacion_service.py#ORG-13", "api/routers/organizacion.py", "features/plataforma/services/operador_engine.py", "tests/test_organizaciones_por_persona.py"]
arbitro = "pytest tests/test_organizaciones_por_persona.py contra una rama Neon de revisión (disparador y función probados con lopdp_app) + suite completa + vigilantes; prueba de mutación documentada"
rastros = ["¤rbac-tenant", "¤seguridad"]
+++

# ORG-13 · Personas en varias organizaciones

**Decisión del propietario (2026-10-26).**
- Una persona puede pertenecer a varias organizaciones **solo** si en todas tiene los roles `dpo` o `implementador`. Es el caso de un DPO o un implementador externo que atiende a varios clientes.
- Quien tiene `admin_organizacion`, `coordinador` o `responsable_area` pertenece a **una sola** organización: no puede tener ningún rol en otra.
- Solo cuentan las asignaciones vigentes (`valid_to` vacío o futuro).

**Hallazgo.** Hoy nada lo controla. Las asignaciones de `user_tenant_roles` se aíslan por organización (RLS), así que al conceder un rol no se ve si la persona ya está en otra. Además, el frontend no puede saber a qué organizaciones pertenece la persona: la organización se fija por despliegue (`NEXT_PUBLIC_TENANT_ID`).

## Entrega
- **Migración** `20261028_organizaciones_por_persona` (id de 32 caracteres como máximo), con `down_revision` igual a la cabeza de `main` al empezar. Compruébalo con `alembic heads` al empezar y otra vez antes de empujar.
  - **Regla en la base:** un disparador `BEFORE INSERT OR UPDATE` sobre `user_tenant_roles` rechaza toda asignación vigente que rompa la regla, mirando las demás organizaciones de la persona. Es `SECURITY DEFINER` con `search_path` fijo, para ver otras organizaciones sin abrir la RLS a la aplicación. Así cubre todos los caminos que conceden roles (asignación directa, invitación, creación de organización) y los que vengan.
  - **Función** `mis_organizaciones(usuario)`: `SECURITY DEFINER`, `search_path` fijo, `EXECUTE` solo para `lopdp_app`. Devuelve id, nombre comercial y roles vigentes de cada organización de ese usuario, y nada de otras personas.
  - **Datos existentes:** antes de crear el disparador, la migración comprueba que nadie incumpla ya la regla. Si alguien la incumple, se detiene y lista los id internos de usuario (nunca correos) para que el propietario decida qué rol retirar. No borra ni cambia asignaciones.
- **API:**
  - `GET /organizacion/mis-organizaciones`: la identidad sale del token; no exige cabecera de organización ni de rol. La persona solo ve las suyas.
  - El rechazo del disparador se traduce en **409** con un mensaje claro («Esta persona ya pertenece a otra organización con un rol que no se puede compartir…») en la asignación directa (`POST /organizacion/roles`), la aceptación de invitaciones y la creación de organizaciones. Nunca un 500.
- **Pruebas**, contra una rama Neon de revisión y con `SET LOCAL ROLE lopdp_app` donde aplique:
  - lista solo las organizaciones propias con roles vigentes; las caducadas no salen; nunca las de otra persona;
  - DPO en A y DPO en B: permitido. DPO en A e implementador en B: permitido;
  - coordinador en A y cualquier rol en B: 409. DPO en A y coordinador en B: 409. Igual con `admin_organizacion` y `responsable_area`;
  - un rol caducado en A no impide asignar en B;
  - la regla se cumple aunque se inserte directamente en la base, no solo por la API;
  - `lopdp_app` sigue sin poder leer `user_tenant_roles` de otra organización: la RLS queda intacta.
- La prueba debe correr también en la rama Neon `test` del CI; la única base prohibida es producción (`ep-late-hall`).
- **Prueba de mutación documentada:** quitar el disparador, o la condición de roles, y comprobar que falla la prueba del coordinador en dos organizaciones.

## Límites
- No toca el frontend: la organización activa y su cambio son FE-21.
- Sustituye a la parte general de BIB-101: la lista de organizaciones de la persona se hace aquí, una sola vez (decisión del propietario, 2026-10-26).
- No cambia las incompatibilidades del DPO dentro de una misma organización (ORG-06 y ORG-07).

## Notas para el propietario
- Migrar la rama Neon `test` antes de que el CI del PR llegue a las pruebas, y producción después de fusionar.
- Depende de CAPA-01 solo por la cadena de migraciones: dos tareas con migración no deben correr a la vez (el 2026-10-26 BIB-105 y DPO-01 dejaron dos cabezas en `main`).

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y los checks del PR están en verde. No modificó ningún archivo fuera de su propiedad.
