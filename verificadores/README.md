# Arnés de pruebas

| Comando | Base | Cuándo |
| :--- | :--- | :--- |
| `python verificadores\arnes_local.py` | PostgreSQL local | Mientras se trabaja y al cerrar una sesión |
| `ejecutar_arnes_tres_pilares.bat` | La de `TEST_DATABASE_URL` | Antes de abrir un PR, si se quiere probar contra Neon |
| CI de GitHub | Rama Neon de cada persona | Siempre: es el árbitro antes de fusionar |

## Arnés rápido

Use el Python del entorno virtual del proyecto:

```powershell
& "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" verificadores\arnes_local.py
```

Corre desde la raíz del worktree. Levanta el servidor si está apagado, crea la base, aplica `alembic upgrade head`, instala `frontend/node_modules` si falta y ejecuta **todas** las pruebas, más los controles de BOM y huellas. No compila el frontend.

**Tiempo medido el 2026-10-30:** la suite completa tardó 1 min 30 s en el equipo de Juan Carlos (1382 aprobadas, 22 omitidas), frente a 48 min contra Neon.

El certificado que emite lleva `"base": "postgresql_local"`.

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
