# OPE-01 · Cada operador de la plataforma tiene su usuario
`¤sdd` `¤arbitro`

## 1. Datos

Hechos medidos en `origin/main` 64802550:
- `operadores_plataforma` (id, email, google_sub, nombre, activo) es de la sala plataforma (`alembic/salas.py:102`). Su rama de Alembic tiene la etiqueta `plataforma` y la cabeza `norm02b_destinatarios_normativos`.
- `administrar_operadores.py` tiene `listar`, `alta` y `baja`, con `MIGRATION_DATABASE_URL`, y no toca `users`.
- `users` es de la sala organizacion (`salas.py:127`). Su pasillo expone `crear_o_recuperar_usuario(session, email, nombre)`.
- El login (`app_core/security.py`, `usuario_de_identidad`) busca en `users` por `google_sub` y, si no lo encuentra, por correo verificado, y entonces vincula el `sub`. Quien no está en `users` recibe 403 `USUARIO_NO_REGISTRADO`.
- En producción `users` tiene 0 filas y hay 5 operadores activos.

Migración `20261125_ope01_operador_usuario`, que cuelga de `norm02b_destinatarios_normativos`: añade `operadores_plataforma.usuario_id varchar NULL REFERENCES users(id)`, con UNIQUE.

## 2. API

Sin API nueva. Línea de órdenes:
- `python -m features.plataforma.administrar_operadores alta <correo> <nombre>`: además de lo de hoy, crea o recupera el usuario y guarda `usuario_id`.
- `python -m features.plataforma.administrar_operadores vincular`: hace lo mismo para cada operador activo sin `usuario_id`, y lista los enlazados. Se puede repetir sin efecto.
- `baja` no cambia: deja `activo = false`.

Pasillo `app_core/pasillo/plataforma.py`:
- `operador_activo(session, usuario_id) -> bool`;
- `listar_operadores_activos(session) -> list[dict]`, con `usuario_id`, `nombre`, `email` y `ha_entrado` (`google_sub` vinculado en `users`).

## 3. Reglas

- **R1 · Un usuario por operador.** Cada operador activo tiene `usuario_id`, y su usuario tiene el mismo correo y no tiene membresía en ningún tenant (`user_tenant_roles`).
- **R2 · Misma identidad.** El `google_sub` del usuario lo vincula el login de siempre. `operador_activo` lo compara con el del operador cuando los dos existen; si difieren, el operador no cuenta como activo.
- **R3 · Baja inmediata.** `operador_activo` lee `activo` en cada llamada, sin caché. Tras `baja`, la siguiente solicitud ya no lo ve activo.
- **R-SP · Sin prohibiciones** (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`OPE-01`).** Solo los archivos de la propiedad. Otras salas, solo por sus pasillos. Las pruebas no usan `import yaml`.

## 4. Interfaz

Sin pantalla.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** `alta` de un correo nuevo, **entonces** hay un operador activo con `usuario_id` y un usuario con ese correo y sin roles en ningún tenant. Mutación m1: no guardar `usuario_id` da rojo. | `tests/test_ope01_operador_usuario.py` |
| **Dado** dos operadores activos sin `usuario_id`, **entonces** `vincular` enlaza a los dos, y repetirlo no crea filas. Mutación m2: crear un usuario por cada ejecución da rojo. | ídem |
| **Dado** `baja`, **entonces** `operador_activo` devuelve `false` en la siguiente llamada. Mutación m3: una caché de la respuesta da rojo. | ídem |
| **Dado** un `google_sub` distinto en las dos tablas, **entonces** `operador_activo` devuelve `false`. Mutación m4: no compararlo da rojo. | ídem |
| **Dado** el grafo, **entonces** la sala tiene una sola cabeza y solo importa otras salas por sus pasillos. | `tests/test_alembic_cabeza_por_sala.py`, `tests/test_adpa_bulkhead.py` |

## 6. Trazabilidad

- **PRD:** operadores de la plataforma y Módulo 7 (Biblioteca).
- Brief del CTO `ARQUITECTO_UXUI_BIBLIOTECA_OPERADORES` (2026-11-25) y parte de pantalla del UX/UI `UXUI_PARTE_PANTALLA_BIBLIOTECA_OPERADORES` (2026-11-25), base `origin/main` 64802550.
