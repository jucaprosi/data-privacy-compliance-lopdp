# Política de credenciales de las ramas de Neon

Vigente desde que Juan Carlos Proaño fusione este documento. Complementa `governance/operaciones/CREDENCIALES_Y_ROLES_BD.md`, que describe cómo rotar paso a paso.

## Por qué existe

Al crear una rama hija, Neon copia los roles de la rama madre ([documentación de roles](https://neon.com/docs/manage/roles)). El equipo detectó una rama de pruebas con la misma contraseña que otras y la rotó. Si una rama comparte contraseña, quien tenga la URL de una entra también en las demás.

Dos hechos de Neon condicionan la regla:

- **Rotar afecta a una sola rama.** Hay que rotar en cada rama donde se use el rol.
- **«Reset from parent» no se documenta como restauración de contraseñas.** Tras un reset, se comprueba la credencial; no se da por rotada ni por heredada.

## Reglas

1. **Toda rama hija recibe credencial propia al crearse.** Antes del primer uso, se rota la contraseña de `lopdp_beta_owner` en esa rama, o se crea un rol propio para ella.
2. **Ninguna rama de pruebas nace de `production`.** Las temporales nacen de `test-<persona>`.
3. **Las ramas temporales se borran al fusionar su tarea.** Una rama borrada no se rota.
4. **Una credencial expuesta se rota en el acto** en todas las ramas que la compartan, sin esperar a confirmar su uso.

## Quién hace qué

| Rama | Crea y rota | Actualiza dónde se usa |
| :--- | :--- | :--- |
| `production` | Juan Carlos | Juan Carlos: `.env` y Vercel |
| `test-main` | Juan Carlos | Juan Carlos: secreto `TEST_DATABASE_URL` de GitHub |
| `test-<persona>` | Juan Carlos | Juan Carlos: secreto `TEST_DATABASE_URL_<PERSONA>`. Cada persona: su `.env` |
| Hija temporal de `test-<persona>` | La persona dueña | La persona dueña: su `.env` |

Una sesión de IA no rota contraseñas, no las recibe ni las escribe. Prepara el comando; lo ejecuta una persona.

## Dónde se guarda

- **Sí:** el `.env` local, los archivos locales de la carpeta `herramientas`, los secretos de GitHub, las variables de Vercel y el gestor de contraseñas de cada persona.
- **Nunca:** chats (incluidas las sesiones de IA), el repositorio, PR, issues, capturas de pantalla ni registros de CI.

Para pasar una credencial a otra persona se usa el enlace de un solo uso del gestor de contraseñas. Si se pega por error en un chat, se aplica la regla 4.

## Cómo se verifica

1. Tras rotar, en la consola de Neon cambia «Last updated» del rol en esa rama.
2. La URL nueva conecta: `comprobar_credenciales.py`, en la carpeta `herramientas`, responde «OK» sin mostrar la contraseña.
3. La URL de la rama madre **no** entra en la rama hija: la misma utilidad responde «FALLA» si se prueba la contraseña anterior.
4. Si la rama la usa el CI, el siguiente arnés conecta. Un fallo de autenticación significa que el secreto de GitHub quedó sin actualizar.
5. Cada rotación se anota con fecha, rama y persona en el registro de operaciones, sin ningún valor.

Juan Carlos revisa cada mes la lista de ramas en la consola de Neon: borra las que no tengan tarea abierta y rota las que no conste que se hayan rotado.
