# Arnés de pruebas

| Comando | Base | Cuándo |
| :--- | :--- | :--- |
| `python verificadores\arnes_local.py --base origin/main` | PostgreSQL local | Mientras se trabaja en una sala: solo el alcance del cambio |
| `python verificadores\arnes_local.py` | PostgreSQL local | Al cerrar una sesión: todas las pruebas |
| `ejecutar_arnes_tres_pilares.bat` | La de `TEST_DATABASE_URL` | Antes de abrir un PR, si se quiere probar contra Neon |
| CI de GitHub | Contenedor PostgreSQL 16 en el PR y en el push a `main` (CI-17) | Siempre: es el árbitro antes de fusionar. En un PR corre el arnés por salas o el completo según lo que cambie; en el push a `main`, el completo |

## Arnés rápido

Use el Python del entorno virtual del proyecto:

```powershell
& "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" verificadores\arnes_local.py
```

Corre desde la raíz del worktree. Levanta el servidor si está apagado, crea la base, aplica `alembic upgrade head`, instala `frontend/node_modules` si falta y ejecuta **todas** las pruebas, más los controles de BOM y huellas. No compila el frontend.

**Tiempo medido el 2026-10-30:** la suite completa tardó 1 min 30 s en el equipo de Juan Carlos (1382 aprobadas, 22 omitidas), frente a 48 min contra Neon.

El certificado que emite lleva `"base": "postgresql_local"`.

## Arnés por salas

Un cambio confinado a salas no exige correr todo. `scripts/seleccionar_pruebas.py` clasifica los archivos cambiados:

| Archivo cambiado | Qué corre |
| :--- | :--- |
| `features/<sala>/**`, `api/routers/<r>.py`, `tests/deuda_adpa/<sala>.txt` | Las pruebas de la sala, las de las salas que dependen de ella (también por `app_core.pasillo.<sala>`) y el núcleo |
| `tests/test_*.py` | Esa prueba y el núcleo |
| `frontend/**`, `governance/**`, `docs/**`, `scripts/*`, `verificadores/*`, documentos de la raíz | Las pruebas que nombran la zona o el archivo, y el núcleo |
| Cualquier otro (`app_core/`, `api/`, `alembic/`, `main.py`, `tests/conftest.py`, `.github/`, ...) | Toda la suite |

El **núcleo** son las pruebas que no pertenecen a ninguna sala y las que recorren todo el repositorio (`git ls-files`, `rglob`, `os.walk` o un árbitro de `scripts/verificar_*`): corren siempre. Una prueba pertenece a una sala si importa `features.<sala>` o `app_core.pasillo.<sala>`, o si nombra el prefijo HTTP de un router de la sala. Para ver el mapa:

```powershell
& "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" scripts\seleccionar_pruebas.py --mapa
```

En local, solo el alcance de lo cambiado frente a la rama base:

```powershell
& "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" verificadores\arnes_local.py --base origin/main
```

El certificado declara `"alcance"`: `completo` o `salas: ...`. **Un certificado por salas no cierra una sesión**: el cierre exige la corrida completa.

En el CI, el job «Alcance de la corrida» decide y corre «Arnés por salas» o «Arnés completo», tanto en el PR como en el push a `main` contra el contenedor PostgreSQL 16 del propio runner (CI-17). «Arnés Físico Determinista», el check obligatorio, pasa solo si el arnés que corrió pasó. Un push a `main` corre siempre el completo: la selección es una heurística que amplía lo elegido, y la fusión vuelve a comprobar todo.

Cada corrida del CI (tanto en PR como en el push a `main`) levanta su propio contenedor PostgreSQL 16 temporal dentro del job, sin compartir base ni hacer fila (CI-17). Un push nuevo al mismo PR cancela la corrida anterior, que ya no sirve.

Un commit se verifica una sola vez (`scripts/corrida_cubierta.py`): un PR adopta la corrida del push sobre el mismo commit si pasó y la rama está al día con su base. Desde que no hay ramas `dev/<persona>` (2026-11-05) ninguna rama de tarea tiene push propio y el paso responde «sin cubrir»; se conserva el mecanismo. Si no hubo push, falló o la rama está detrás, el PR corre su propio arnés; la compuerta anota «Cubierto por la corrida N». Mientras espera, «Alcance de la corrida» tarda lo que tarde el push.

## Hook pre-push

`.githooks/pre-push` lleva la norma de correr el arnés antes de subir a un árbitro. Se instala una vez por clon, en Windows, Mac o Linux, y vale para todos sus worktrees:

```bash
python scripts/instalar_hooks.py
```

Sustituye el `pre-push` local (el anterior queda en `pre-push.anterior`) por un envoltorio que ejecuta la versión del hook de cada rama. No usa `core.hooksPath`: una rama anterior al hook perdería el bloqueo de `main`, y `core.autocrlf=true` le dejaría CRLF. Si `core.hooksPath` está definido, el instalador se detiene y dice cómo retirarlo.

| Situación | Efecto |
| :--- | :--- |
| Push a `main`, también para borrarla | Bloquea |
| `arnes_local.py --base origin/main` sale distinto de 0 | Bloquea |
| Arnés en verde | Deja pasar |
| Sin PostgreSQL local o sin un Python con las dependencias | Avisa y deja pasar |
| Rama que no es `tarea/<persona>/<id>`, o sin `origin/main` | Avisa y deja pasar |
| Carpeta principal del clon, worktree sin `.env` o `.env` con producción | Avisa y deja pasar, sin correr nada |
| Lo que se sube no es la cabeza del worktree | Avisa: el arnés prueba lo que hay en el disco, no otra rama |

Solo usa la base local: `arnes_local.py` impone su URL. El CI sigue siendo la compuerta. El hook corre con `--maxfail=1`: se detiene con el primer fallo. El arnés prueba el worktree tal como está, con lo que aún no se haya confirmado. Para el Python, define `LOPDP_PYTHON` si no es el `.venv` del worktree ni el de la carpeta principal. El primer push de un worktree puede tardar más: si las pruebas elegidas lo requieren, el arnés instala `frontend/node_modules`.

## Instalar PostgreSQL local (Windows, sin administrador)

1. Descargue de EnterpriseDB los binarios `postgresql-16.14-1-windows-x64-binaries.zip`.
2. Descomprímalos en `%LOCALAPPDATA%\Programs\PostgreSQL16`, para que exista la carpeta `pgsql`.
3. Inicialice los datos una sola vez:

```powershell
& "$env:LOCALAPPDATA\Programs\PostgreSQL16\pgsql\bin\initdb.exe" -D "$env:LOCALAPPDATA\Programs\PostgreSQL16\datos" -U lopdp_beta_owner --auth=trust -E UTF8 --locale=C
```

El servidor escucha solo en `127.0.0.1:55432`, sin contraseña y sin garantías de escritura. Sirve únicamente para pruebas: no guarde datos reales. Para usar otra carpeta, defina `LOPDP_PG_DIR`.

## Límites

- **No reemplaza a Neon.** No ejercita el pooler ni la latencia real.
- **En un worktree** la suite exige un `.env` propio, aunque la base sea local. Debe contener solo la `TEST_DATABASE_URL` de una rama de pruebas; nunca copie el `.env` principal entero, porque trae producción.
- **Guardias de `tests/conftest.py`:** la suite se detiene si esa URL o `DATABASE_URL` apuntan a producción.
