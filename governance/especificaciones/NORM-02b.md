# NORM-02b · Aviso a las organizaciones de resoluciones nuevas o modificadas
`¤sdd` `¤inteligencia-normativa` `¤vigilancia-spdp` `¤seguridad-tenant`

## 1. Datos

Sin tablas nuevas. El aviso se arma con lo que una corrida de vigilancia encontró y con la lista de destinatarios que da una función nueva de la base.

- **Migración `alembic/versions/norm02b_destinatarios_normativos.py`**, primera de la sala `plataforma` (`alembic/salas.py`: dueña de `operadores_plataforma`, `auditoria_plataforma` e `invitaciones_organizacion`, y donde vive el motor que lee la función): `down_revision = BASE_COMUN`, `branch_labels = ("plataforma",)`, una cabeza por sala (CI-28). No va en `organizacion` aunque las tablas que lee sean de esa sala: abrir la rama de `organizacion` obligaría, por la regla R4 de CI-28, a declarar `depends_on` en las migraciones ya aplicadas de las demás salas que nombran `tenants`, `users` o `user_tenant_roles` (12 en `origin/main` 020bc051), y `test_grafo_real_cumple_las_reglas` falla. Crea `fn_destinatarios_normativos()`:
  - firma: sin parámetros, `RETURNS TABLE(tenant_id VARCHAR, correos_admin TEXT[], correos_dpo TEXT[])`, `LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, public`;
  - filtro: solo organizaciones activas; roles `admin_organizacion` y `dpo` vigentes (`valid_to IS NULL OR valid_to > now()`); usuarios con `activo` y `deleted_at IS NULL`, igual que `fn_tenant_tiene_admin_activo` (`alembic/versions/20261022_invitacion_unica_emitida.py:60`). Una organización sin ningún correo en los dos grupos no sale;
  - permisos: `REVOKE ALL ON FUNCTION fn_destinatarios_normativos() FROM PUBLIC` y `GRANT EXECUTE ON FUNCTION fn_destinatarios_normativos() TO lopdp_app`, y nada más. No cambia ninguna política ni la RLS de `user_tenant_roles`;
  - **dueño:** el rol que ejecuta la migración, que es el dueño de las tablas (`lopdp_beta_owner` en Cloud SQL, `governance/operaciones/cloud_sql_instance.yaml`). Con `FORCE ROW LEVEL SECURITY`, la RLS también se aplica al dueño de la tabla salvo que tenga `BYPASSRLS` o sea superusuario, y en Cloud SQL el rol que migra no es un superusuario de verdad (lo documenta `20261108_biblioteca_capacidades_propietario.py`). Por eso la función se comprueba en Cloud SQL, no solo en el PostgreSQL local (R2b).
- **Brief del propietario** `governance/operaciones/BRIEF_PROPIETARIO_NORM02B.md` (crea): tras migrar cada base de Cloud SQL, una llamada de solo lectura con `lopdp_app` que devuelve solo números, sin correos: `SELECT count(*) FROM fn_destinatarios_normativos()` y, para la función existente, `SELECT count(*) FROM tenants t WHERE fn_tenant_tiene_admin_activo(t.id)`. Si alguno da 0 habiendo organizaciones activas con administrador, se detiene y se informa al CTO.

- **Destinatarios:** por cada organización activa, los correos de sus usuarios con rol vigente `admin_organizacion` y `dpo`. Nada más: ni nombres, ni otros roles, ni datos de la organización.
- **Contenido del aviso:** por cada resolución nueva o con versión nueva en esa corrida, el número, el título y el enlace interno al centro de vigilancia. Es información pública del corpus normativo.

Medido en `origin/main` 020bc051: `app_core/pasillo/plataforma.py` y `app_core/pasillo/notificaciones.py` existen (BOV-01 y NOTIF-01, hechas). El operador lee con `lopdp_app` sin fijar organización (ORG-09, `INV_LOPDP_OPERATOR_NO_TENANT_DATA`), y con ese mecanismo `user_tenant_roles` da 0 filas (`tests/test_plataforma_operador.py::test_operador_como_lopdp_app_sin_tenant_no_ve_filas_rls`). Por eso los destinatarios salen de la función, no de una consulta directa.

## 2. API

No hay rutas HTTP nuevas. Tres piezas internas:

| Pieza | Dónde | Qué hace |
| :--- | :--- | :--- |
| `destinatarios_normativos(session)` | `app_core/pasillo/plataforma.py`, sección `NORM-02b` | devuelve `[{tenant_id, correos_admin, correos_dpo}]` de las organizaciones activas, leídos solo de `fn_destinatarios_normativos()` |
| `avisar_novedades_normativas(…)` | `app_core/pasillo/notificaciones.py`, sección `NORM-02b` | envía un correo por organización, por el notificador configurado |
| el avisador real | `features/inteligencia_normativa/inteligencia_normativa_service.py`, sección `NORM-02b` | conecta las dos anteriores al final de una corrida correcta |

## 3. Reglas

