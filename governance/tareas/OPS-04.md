+++
id = "OPS-04"
titulo = "Entorno de base de datos PostgreSQL 16 local por agente"
ola = "indep"
estado = "hecha"
sala = "operaciones"
depende_de = []
propiedad = ["governance/tareas/OPS-04.md"]
arbitro = "un agente de desarrollo conecta a su PostgreSQL 16 local y comprueba que el rol lopdp_app existe"
rastros = ["¤seguridad", "¤ci-cd"]
+++

# OPS-04 · Base de datos local por agente de desarrollo

**Objetivo.** Cada agente de desarrollo ejecuta pruebas y migraciones contra PostgreSQL 16 local aislado (`127.0.0.1:55432`) mediante `scripts/entorno_local.ps1`.

## Entrega
- Procedimiento operativo: levantar el servicio PostgreSQL 16 local, exportar `TEST_DATABASE_URL` y `TEST_MIGRATION_DATABASE_URL` en la sesión de PowerShell (nunca en archivos dentro del repositorio), ejecutar `alembic upgrade head` y comprobar que `lopdp_app` existe.

## Límites
- Las cadenas de conexión son secretos: las crea y las entrega el usuario.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
