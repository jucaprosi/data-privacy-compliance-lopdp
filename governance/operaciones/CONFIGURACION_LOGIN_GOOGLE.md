# Configuración del inicio de sesión con Google

Esta guía configura Google Identity Services para el modo `oidc` de la Plataforma LOPDP 360. No contiene identificadores, secretos ni datos reales. Sustituya todos los valores entre `<...>` antes de ejecutar los ejemplos.

## 1. Variables de entorno que realmente lee el código

| Variable | Proyecto | Valor esperado | Lectura en código |
|---|---|---|---|
| `AUTH_MODE` | Backend | `oidc` en producción; `headers` solo para desarrollo o vuelta atrás explícita | `app_core/security.py:42-45` |
| `GOOGLE_CLIENT_ID` | Backend | ID del cliente OAuth web, igual al utilizado por el frontend | `app_core/security.py:89-105` |
| `NEXT_PUBLIC_AUTH_MODE` | Frontend | `oidc` para exigir Google; `headers` para desarrollo o vuelta atrás | `frontend/src/lib/auth/modo.ts:36-42` |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Frontend | ID público del mismo cliente OAuth web | `frontend/src/lib/auth/modo.ts:45-47` |
| `NEXT_PUBLIC_TENANT_ID` | Frontend | ID interno del tenant al que pertenece este despliegue | `frontend/src/lib/auth/modo.ts:50-60` |
| `BACKEND_URL` | Frontend (proxy Next.js) | Origen del backend, por ejemplo `http://127.0.0.1:5000`; tiene prioridad sobre `NEXT_PUBLIC_API_URL` | `frontend/next.config.ts:3-7` |
| `NEXT_PUBLIC_API_URL` | Frontend (alternativa del proxy) | Origen o base terminada en `/api/v1`; se usa solo si falta `BACKEND_URL` | `frontend/next.config.ts:3-7` |

`GOOGLE_CLIENT_SECRET` no aparece en el flujo implementado y no debe añadirse por esta guía. El navegador recibe un ID token mediante callback y el backend valida su firma, emisor, audiencia y vigencia con las claves públicas de Google (`frontend/src/lib/auth/google.ts:12-18`, `app_core/security.py:66-73,89-121`).

Las variables `NEXT_PUBLIC_*` se incorporan al bundle de Next.js. Trate `NEXT_PUBLIC_GOOGLE_CLIENT_ID` como identificador público, pero nunca publique secretos con ese prefijo.

## 2. Matriz de modos

| Backend `AUTH_MODE` | Frontend `NEXT_PUBLIC_AUTH_MODE` | Resultado |
|---|---|---|
| `oidc` o ausente/desconocido | `oidc` | Configuración normal: aparece el botón de Google; la API exige `Authorization: Bearer <ID token>` y verifica al usuario. |
| `headers` | `headers` | Desarrollo controlado: no hay pantalla de login; se usan `X-User-ID`, `X-Tenant-ID` y, donde corresponde, `X-Role`. |
| `oidc` | `headers` | Incompatible: el frontend no aporta token de Google y la API responde 401. |
| `headers` | `oidc` | Incompatible e inseguro como despliegue: el frontend obtiene un token, pero el backend decide la identidad por `X-User-ID`; el cliente OIDC no envía esa cabecera. |

Reglas de valor desconocido:

- Backend: cualquier valor distinto de `headers`, incluidos vacío o ausente, cae en `oidc` (`app_core/security.py:42-45`).
- Frontend: un valor desconocido cae en `oidc`. Si la variable está vacía, `next build`/producción usa `oidc` y `next dev` usa `headers` (`frontend/src/lib/auth/modo.ts:36-42`). Para probar Google con `next dev`, fije `NEXT_PUBLIC_AUTH_MODE=oidc` explícitamente.

## 3. Google Cloud Console

Estos pasos son externos al repositorio y deben realizarlos quien administre el proyecto de Google Cloud:

1. Abra **Google Auth Platform > Clients** en el proyecto correcto. Configure antes la marca/pantalla de consentimiento y la audiencia que corresponda a la organización.
2. Cree un cliente de tipo **Web application**. No use un cliente Desktop, Android ni iOS.
3. En **Authorized JavaScript origins**, registre exactamente los orígenes que servirán la pantalla de login, sin ruta ni barra final:
   - local: `http://localhost:3001` para el ejemplo de esta guía;
   - local alternativo, solo si se usa: `http://127.0.0.1:3001`;
   - producción: `https://<dominio-produccion>`.
4. Este flujo usa el callback JavaScript de Google Identity Services y no implementa una URL de redirección propia (`frontend/src/lib/auth/google.ts:12-18` y `frontend/src/app/login/page.tsx:45-58`). Por ello, no agregue una URI de redirección solo por suposición. Si el flujo cambia a redirección, registre entonces la URI completa que implemente el código.
5. Copie únicamente el **Client ID**. Cárguelo con el mismo valor en `NEXT_PUBLIC_GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_ID`.
6. Si la aplicación está en estado de prueba, añada las cuentas permitidas como usuarios de prueba. Publique/configure la audiencia según la política de la organización antes de producción.

Google documenta que un cliente web necesita orígenes JavaScript autorizados y que, para pruebas locales, se deben registrar el origen localhost y su variante con puerto. Referencia: <https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid>.

No se puede verificar desde este repositorio: el proyecto seleccionado, la marca/pantalla de consentimiento, la audiencia, los usuarios de prueba, los dominios autorizados, los valores desplegados ni que la organización controle el dominio productivo.

