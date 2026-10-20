+++
id = "SEC-09"
titulo = "Recrear la tabla derechos_arco_solicitudes con RLS: el modelo ARCO+ no tiene tabla en la base"
ola = "D"
estado = "pendiente"
sala = "derechos_arco"
depende_de = ["SEC-02", "ORG-07"]
propiedad = ["alembic/versions/*_derechos_arco_solicitudes.py", "tests/test_derechos_arco_esquema.py"]
arbitro = "pytest tests/test_derechos_arco_esquema.py tests/test_alembic_una_cabeza.py + suite completa contra una rama Neon propia; prueba de mutación documentada"
rastros = ["¤seguridad", "¤rbac-tenant"]
+++

# SEC-09 · Recrear la tabla `derechos_arco_solicitudes` con RLS

**Objetivo.** El modelo `SolicitudARCO` (`features/derechos_arco/domain/models.py`) declara la tabla `derechos_arco_solicitudes`, y el servicio persistente (`features/derechos_arco/derechos_arco_service.py`) y el router `api/routers/arco_router.py` la usan. Pero **ninguna migración la deja creada**: la crea `001_initial_schema.py` (con otras columnas, `titular_id` y `tipo_derecho`) y la elimina `9369ce2c67fd_add_tenants_and_registro_auditoria.py` (`op.drop_table('derechos_arco_solicitudes')` en su `upgrade`), y ninguna posterior la recrea. Una base que siga las migraciones hasta la cabeza **no tiene la tabla**: el router persistente respondería con un error de relación inexistente. Hoy esto pasa desapercibido porque `/api/v1/arco` lo sirve un router semilla en memoria (hallazgo H01 de SEC-02); SEC-08 lo sustituye, y lo bloquea que la tabla no exista (comprobado por su agente con `to_regclass('public.derechos_arco_solicitudes')` = nulo).

## Entrega
- Una migración `*_derechos_arco_solicitudes.py` (`down_revision` = la cabeza de `main` al crear la rama; hoy `20261019_org07_estructura`) que crea la tabla **con las columnas del modelo vigente**: `id` (UUID, `gen_random_uuid()`), `tenant_id` (UUID, no nulo, con índice), `tipo_solicitud` y `estado` (tipos enumerados con los valores de `TipoSolicitud` y `EstadoSolicitud`), `cedula_solicitante` (varchar 20), `nombre_solicitante` (varchar 200), `fecha_recepcion` y `fecha_vencimiento` (con zona horaria, no nulas) y `evidencia_respuesta_hash` (varchar 64, opcional). Se comprueba contra el modelo, no contra la migración 001.
- **Seguridad, como el resto de tablas con tenant** (patrón de `20261019_org07_estructura`): `ENABLE` y `FORCE ROW LEVEL SECURITY`, política de aislamiento por `app.current_tenant_id`, y `GRANT SELECT, INSERT, UPDATE` al rol `lopdp_app` **sin `DELETE`** (las solicitudes ARCO son un expediente probatorio: no se borran).
- **Idempotente y segura en cualquier base:** crea los tipos y la tabla solo si no existen (`IF NOT EXISTS` / bloque `DO`), de modo que aplicarla sobre una base donde la tabla ya exista (por ejemplo una producción que se hubiera tocado a mano) no falla ni destruye datos. Un `downgrade` completo que deja la base como estaba antes.
- `tests/test_derechos_arco_esquema.py`, con base real: la tabla existe; sus columnas y tipos coinciden con el modelo (comparar `Base.metadata` con `information_schema`); RLS activo y forzado, con política; `lopdp_app` puede `INSERT`/`SELECT`/`UPDATE` y **no** `DELETE`; aislamiento: con el tenant A fijado no se ven las filas del tenant B; sin tenant fijado no se ve ninguna. Sin SQL interpolado.
- **Prueba de mutación documentada:** al quitar a propósito el `FORCE ROW LEVEL SECURITY` o el `GRANT` (en una copia de la migración aplicada a una rama de pruebas), las pruebas fallan.

## Límites
- No toca el modelo, el servicio ni los routers de ARCO (eso es SEC-08).
- No migra datos: la tabla no tiene filas que conservar (el router vigente las guarda en memoria).
- No toca la tabla `transferencias_terceros`, **con el mismo defecto** (verificado): la misma migración `9369ce2c67fd` la elimina en su `upgrade` (línea 47) y solo la recrea en su `downgrade`; ninguna migración posterior la crea, y `features/transferencias/services/encargados_service.py` la mapea (`__tablename__ = "transferencias_terceros"`). Se reporta en el informe como hallazgo aparte para otra tarea; no se corrige aquí para no mezclar dos tablas en una migración.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
- El propietario comprueba en producción `SELECT to_regclass('public.derechos_arco_solicitudes');` antes de aplicar la migración, para saber si hay algo que conservar.
