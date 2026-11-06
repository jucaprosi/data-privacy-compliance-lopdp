# Guion de publicación del PMV en producción
`¤ci-cd` `¤seguridad` `¤rbac-tenant`

> Guion de la primera publicación del PMV (Assessment, Hoja de Ruta y Biblioteca) después del 2026-11-02. Lo ejecutan Juan Carlos, Aleczandra o José. Ninguna sesión de IA migra producción ni publica. Va **después** de fusionar FE-26 y desde `origin/main`. Completa el apartado 6 de `PROCEDIMIENTO_VERCEL.md` y la regla 4 de `REGISTRO_MIGRACIONES_MANUALES.md`; no los sustituye.

## 0. Situación de partida (medida el 2026-11-05)

| Qué | Estado |
| :-- | :-- |
| Rama `produccion` (Vercel) | `6153b08`, del 2026-11-02; 329 commits por detrás de `main` |
| Base `production` (Neon) | `20261102_merge_firma_main` |
| Cabeza de `main` | `20261118_merge_heads_cierre_dev`, una sola cabeza |
| Migraciones pendientes | 24 revisiones: FIRMA-02 (`aceptaciones`) y la Biblioteca (BIB-103 a BIB-401), con 8 fusiones de cabezas |
| Tipo de cambio | Solo aditivo: tablas, funciones, disparadores y permisos nuevos. Ningún `upgrade` reescribe ni borra filas existentes. El código anterior sigue funcionando con el esquema nuevo, así que volver atrás en Vercel no exige tocar la base. |
| Ensayo previo | Obligatorio. El 2026-11-02 se omitió y quedó anotado como desviación de la regla 4. |

Lo mide el paso 1.3. Si al ejecutarlo no coincide, se para y se revisa antes de seguir.

## 1. Preparar la carpeta de publicación

Se publica desde una carpeta nueva, sin `.env` propio, en la cabeza de `origin/main`. Abre **PowerShell** y deja la ventana abierta hasta el final: los pasos siguientes usan sus variables.

**1.1. Precondiciones.** Compruébalas en GitHub antes de empezar:
- FE-26 está fusionado y el CI de `main` está en verde.
- El flujo «Migrar las bases de pruebas de Neon» dejó `test-main` `AL DÍA` en su última ejecución sobre `main`.
- Hay otra persona del equipo disponible para aprobar el PR del paso 7.

**1.2. Carpeta y Python.**

```bash
$raiz = "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"; $fecha = Get-Date -Format "yyyyMMdd"; $pub = "$raiz\.worktrees\publicacion-$fecha"; $py = "$raiz\.venv\Scripts\python.exe"; $herr = "C:\Users\Juan Carlos\Desktop\herramientas"
```

```bash
cd $raiz; git fetch origin; git worktree add --detach $pub origin/main; cd $pub; if (Test-Path .env) { throw "PARAR: la carpeta de publicación no debe tener .env" }; git log -1 --oneline
```

**1.3. Qué se publica.** Debe salir una sola cabeza, `20261118_merge_heads_cierre_dev (head)`, o la que haya en `main` ese día.

```bash
& $py -m alembic heads; git diff --stat origin/produccion origin/main -- alembic/versions | Select-Object -Last 1
```

**1.4. Comprobador de RLS.** Se escribe una vez en la carpeta temporal. Solo imprime nombres de tablas y resultados, nunca datos ni cadenas de conexión.

```bash
@'
import os
import psycopg
url = os.environ["MIGRATION_DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://", 1)
with psycopg.connect(url) as c:
    rol = c.execute("select rolbypassrls, rolsuper from pg_roles where rolname = 'lopdp_app'").fetchone()
    print("lopdp_app sin BYPASSRLS ni superusuario:", "OK" if rol == (False, False) else f"MAL {rol}")
    malas = c.execute("""
        select c.relname from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public' and c.relkind = 'r'
          and exists (select 1 from information_schema.columns k
                      where k.table_schema = 'public' and k.table_name = c.relname and k.column_name = 'tenant_id')
          and not (c.relrowsecurity and c.relforcerowsecurity)
        order by 1""").fetchall()
    print("Tablas con tenant_id sin RLS forzada:", [m[0] for m in malas] or "ninguna")
'@ | Set-Content -Encoding utf8 "$env:TEMP\comprobar_rls.py"
```

Resultado esperado en los pasos 4 y 5: `OK` y `ninguna`. Cualquier otra cosa para la publicación.

