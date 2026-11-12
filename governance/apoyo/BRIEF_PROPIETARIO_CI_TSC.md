# Brief para el propietario · CI-20 · `tsc --noEmit` del frontend en el CI
`¤ci-cd` `¤arbitro`

> **Gobernanza reservada.** Este brief lo aplica el propietario: el sub chat no escribe en `.github/`. Ficha `governance/tareas/CI-20.md`.

## Por qué
El 2026-11-08 entró a `main` una regresión de tipos (TS2339 en `frontend/tests/diagnostico/no-aplica.spec.ts`, por dos campos que `FilaRespuesta` no declaraba). Entró en verde porque ningún job del CI corre `tsc`: `next build` y Playwright no revisan los tipos de las pruebas. En el estado actual de `main`, `npx tsc --noEmit` en `frontend/` termina con código 0 (medido en el worktree de esta ficha tras `npm ci`), así que el paso se puede agregar sin arreglar nada antes.

## Qué cambia
Un paso nuevo en `.github/workflows/zero-regression-pipeline.yml`, en el job **`Playwright Frontend`**, justo después de `Install Frontend Dependencies` (`npm ci`) y antes de `Install Chromium`.

Se elige ese job porque:
- ya instala las dependencias del frontend en cada corrida;
- es un check obligatorio de `main` (`PROTECCION_MAIN.md`), así que un error de tipos bloquea la fusión sin tocar la protección de ramas;
- no cambia el nombre de ningún check, de modo que las reglas de `main` siguen valiendo.

Con la corrida cubierta por el push, ese job se omite (igual que hoy): el push a `main` ya lo pasó sobre ese mismo commit.

Bloque a insertar (sangría de dos espacios más que `steps:`, como los pasos vecinos):

```yaml
      - name: Tipos del frontend (tsc --noEmit)
        working-directory: ./frontend
        run: npx tsc --noEmit
```

El script `typecheck` de `frontend/package.json` hace lo mismo (`npm run typecheck`); se usa `npx tsc --noEmit` para que el paso no dependa de que alguien cambie ese script.

## Cómo lo aplica el propietario (PowerShell)

```powershell
$repo = "C:\Users\<usuario>\Desktop\Plataforma LOPDP 360\.claude\worktrees\<worktree-del-propietario>"
$rama = "tarea/<persona>/ci-20-tsc"
cd $repo
git fetch origin
git switch -c $rama origin/main
# Abrir .github/workflows/zero-regression-pipeline.yml y pegar el bloque yaml de arriba
# en el job "Playwright Frontend", entre "Install Frontend Dependencies" e "Install Chromium".
cd "$repo\frontend"
npm ci
npx tsc --noEmit          # debe terminar con código 0
cd $repo
git add .github/workflows/zero-regression-pipeline.yml
git commit -m "ci: CI-20 tsc --noEmit del frontend en el job Playwright Frontend"
git push -u origin $rama
gh pr create --base main --title "ci: CI-20 tsc --noEmit del frontend" --body "Brief: governance/apoyo/BRIEF_PROPIETARIO_CI_TSC.md"
```

## Comprobación (el árbitro de la ficha)
1. El PR del paso nuevo debe quedar en verde en `Playwright Frontend`, con el paso «Tipos del frontend (tsc --noEmit)» visible en el log.
2. Un PR de prueba, que no se fusiona, debe quedar en rojo por un error de tipos deliberado:

```powershell
$repo = "C:\Users\<usuario>\Desktop\Plataforma LOPDP 360\.claude\worktrees\<worktree-del-propietario>"
$rama = "prueba/ci-20-tipos-rojo"
cd $repo
git fetch origin
git switch -c $rama origin/main     # con el paso de CI-20 ya fusionado
Add-Content "$repo\frontend\src\lib\error_de_tipos_deliberado.ts" 'export const x: number = "no es un número";'
git add frontend/src/lib/error_de_tipos_deliberado.ts
git commit -m "prueba: error de tipos deliberado (no fusionar)"
git push -u origin $rama
gh pr create --draft --base main --title "prueba: error de tipos deliberado (no fusionar)" --body "Debe quedar en rojo en Playwright Frontend."
```

   El paso «Tipos del frontend (tsc --noEmit)» debe fallar con `TS2322`. Después, se cierra el PR sin fusionar y se borra la rama:

```powershell
gh pr close $rama --delete-branch
```

3. Ningún check cambia de nombre: la protección de `main` sigue con `Arnés Físico Determinista` y `Playwright Frontend`.