- **R1 · Lectura mínima entre organizaciones.** `destinatarios_normativos` es la única función de esta ficha que lee más de una organización. Devuelve solo el identificador de la organización y los dos grupos de correos. No devuelve nombres, RUC ni ningún dato de tratamiento.
- **R2 · Sin saltarse el aislamiento (decisión del CTO y del propietario, 2026-11-19, opción (a)).** Los destinatarios se leen solo con `fn_destinatarios_normativos()`, una función `SECURITY DEFINER` estrecha que sigue el patrón de `fn_tenant_tiene_admin_activo`. El operador sigue sin fijar nunca organización (ORG-09). No se crea un rol que salte la RLS, no se añade ni cambia ninguna política y la lectura directa de `user_tenant_roles` con `lopdp_app` sin organización sigue dando 0 filas. Solo `lopdp_app` ejecuta la función.
- **R2b · La función ve las filas en la nube.** El dueño de la función es el rol que migra. Si en Cloud SQL ese rol no ve las filas de `user_tenant_roles` por la RLS forzada, la función devolvería vacío en silencio. La comprobación del brief del propietario lo detecta; si falla, se detiene y lo decide el CTO, sin añadir políticas por cuenta propia.
- **R3 · Un correo por organización.** Cada organización recibe su propio mensaje, con sus destinatarios. Ningún mensaje lleva destinatarios de dos organizaciones, ni en copia ni en copia oculta, y ningún mensaje nombra a otra organización.
- **R4 · Cuándo se avisa.** Al final de una corrida correcta que encontró al menos una resolución nueva o una versión nueva. Una corrida sin novedades no avisa. Una corrida fallida avisa solo al operador (NORM-02).
- **R5 · Sin repetir.** El aviso lleva solo las novedades de esa corrida. Una resolución ya conocida no se vuelve a anunciar en la corrida siguiente.
- **R6 · El envío no rompe la corrida.** Si el notificador falla para una organización, la corrida sigue, las demás reciben su aviso y el fallo queda en la bitácora de la corrida con el número de avisos enviados y fallidos, sin correos.
- **R7 · Organizaciones sin destinatarios.** Una organización sin administrador ni DPO vigentes no recibe aviso y se cuenta en la bitácora.
- **R8 · Sin correos en registros.** Ni los registros ni la bitácora guardan direcciones de correo.
- **R-ADPA · Ortogonalidad ZERAG (`NORM-02b`).** La sala normativa llega a plataforma y a notificaciones solo por sus pasillos.

## 4. Interfaz

No aplica: no hay pantalla nueva. El correo usa la plantilla del notificador; su texto lo revisa UX/UI si cambia la plantilla.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** dos organizaciones activas con administrador y DPO, y una corrida con una resolución nueva, **entonces** cada organización recibe un correo con sus propios destinatarios. Mutación: un solo correo con todos los destinatarios hace fallar la prueba. | `test_un_aviso_por_organizacion` |
| **Dado** los mensajes enviados, **entonces** ninguno contiene un correo, un identificador ni un nombre de otra organización. Mutación: añadir en copia a la otra organización hace fallar la prueba. | `test_ningun_aviso_cruza_organizaciones` |
| **Dado** `destinatarios_normativos` y `fn_destinatarios_normativos()`, **entonces** cada elemento tiene solo `tenant_id`, `correos_admin` y `correos_dpo`. Mutaciones: añadir el nombre de la organización al pasillo, o añadir una columna a la función, hace fallar la prueba. | `test_destinatarios_solo_lo_minimo` |
| **Dado** una organización inactiva, o un usuario con rol vencido, **entonces** no recibe aviso. | `test_solo_activas_y_roles_vigentes` |
| **Dado** `fn_destinatarios_normativos()` llamada directamente, **entonces** no devuelve organizaciones inactivas, roles vencidos ni usuarios inactivos o borrados. Mutación: quitar la condición de `valid_to` hace fallar la prueba. | `test_funcion_excluye_inactivas_y_vencidas` |
| **Dado** una corrida sin novedades, o una fallida, **entonces** ninguna organización recibe aviso. | `test_sin_novedades_no_avisa` |
| **Dado** el notificador que falla para una organización, **entonces** la corrida termina bien, la otra recibe su aviso y la bitácora cuenta uno enviado y uno fallido, sin correos. | `test_fallo_de_envio_no_rompe_la_corrida` |
| **Dado** el usuario de la aplicación sin contexto de organización, **entonces** no puede leer los destinatarios por una consulta directa (0 filas de `user_tenant_roles`): solo por la función del pasillo. La función es `SECURITY DEFINER`, su `search_path` está fijado y `PUBLIC` no tiene `EXECUTE`. Mutación: `GRANT EXECUTE … TO PUBLIC` hace fallar la prueba. | `test_lectura_solo_por_el_pasillo` |

Todas en `tests/test_norm02b_avisos_organizaciones.py`, contra el PostgreSQL 16 local con `lopdp_app`, con el notificador doble y sin `import yaml`.

## 6. Trazabilidad

- Ficha: `governance/tareas/NORM-02b.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Separada de NORM-02 por el Tech Lead (2026-11-13). Depende de NORM-02 y de BOV-01 (en curso las dos) y de NOTIF-01. Orden: BOV-01 → NORM-02b.
- **Propiedad concreta**, medida en `origin/main` 020bc051. La ficha tiene el motor, la prueba, la migración y el brief del propietario; las cuatro secciones las abre el PR de implementación y amplía con ellas la propiedad (R-PROP-EXISTE):
  - `alembic/versions/norm02b_destinatarios_normativos.py` (crea);
  - `governance/operaciones/BRIEF_PROPIETARIO_NORM02B.md` (crea);
  - `app_core/pasillo/plataforma.py#NORM-02b` (por sembrar);
  - `features/plataforma/services/destinatarios_normativos_engine.py` (crea);
  - `features/plataforma/plataforma_service.py#NORM-02b` (por sembrar; el archivo lo comparten por sección ORG-20, en curso, y PLAT-01, pendiente);
  - `app_core/pasillo/notificaciones.py#NORM-02b` (por sembrar);
  - `features/inteligencia_normativa/inteligencia_normativa_service.py#NORM-02b` (por sembrar);
  - `tests/test_norm02b_avisos_organizaciones.py` (crea).
- Modelo sugerido: opus. Es la única lectura entre organizaciones de la tanda; un error filtra datos de una organización a otra.