## 2. Variables de Vercel (antes de migrar)

**2.1. `SESSION_SECRET` es obligatoria.** `features/biblioteca/services/archivos.py:24` firma los enlaces de descarga con `SESSION_SECRET`, y si falta, con `SECRET_KEY`. Si no existe ninguna de las dos, usa una clave fija que está publicada en este repositorio público, y cualquiera podría falsificar un enlace de descarga. Antes del 2026-11-05 esa variable no figuraba en `VARIABLES_VERCEL.md`.

Se genera con el generador criptográfico de .NET y se carga sin mostrarla, desde la carpeta principal, que es la enlazada al proyecto del backend:

```bash
cd $raiz; $b = New-Object byte[] 48; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b); $s = [Convert]::ToBase64String($b); $OutputEncoding = New-Object System.Text.UTF8Encoding $false; $s | vercel env add SESSION_SECRET production --sensitive --yes; $s = $null; $b = $null; cd $pub
```

**2.2. Comprobar el resto, solo por nombre.**

```bash
cd $raiz; vercel env ls production; cd $pub
```

En el proyecto del **backend** deben estar `DATABASE_URL` (con `lopdp_app`), `JWT_SECRET`, `SESSION_SECRET`, `GOOGLE_CLIENT_ID` y `CORS_ORIGINS`. **No** deben estar:
- `AUTH_MODE` con valor `headers` (`SEC-15`);
- `EVIDENCIA_DIAGNOSTICO` con un valor distinto de `declarada`;
- `EVIDENCIA_FISICA` encendida.

En el proyecto del **frontend**, que no está enlazado en local, se revisa en el panel de Vercel: *Settings* → *Environment Variables*. `NEXT_PUBLIC_EVIDENCIA_FISICA` no debe estar encendida (FE-26).

Si `SESSION_SECRET` o `JWT_SECRET` cambian, las descargas o las sesiones abiertas dejan de valer: quien estuviera conectado vuelve a iniciar sesión. Es esperado.

## 3. Respaldo de producción

Copia de `production` en una rama de Neon, que se conserva hasta la siguiente publicación con respaldo nuevo.

```bash
cd $herr; . .\config_neon.ps1 | Out-Null; $env:PARENT_BRANCH = "production"; $env:BRANCH_PREFIX = ""; powershell -NoProfile -File .\crear_rama_neon.ps1 -Agente "respaldo-$fecha" -PermitirProduccion; Remove-Item ".\rama-respaldo-$fecha.txt" -ErrorAction SilentlyContinue; cd $pub
```

El archivo `rama-respaldo-<fecha>.txt` lleva cadenas con contraseña y el respaldo no se usa para conectar. Por eso se borra al momento.

## 4. Ensayo sobre una copia

Otra copia de `production`, solo para ensayar. Se migra, se comprueba y se borra.

```bash
cd $herr; $env:PARENT_BRANCH = "production"; $env:BRANCH_PREFIX = ""; powershell -NoProfile -File .\crear_rama_neon.ps1 -Agente "ensayo-$fecha" -PermitirProduccion; cd $pub
```

```bash
$f = "$herr\rama-ensayo-$fecha.txt"; $env:MIGRATION_DATABASE_URL = ((Select-String -Path $f -Pattern '^MIGRATION_DATABASE_URL=').Line -replace '^MIGRATION_DATABASE_URL=','').Trim(); if ($env:MIGRATION_DATABASE_URL -match 'ep-late-hall') { Remove-Item Env:MIGRATION_DATABASE_URL; throw "PARAR: la URL del ensayo apunta a producción" }; & $py -m alembic current
```

Debe decir `20261102_merge_firma_main`. Si dice otra cosa, para.

```bash
& $py -m alembic upgrade head; & $py -m alembic current; & $py "$env:TEMP\comprobar_rls.py"; Remove-Item Env:MIGRATION_DATABASE_URL
```

Debe acabar en la cabeza del paso 1.3, con `OK` y `ninguna`. Anota el resultado; va al registro del paso 6.

Después se borra la rama `ensayo-<fecha>` en la consola de Neon (*Branches* → la rama → *Delete*) y su archivo:

```bash
Remove-Item "$herr\rama-ensayo-$fecha.txt"
```

Si el ensayo falla, no se sigue. El error se anota en un PR y se corrige en `main`.

## 5. Migrar producción

La cadena directa de producción se lee del `.env` de la carpeta principal, sin mostrarla. Solo vive en esta ventana mientras dura el paso.

