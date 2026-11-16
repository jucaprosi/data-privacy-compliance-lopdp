# Entorno local de ejecución
`¤ci-cd` `¤arbitro`

> El backend, Alembic, los scripts y las pruebas leen **únicamente** variables de entorno del proceso (`os.environ`). No existe `.env` ni `.env.example`: cualquier archivo `.env` en el directorio se ignora. La resolución del intérprete Python/Node vive en `scripts/entorno.bat`, y la configuración de variables locales en PowerShell vive en `scripts/entorno_local.ps1`.

## Precedencia del intérprete

| Intérprete | 1.º | 2.º | 3.º |
| :--- | :--- | :--- | :--- |
| **Python** | la variable `PYTHON_BIN`, si ya está definida | `.venv\Scripts\python.exe` del proyecto | `python` del `PATH` |
| **Node.js** | la variable `NODE_BIN`, si ya está definida | `node` del `PATH` | — |

Después de resolver Python, `scripts/verificar_entorno.py` comprueba que ese intérprete tenga **todos** los requisitos de `requirements.txt` (solo presencia, no versiones). Si falta alguno, el `.bat` se detiene con un mensaje que lo lista y dice cómo resolverlo.

## Preparar el entorno Python

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Para usar otro intérprete sin editar ningún archivo: `set PYTHON_BIN=C:\ruta\a\python.exe` antes de ejecutar el `.bat`.

## Reglas que comprueba `tests/test_entorno_arnes.py`

1. Ningún `.bat` versionado lleva rutas de usuario de una máquina concreta.
2. Todo `.bat` que ejecuta Python o Node lo resuelve mediante `scripts\entorno.bat`.
3. `entorno.bat` sale con 0 si el entorno sirve y con 1, con un mensaje claro, si el intérprete no existe.
4. El intérprete con el que se ejecutan las pruebas cumple `requirements.txt`.

## Variables de entorno del proyecto

| Variable | Uso | Obligatoria fuera de Cloud Run | En Cloud Run (`K_SERVICE`) |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | Base PostgreSQL de la API (`asyncpg` / `psycopg`) | Local (`localhost`, `127.0.0.1`, `::1`); sin definir usa SQLite de desarrollo | Obligatoria, usuario `lopdp_app`, socket `/cloudsql/<proyecto>:<región>:<instancia>` |
| `MIGRATION_DATABASE_URL` | Migraciones (`alembic`), siembra y utilidades | Obligatoria en local (`localhost`, `127.0.0.1`, `::1`) | No aplica en runtime |
| `TEST_DATABASE_URL` | Suite de pruebas con PostgreSQL 16 local o CI | Obligatoria para pruebas con BD (`localhost`, `127.0.0.1`, `::1`) | No aplica |
| `APP_ENV` | Identidad del entorno (`development`, `test`, `pruebas`, `demo`, `production`) | Por defecto `development` | `production` / `pruebas` / `demo` |
| `AUTH_MODE` | `headers` (solo local) u `oidc` (Google OIDC) | `headers` en local; en `pruebas` y `demo` siempre `oidc` | Siempre `oidc` |
| `CORS_ORIGINS` | Orígenes permitidos separados por comas | Por defecto `*` fuera de la nube; en local usar origen explícito | Obligatoria, solo orígenes `https://` sin `*` ni rutas |
| `JWT_SECRET` | Firma de tokens de sesión (mín. 32 chars en nube) | Tiene clave de desarrollo fuera de Cloud Run | Obligatoria desde Secret Manager (`>= 32` chars, propia) |
| `SESSION_SECRET` | Firma de enlaces temporales (mín. 32 chars en nube) | Tiene clave de desarrollo fuera de Cloud Run | Obligatoria desde Secret Manager (`>= 32` chars, distinta de `JWT_SECRET`) |
| `K_SERVICE` | Identificador inyectado por Google Cloud Run | **No definir en local** (activa guardas de nube y prohíbe `headers`) | Inyectada por Cloud Run |
| `HUELLA_PROYECTO_PRODUCCION` | Identificador del proyecto GCP de producción (para guardias `pruebas`/`demo`) | Requerida si `APP_ENV` es `demo` o `pruebas` | Requerida en `pruebas` y `demo` |
| `ANF_STB_URL`, `ANF_API_TOKEN`, `ANF_API_ID`, `ANF_API_PASSWORD` | Integración ANF STB v2 | Opcionales (vacías = sin llamadas remotas) | Secretos cuando firma remota esté activa |

### Guardia única de base local (`app_core/huellas_produccion.py`)

`tests/conftest.py`, `app_core/security.py` (`AUTH_MODE=headers`), `alembic/env.py`, `.githooks/pre-push` y los scripts de utilidades aplican la misma lista blanca de hosts locales: `localhost`, `127.0.0.1`, `::1`. Cualquier host remoto o socket `/cloudsql/` falla cerrado antes de abrir conexión (sin imprimir URLs ni credenciales). En Cloud Run (`K_SERVICE` + `AUTH_MODE=oidc`), el arranque de producción contra Cloud SQL (`/cloudsql/...`) no pasa por la guardia de base local y sigue gobernado por SEC-16, SEC-17 y SEC-20.

## Comandos pegables para trabajo local (PowerShell)

1. Fijar las variables en la ventana actual de PowerShell con PostgreSQL 16 del arnés local (`127.0.0.1:55432`):

```powershell
.\scripts\entorno_local.ps1
```

2. Verificar arranque y migraciones contra PostgreSQL 16 local:

```powershell
.\scripts\entorno_local.ps1
.venv\Scripts\python.exe -m alembic upgrade heads
```

3. Ejecutar pruebas locales (requiere levantar o apuntar al PostgreSQL 16 local):

```powershell
.\scripts\entorno_local.ps1
.venv\Scripts\python.exe -m pytest tests/ -q
```

## Demo y pruebas en local (EP-11)

- **Base:** en local la base es PostgreSQL 16 en `127.0.0.1` (arnés local o túnel `cloud-sql-proxy` en `127.0.0.1` hacia pruebas/demo, nunca producción).
- **Guardia:** con `APP_ENV=demo` o `APP_ENV=pruebas`, `validar_arranque()` (`app_core/entorno/guardias.py`) corta el arranque con `ErrorArranqueEntorno` si `DATABASE_URL` apunta a la base de producción (`apunta_a_produccion`, SEC-20), si falta `HUELLA_PROYECTO_PRODUCCION` o si `AUTH_MODE=headers`. Es un error que impide arrancar y el mensaje nunca muestra la URL.
- **Acceso:** la demo usa OIDC de Google real (`AUTH_MODE=oidc`). El cliente OAuth debe tener `http://localhost:3000` entre los orígenes autorizados y la URI de retorno local.

```powershell
.\scripts\entorno_local.ps1 -AppEnv demo -AuthMode oidc -HuellaProyectoProduccion "<id-proyecto-produccion>"
.\iniciar_todo.bat
```

## Lo que no hace `scripts/entorno.bat`
* No comprueba versiones de los paquetes, solo su presencia.
* No instala nada: indica el comando.
* No cubre `node_modules` del frontend: si falta, falla `tsc` o `next build`.
