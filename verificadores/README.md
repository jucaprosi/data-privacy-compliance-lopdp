# Arnés de pruebas

| Comando | Base | Cuándo |
| :--- | :--- | :--- |
| `python verificadores\arnes_local.py --base origin/dev/<persona>` | PostgreSQL local | Mientras se trabaja en una sala: solo el alcance del cambio |
| `python verificadores\arnes_local.py` | PostgreSQL local | Al cerrar una sesión: todas las pruebas |
| `ejecutar_arnes_tres_pilares.bat` | La de `TEST_DATABASE_URL` | Antes de abrir un PR, si se quiere probar contra Neon |
| CI de GitHub | Rama Neon de cada persona | Siempre: es el árbitro antes de fusionar. En un PR corre el arnés por salas o el completo según lo que cambie; en un push, el completo |

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

El **núcleo** son las pruebas que no pertenecen a ninguna sala: corren siempre. Una prueba pertenece a una sala si importa `features.<sala>` o `app_core.pasillo.<sala>`, o si nombra el prefijo HTTP de un router de la sala. Para ver el mapa:

```powershell
& "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" scripts\seleccionar_pruebas.py --mapa
```

En local, solo el alcance de lo cambiado frente a la rama base:

```powershell
& "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" verificadores\arnes_local.py --base origin/dev/juan-carlos
```

El certificado declara `"alcance"`: `completo` o `salas: ...`. **Un certificado por salas no cierra una sesión**: el cierre exige la corrida completa.

En el CI, el job «Alcance de la corrida» decide y corre «Arnés por salas» o «Arnés completo», ambos contra la rama Neon de la persona. «Arnés Físico Determinista», el check obligatorio, pasa solo si el arnés que corrió pasó. Un push a `dev/<persona>` o a `main` corre siempre el completo: la selección es una heurística que amplía lo elegido, y la fusión vuelve a comprobar todo.

Las corridas que comparten la rama de Neon de una persona van de una en una, por orden de llegada: antes de tocar Neon, cada arnés espera a que terminen los de las corridas anteriores (`scripts/esperar_turno_neon.py`). Tres corridas a la vez tardaron casi el triple que una sola. Un push nuevo a la misma rama o al mismo PR cancela la corrida anterior, que ya no sirve.

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
