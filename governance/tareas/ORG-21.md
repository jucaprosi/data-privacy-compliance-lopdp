+++
id = "ORG-21"
titulo = "El operador de la plataforma entra aunque no pertenezca a ninguna organización"
ola = "D"
estado = "pendiente"
sala = "plataforma"
depende_de = ["ORG-09", "ORG-11", "FE-07", "FE-10", "FE-20", "FE-21", "BIB-115"]
propiedad = ["frontend/src/app/login/page.tsx#ORG-21", "frontend/src/lib/plataforma/cliente.ts#ORG-21", "frontend/src/lib/auth/sesion.ts#ORG-21", "frontend/src/lib/auth/cabeceras.ts#ORG-21", "frontend/tests/auth/operador-sin-organizacion-activa.spec.ts"]
arbitro = "Playwright frontend/tests/auth/operador-sin-organizacion-activa.spec.ts en un proyecto del CI + tsc --noEmit + vigilantes; prueba de mutación documentada"
rastros = ["¤rbac-tenant", "¤seguridad"]
+++

# ORG-21 · El operador de la plataforma entra aunque no pertenezca a ninguna organización

**Hallazgo (2026-11-06, publicación del PMV).** El propietario, registrado como operador en `operadores_plataforma`, no puede entrar en producción. Con su cuenta de Google, la pantalla de entrada responde «No se pudieron consultar tus organizaciones: el servidor respondió 403» (`{"detail":"Usuario no registrado en la plataforma."}`). La causa:
- `frontend/src/app/login/page.tsx` consulta `GET /api/v1/organizacion/mis-organizaciones` antes de abrir la sesión. El servidor busca la identidad solo en `users` (`app_core/security.py`, `usuario_de_identidad`) y responde 403 a quien no está ahí. Un operador vive en `operadores_plataforma`, otra tabla.
- Aunque estuviera en `users`, con la lista vacía la pantalla muestra «Tu cuenta no pertenece a ninguna organización» y tampoco abre la sesión.
- `/plataforma` envía el token de la sesión (`cabecerasDePlataforma`). Sin sesión no hay token: el operador nunca llega a su pantalla, y sin ella no puede dar de alta la primera organización ni invitar a su administrador.

Predicado: ∀ p ∈ operadores_activos : p ∉ miembros ⟹ puede_abrir(/plataforma). Medido el 2026-11-06 en producción: falso.

## Entrega
- **`frontend/src/lib/plataforma/cliente.ts#ORG-21`:** `esOperadorDeLaPlataforma(token)`. Pregunta al servidor con `Authorization: Bearer <token>` a una ruta de `/api/v1/plataforma` que ya exige operador (`verificar_operador`), por ejemplo el listado de organizaciones. 200 ⟹ verdadero; 403 ⟹ falso; cualquier otro error se propaga. No usa la sesión guardada, porque aún no existe.
- **`frontend/src/app/login/page.tsx#ORG-21`:** cuando `consultarMisOrganizaciones` responde 403, o devuelve la lista vacía, se llama a `esOperadorDeLaPlataforma(credential)`:
  - si es operador: `guardarSesion(credential)` sin organización activa y `window.location.assign("/plataforma")`;
  - si no lo es: el mismo mensaje de hoy («Tu cuenta no pertenece a ninguna organización; pide una invitación.» o el del 403);
  - si es operador **y** tiene organizaciones, el flujo de hoy no cambia: entra en su organización y llega a `/plataforma` desde el menú.
- **`frontend/src/lib/auth/sesion.ts#ORG-21`:** `leerSesionDeOperador()`, con la misma validación que `leerSesion()` (forma del token y caducidad) pero sin exigir organización activa. `leerSesion()` no cambia: en `oidc` sigue descartando la sesión sin organización (FE-21).
- **`frontend/src/lib/auth/cabeceras.ts#ORG-21`:** en `oidc`, `cabecerasDePlataforma()` usa `leerSesionDeOperador()`. Solo las rutas de `/api/v1/plataforma`, donde manda `verificar_operador`, aceptan esa sesión; las demás pantallas siguen con `leerSesion()`.
  *Ampliación aprobada por el coordinador el 2026-11-06:* la especificación nueva mostró que el listado de `/plataforma` salía sin `Authorization`, porque `leerSesion()` descarta la sesión sin organización.
- El servidor no cambia: la autoridad sigue siendo `verificar_operador` en cada ruta de `/api/v1/plataforma` (OWASP, Authorization Cheat Sheet: «Developers must never rely on client-side access control checks»). La comprobación en la pantalla de entrada solo decide a dónde llevar a la persona.

## Pruebas
- `frontend/tests/auth/operador-sin-organizacion-activa.spec.ts`, en modo `oidc` con la credencial y las rutas simuladas, como las demás pruebas de `frontend/tests/auth/`:
  - `mis-organizaciones` 403 y `plataforma` 200 ⟹ llega a `/plataforma` y ve el listado, y esa petición lleva `Authorization: Bearer`;
  - `mis-organizaciones` 200 con lista vacía y `plataforma` 200 ⟹ llega a `/plataforma`;
  - `mis-organizaciones` 403 y `plataforma` 403 ⟹ se queda en la entrada con el mensaje de hoy y sin sesión guardada;
  - `mis-organizaciones` con una organización ⟹ entra en ella como hoy, aunque `plataforma` responda 200.
- La especificación tiene que correr en algún proyecto del CI (`CI-16`): si usa ganchos de desarrollo, va en `SOLO_DESARROLLO` con el sufijo `-activa`; si no, en `produccion`.
- Mutación documentada: abrir la sesión sin preguntar al servidor; el caso «403 y 403» debe fallar.

## Límites
- No cambia el backend, `mis-organizaciones`, `usuario_de_identidad` ni `operadores_plataforma`.
- No da al operador acceso a datos de las organizaciones (ORG-09).
- Las demás pantallas siguen sin organización activa para el operador: si navega fuera de `/plataforma`, se comportan como hoy sin organización.
