# Brief del propietario · Comprobar los destinatarios del aviso normativo (NORM-02b)

Fecha: 2026-11-19. Redactado con la ficha NORM-02b. Lo ejecuta el propietario. El resto del equipo no ejecuta nada de esto. Todas las consultas son de solo lectura y devuelven solo números: ningún correo, nombre ni dato de una organización.

## Qué comprueba este brief y por qué
NORM-02b avisa a cada organización cuando la vigilancia normativa encuentra resoluciones nuevas o con una versión nueva. Los destinatarios (administradores y DPO vigentes) salen de la función `fn_destinatarios_normativos()`, que crea la migración `norm02b_destinatarios_normativos` (primera de la sala `plataforma`). La función es `SECURITY DEFINER`: lee `user_tenant_roles` con los permisos de su dueño, que es el rol que migra (`lopdp_beta_owner`).

En Cloud SQL ese rol no es un superusuario de verdad y la tabla tiene `FORCE ROW LEVEL SECURITY`. Si la RLS le oculta las filas, la función devuelve vacío **en silencio** y ninguna organización recibe el aviso. En el PostgreSQL local no se puede ver, porque allí el dueño es superusuario. Por eso se comprueba en cada base de Cloud SQL (regla R2b de `governance/especificaciones/NORM-02b.md`).

Qué no hace este brief: no migra, no despliega, no cambia permisos, roles ni políticas, y no envía correos.

## Cuándo
Después de aplicar las migraciones de `main` con NORM-02b en cada base de Cloud SQL (pruebas, demo y producción), una vez por base.

## Paso único: tres conteos con `lopdp_app`
Conéctate a la base recién migrada con el usuario `lopdp_app` (el de la aplicación, no el dueño), en tu cliente de base de datos habitual. Para tener el texto exacto:

```powershell
$CONSULTA = @'
SELECT
  (SELECT count(*) FROM tenants WHERE activo IS TRUE) AS organizaciones_activas,
  (SELECT count(*) FROM tenants t WHERE t.activo IS TRUE AND fn_tenant_tiene_admin_activo(t.id)) AS con_administrador,
  (SELECT count(*) FROM fn_destinatarios_normativos()) AS con_destinatarios;
'@
Write-Output $CONSULTA
```

Pégala tal cual y anota los tres números.

## Cómo se lee
- `con_destinatarios` debe ser mayor que 0 y al menos igual a `con_administrador` (una organización con administrador vigente siempre tiene destinatarios). Todo bien: no hay que hacer nada más.
- `organizaciones_activas` es 0: no hay a quién avisar; la comprobación se repite cuando exista la primera organización con administrador.
- **`con_destinatarios` o `con_administrador` da 0 habiendo organizaciones activas que sabes que tienen administrador:** la RLS forzada oculta las filas al dueño de la función. **Detente** y pásale los tres números al CTO. No añadas políticas, no cambies el dueño de la función ni crees roles por tu cuenta: lo decide el CTO.
- Un error `permission denied for function fn_destinatarios_normativos`: estás conectado con un usuario distinto de `lopdp_app`, o la migración no se aplicó en esa base. Comprueba el usuario y la migración y repite.

## Qué le dices al CTO
- Por cada base: su nombre y los tres números, o el error exacto.
- Con eso, el CTO da por comprobada la regla R2b en esa base o decide el remedio.
