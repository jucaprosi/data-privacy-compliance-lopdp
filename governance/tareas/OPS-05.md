+++
id = "OPS-05"
titulo = "Guía de configuración del inicio de sesión con Google (local y producción)"
ola = "D"
estado = "pendiente"
sala = "operaciones"
depende_de = ["FE-07", "SEC-03"]
propiedad = ["governance/operaciones/CONFIGURACION_LOGIN_GOOGLE.md"]
arbitro = "cada variable de entorno y cada clave citada existe en el código (git grep); el propietario sigue la guía y el login funciona en local"
rastros = ["¤seguridad", "¤rbac-tenant"]
+++

# OPS-05 · Guía de configuración del inicio de sesión con Google (local y producción)

**Objetivo.** El login con Google está implementado y probado con simulación (FE-07, SEC-03), pero nunca se ha probado con Google real. Faltan la configuración en Google Cloud, las variables de Vercel y la prueba local, y hoy esos pasos están repartidos en fichas y conversaciones. Esta tarea deja **una sola guía, verificada contra el código**, para que el propietario pueda activar el login sin adivinar.

## Entrega
- `governance/operaciones/CONFIGURACION_LOGIN_GOOGLE.md` con:
  - **Tabla de variables**: nombre exacto, en qué proyecto va (frontend o backend), qué valor lleva, y el **archivo y línea del código que la lee**. Obtenerlas con `git grep` (`GOOGLE_CLIENT_ID`, `NEXT_PUBLIC_GOOGLE_CLIENT_ID`, `NEXT_PUBLIC_TENANT_ID`, `AUTH_MODE`, `NEXT_PUBLIC_AUTH_MODE`, `BACKEND_URL` y las que aparezcan). Una variable que el código no lee no se cita.
  - **Matriz de modos**: qué hace la interfaz y el servidor en `headers` y en `oidc`, y qué pasa con un valor desconocido (cae en `oidc`), según `frontend/src/lib/auth/modo.ts` y `app_core/security.py`.
  - **Pasos en Google Cloud Console** para crear el cliente OAuth web con el botón de Google Identity Services: orígenes autorizados de JavaScript (local y producción). Indicar qué pasos **no se pueden verificar desde el repositorio**.
  - **Prueba local paso a paso** (PowerShell, completa y pegable): variables de `frontend/.env.local` y del backend, arranque de ambos, y qué ver en la pestaña Red (`Authorization: Bearer`, `X-Tenant-ID`, sin `X-User-ID`).
  - **Aprovisionamiento del usuario:** el correo con el que se entra debe existir como usuario del tenant; cómo comprobarlo con `GET /organizacion/me/roles` y qué respuesta se ve si falta.
  - **Vuelta atrás:** cómo volver a `AUTH_MODE=headers` sin perder datos.
  - Un apartado «No verificado» con lo que solo se sabrá al probar con Google real.

## Límites
- No cambia código, variables de entorno ni la configuración de Vercel o de Google: solo documenta.
- No incluye valores reales (ID de cliente, secretos, contraseñas): solo nombres de variables y formatos.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