## 4. Aprovisionamiento del usuario

Google prueba la identidad; no crea usuarios ni concede acceso. Antes del primer inicio de sesión:

1. Debe existir una fila activa en `users` cuyo correo, normalizado a minúsculas, coincida con el correo verificado por Google. En el primer acceso, el backend busca por `google_sub`; si aún no existe, busca por correo y vincula ese `sub` (`app_core/security.py:124-148`).
2. El usuario debe tener al menos una asignación vigente en `user_tenant_roles` para el tenant configurado. El rol y el tenant enviados por el cliente se autorizan contra esa asignación (`app_core/security.py:158-170`, `api/rbac.py:42-57`).
3. Tras iniciar sesión, compruebe los roles con:

```powershell
$token = '<ID_TOKEN_RECIEN_OBTENIDO>'
$tenant = '<TENANT_ID>'
$headers = @{ Authorization = "Bearer $token"; 'X-Tenant-ID' = $tenant }
Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:5000/api/v1/organizacion/me/roles' -Headers $headers
```

La respuesta correcta tiene la forma `{"user_id":"...","tenant_id":"...","roles":[...]}` (`api/routers/organizacion.py:21-29`). No copie el token a archivos, historial compartido, capturas ni registros.

Si falta el aprovisionamiento:

- correo inexistente o usuario inactivo: HTTP 403, `Usuario no registrado en la plataforma.`;
- cuenta ya vinculada a otro `sub`: HTTP 403, `La cuenta está vinculada a otra identidad de Google.`;
- rol/tenant no autorizado en endpoints que exigen contexto: HTTP 403, `Sin membresía activa`;
- configuración backend sin `GOOGLE_CLIENT_ID`: HTTP 503, `La autenticación no está configurada en el servidor.`;
- token ausente, inválido, caducado o con correo no verificado: HTTP 401.

## 5. Prueba local en PowerShell

Requisitos: dependencias Python y `frontend/node_modules` ya instaladas, base local/de prueba configurada y usuario/rol aprovisionados. Use dos terminales. El ID de cliente puede verse en la consola de Google; no use un secreto.

### Terminal 1: backend

```powershell
Set-Location 'C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360'
$env:AUTH_MODE = 'oidc'
$env:GOOGLE_CLIENT_ID = '<CLIENT_ID>.apps.googleusercontent.com'
python main.py
```

Espere a que la API responda en `http://127.0.0.1:5000/api/v1/health`. `main.py` inicia Uvicorn con recarga en el puerto 5000 (`main.py:185-187`).

### Terminal 2: frontend

```powershell
Set-Location 'C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\frontend'
$env:NEXT_PUBLIC_AUTH_MODE = 'oidc'
$env:NEXT_PUBLIC_GOOGLE_CLIENT_ID = '<CLIENT_ID>.apps.googleusercontent.com'
$env:NEXT_PUBLIC_TENANT_ID = '<TENANT_ID>'
$env:BACKEND_URL = 'http://127.0.0.1:5000'
npm run dev -- --port 3001
```

Abra `http://localhost:3001/login`, pulse **Iniciar sesión con Google** y elija la cuenta aprovisionada. El navegador guarda el ID token solo en `sessionStorage`, nunca en la URL (`frontend/src/lib/auth/sesion.ts:1-13,67-100`). Después del login debe navegar a `/dashboard` (`frontend/src/app/login/page.tsx:35-37`).

Comprobaciones negativas mínimas:

1. Quite temporalmente `NEXT_PUBLIC_GOOGLE_CLIENT_ID`, reinicie el frontend y confirme que `/login` muestra que falta esa variable.
2. Restaure el cliente, use un `NEXT_PUBLIC_TENANT_ID` sin membresía y confirme HTTP 403 al acceder a una operación que exige contexto de rol.
3. Cierre la pestaña, ábrala de nuevo y confirme que se solicita otra sesión; el token no se conserva en `localStorage`.

## 6. Vuelta atrás a `headers`

Úsela solo como medida temporal en un entorno controlado. Cambie ambos lados juntos y reinicie backend y frontend para que Next.js reconstruya sus variables públicas:

```powershell
# Backend, antes de iniciarlo
$env:AUTH_MODE = 'headers'

# Frontend, antes de `npm run dev` o `npm run build`
$env:NEXT_PUBLIC_AUTH_MODE = 'headers'
```

En este modo el servidor confía en cabeceras declaradas por el cliente; no es adecuado para producción con usuarios reales. Para volver a Google, fije ambos valores en `oidc`, restaure los dos Client ID y el tenant, y reinicie ambos procesos.

## 7. No verificado

- `governance/tareas/OPS-05.md`, `ADPA.md` y la sección `BL-48` de `governance/apoyo/BRIEFS_POR_BLOQUE.md` no existen en este checkout; el encargo adjunto fue la especificación operativa disponible.
- No se accedió a Google Cloud Console ni a los entornos desplegados; sus valores, dominios, consentimiento, audiencia y usuarios de prueba no están verificados.
- No se realizó un login real ni se usaron credenciales reales. Las pruebas automatizadas del repositorio simulan Google; la tarea FE-07 reserva la prueba real al propietario (`governance/tareas/FE-07.md:28-29`).
- No se verificó una base local con un usuario y una membresía reales, ni una respuesta real de `/api/v1/organizacion/me/roles`.
- Las vistas previas con URL variable no están cubiertas: cada origen debe registrarse previamente y el repositorio indica probar el SSO real solo en local y producción (`governance/tareas/FE-07.md:28-29`).
