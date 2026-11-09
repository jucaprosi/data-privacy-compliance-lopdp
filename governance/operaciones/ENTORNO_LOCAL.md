# Entorno local de ejecución
`¤ci-cd` `¤arbitro`

> Cómo se decide qué intérprete usan los `.bat` del proyecto (arnés, arranque del backend) y cómo cambiarlo. La lógica vive en un único sitio: `scripts/entorno.bat`.

## Precedencia

| Intérprete | 1.º | 2.º | 3.º |
| :--- | :--- | :--- | :--- |
| **Python** | la variable `PYTHON_BIN`, si ya está definida | `.venv\Scripts\python.exe` del proyecto | `python` del `PATH` |
| **Node.js** | la variable `NODE_BIN`, si ya está definida | `node` del `PATH` | — |

Después de resolver Python, `scripts/verificar_entorno.py` comprueba que ese intérprete tenga **todos** los requisitos de `requirements.txt` (solo presencia, no versiones). Si falta alguno, el `.bat` se detiene con un mensaje que lo lista y dice cómo resolverlo. Antes se ejecutaba igualmente y el fallo aparecía lejos de su causa: un router sin cargar y un `/health` en 503.

## Preparar el entorno

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

## Demo y pruebas en local (EP-11)

- **Base:** el `.env` del worktree apunta a la rama Neon de pruebas `test-<persona>`. Nunca se usa el `.env` de la carpeta principal, porque ese apunta a producción.
- **Guardia:** con `APP_ENV=demo` o `APP_ENV=pruebas`, `validar_arranque()` (`app_core/entorno/guardias.py`) corta el arranque con `ErrorArranqueEntorno` si `DATABASE_URL` apunta a la base de producción (`apunta_a_produccion`, SEC-15). También lo corta si falta `HUELLA_PROYECTO_PRODUCCION` o si `AUTH_MODE=headers`. Es un error que impide arrancar, no un aviso, y el mensaje nunca muestra la URL.
- **Acceso:** la demo usa OIDC de Google real. El cliente OAuth debe tener `http://localhost:3000` entre los orígenes autorizados y la URI de retorno local. Nunca `AUTH_MODE=headers`.

```powershell
cd "C:\Users\<usuario>\Desktop\Plataforma LOPDP 360\.claude\worktrees\<worktree>"
$env:APP_ENV = "demo"
$env:HUELLA_PROYECTO_PRODUCCION = "<huella-del-proyecto-de-produccion>"
.\iniciar_todo.bat
```

## Lo que no hace
* No comprueba versiones de los paquetes, solo su presencia.
* No instala nada: indica el comando.
* No cubre `node_modules` del frontend: si falta, falla `tsc` o `next build`.