```bash
cd $pub; $env:MIGRATION_DATABASE_URL = ((Select-String -Path "$raiz\.env" -Pattern '^MIGRATION_DATABASE_URL=' | Select-Object -Last 1).Line -replace '^MIGRATION_DATABASE_URL=','').Trim(); if ($env:MIGRATION_DATABASE_URL -notmatch 'ep-late-hall') { Remove-Item Env:MIGRATION_DATABASE_URL; throw "PARAR: esta URL no es la de producción" }; & $py -m alembic current
```

Debe decir `20261102_merge_firma_main`, la misma que en el ensayo.

```bash
& $py -m alembic upgrade head; & $py -m alembic current; & $py "$env:TEMP\comprobar_rls.py"; Remove-Item Env:MIGRATION_DATABASE_URL
```

Debe acabar en la cabeza del paso 1.3, con `OK` y `ninguna`.

## 6. Registrar la migración

El mismo día, en un PR a `main`, se añade una fila a `REGISTRO_MIGRACIONES_MANUALES.md`:
- **Base:** `production`.
- **Revisión:** `20261102_merge_firma_main` → la cabeza del paso 1.3.
- **Origen:** el commit de `main` publicado.
- **Aplicó:** quien lo hizo.
- **Confirmación:** la salida de `alembic current`.
- **Nota:** «aditiva; ensayo previo en `ensayo-<fecha>` correcto; copia previa `respaldo-<fecha>`».

En el mismo PR se quita la fila de «Migraciones previstas».

## 7. Publicar

Igual que el apartado 6 de `PROCEDIMIENTO_VERCEL.md`:

```bash
gh pr create --repo jucaprosi/data-privacy-compliance-lopdp --base produccion --head main --title "Publicación $fecha: PMV" --body "Publica main en producción, ya migrada a la cabeza de Alembic (guion governance/operaciones/PUBLICACION_PMV.md)."
```

Otra persona lo aprueba y se fusiona con *Merge pull request*. Se crean dos despliegues, uno del backend y otro del frontend.

## 8. Verificar

**8.1. Backend.** Debe salir con código 0:

```bash
& $py scripts\verificar_despliegue.py data-privacy-compliance-lopdp.vercel.app
```

**8.2. Recorrido del PMV en producción**, con una organización real y la cuenta de su DPO:
1. **Diagnóstico.** Responder algunas preguntas con nivel de evidencia declarado. La pantalla no ofrece adjuntar archivos (FE-26).
2. **Sello.** Sellar. El aviso dice que la evidencia es declarada y no verificada.
3. **Reporte.** Junto al nivel de evidencia figura «declarada, no verificada» (DIAG-13).
4. **Hoja de ruta.** Se genera, y ninguna vista ofrece «Custodia de Evidencias».
5. **Biblioteca.**
   - El botón muestra el contador, o el aviso si no carga (BIB-116).
   - El catálogo, los borradores y la descarga de una plantilla funcionan, sin errores 422 (BIB-115).
6. **Menú.** No aparece la sala Evidencias.

Si algo falla, se anota con la hora y se decide en el paso 9.

## 9. Si algo sale mal

- **Error en la aplicación:** *Promote to Production* del despliegue anterior en Vercel, en los dos proyectos (`PROCEDIMIENTO_VERCEL.md`, apartado 3, paso 5). Como la migración es aditiva, la base no se toca.
- **Error en la migración a medias:** no se repite `upgrade` a ciegas. `alembic current` dice dónde quedó. `alembic/env.py` no activa `transaction_per_migration`, así que en PostgreSQL todo el `upgrade` corre en una sola transacción: si una revisión falla, se deshace todo y la base sigue en `20261102_merge_firma_main`. Se corrige en `main` y se vuelve al paso 4.
- **Datos dañados**, cosa que estas migraciones no deberían causar: se restaura desde `respaldo-<fecha>` con la función de restauración de ramas de Neon, revisando antes en su consola que el origen sea esa rama. Decide el propietario.

## 10. Limpieza

- **Ahora:**
  - Borrar la carpeta: `cd $raiz; git worktree remove $pub`.
  - Comprobar que en `$herr` no quedan `rama-respaldo-*` ni `rama-ensayo-*`.
- **Cuando producción lleve unos días estable y el recorrido 8.2 esté correcto:** borrar en Neon `respaldo-20261102`. Ya lo reemplaza `respaldo-<fecha>`.
- `respaldo-<fecha>` se conserva hasta la siguiente publicación que cree el suyo.
