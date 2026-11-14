# NORM-02b · Aviso a las organizaciones de resoluciones nuevas o modificadas
`¤sdd` `¤inteligencia-normativa` `¤vigilancia-spdp` `¤seguridad-tenant`

## 1. Datos

Sin tablas ni migraciones. El aviso se arma con lo que una corrida de vigilancia encontró y con una lista de destinatarios que hoy no ofrece ningún pasillo.

- **Destinatarios:** por cada organización activa, los correos de sus usuarios con rol vigente `admin_organizacion` y `dpo`. Nada más: ni nombres, ni otros roles, ni datos de la organización.
- **Contenido del aviso:** por cada resolución nueva o con versión nueva en esa corrida, el número, el título y el enlace interno al centro de vigilancia. Es información pública del corpus normativo.

Medido en `origin/main` 4eca5af2: `app_core/pasillo/plataforma.py` no existe. La única lectura de varias organizaciones es `listar_organizaciones` de `features/plataforma/services/operador_engine.py`, que es del operador y devuelve más datos de los que hacen falta.

## 2. API

No hay rutas HTTP nuevas. Tres piezas internas:

| Pieza | Dónde | Qué hace |
| :--- | :--- | :--- |
| `destinatarios_normativos(session)` | `app_core/pasillo/plataforma.py`, sección `NORM-02b` | devuelve `[{tenant_id, correos_admin, correos_dpo}]` de las organizaciones activas |
| `avisar_novedades_normativas(…)` | `app_core/pasillo/notificaciones.py`, sección `NORM-02b` | envía un correo por organización, por el notificador configurado |
| el avisador real | `features/inteligencia_normativa/inteligencia_normativa_service.py`, sección `NORM-02b` | conecta las dos anteriores al final de una corrida correcta |

## 3. Reglas

- **R1 · Lectura mínima entre organizaciones.** `destinatarios_normativos` es la única función de esta ficha que lee más de una organización. Devuelve solo el identificador de la organización y los dos grupos de correos. No devuelve nombres, RUC ni ningún dato de tratamiento.
- **R2 · Sin saltarse el aislamiento.** La función lee con el mismo mecanismo que ya usa el operador de la plataforma para listar organizaciones. No se crea un rol que salte la RLS ni se añade una política nueva. Si con ese mecanismo no se pueden leer los roles de los usuarios, la ficha se detiene y lo informa: es una decisión del propietario y de Seguridad.
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
| **Dado** `destinatarios_normativos`, **entonces** cada elemento tiene solo `tenant_id`, `correos_admin` y `correos_dpo`. Mutación: añadir el nombre de la organización hace fallar la prueba. | `test_destinatarios_solo_lo_minimo` |
| **Dado** una organización inactiva, o un usuario con rol vencido, **entonces** no recibe aviso. | `test_solo_activas_y_roles_vigentes` |
| **Dado** una corrida sin novedades, o una fallida, **entonces** ninguna organización recibe aviso. | `test_sin_novedades_no_avisa` |
| **Dado** el notificador que falla para una organización, **entonces** la corrida termina bien, la otra recibe su aviso y la bitácora cuenta uno enviado y uno fallido, sin correos. | `test_fallo_de_envio_no_rompe_la_corrida` |
| **Dado** el usuario de la aplicación sin contexto de organización, **entonces** no puede leer los destinatarios por una consulta directa: solo por la función del pasillo. | `test_lectura_solo_por_el_pasillo` |

Todas en `tests/test_norm02b_avisos_organizaciones.py`, contra el PostgreSQL 16 local con `lopdp_app`, con el notificador doble y sin `import yaml`.

## 6. Trazabilidad

- Ficha: `governance/tareas/NORM-02b.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Separada de NORM-02 por el Tech Lead (2026-11-13). Depende de NORM-02 (en curso) y de NOTIF-01.
- **Propiedad concreta**, medida en `origin/main` 4eca5af2. La ficha solo tiene el archivo de pruebas:
  - `app_core/pasillo/plataforma.py` (crea), con su sección `NORM-02b`;
  - `features/plataforma/services/destinatarios_normativos_engine.py` (crea);
  - `features/plataforma/plataforma_service.py#NORM-02b` (por sembrar; el archivo lo comparten por sección ORG-20, en curso, y PLAT-01, pendiente);
  - `app_core/pasillo/notificaciones.py#NORM-02b` (por sembrar);
  - `features/inteligencia_normativa/inteligencia_normativa_service.py#NORM-02b` (por sembrar);
  - `tests/test_norm02b_avisos_organizaciones.py` (crea).
- Modelo sugerido: opus. Es la única lectura entre organizaciones de la tanda; un error filtra datos de una organización a otra.
- **Bloqueo del árbitro:** `scripts/verificar_especificaciones.py` rechaza el sufijo «b».
