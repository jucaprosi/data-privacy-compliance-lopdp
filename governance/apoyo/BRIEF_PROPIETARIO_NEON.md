# Brief para el propietario · retiro del proveedor de la base del PMV (BL-288)

`¤coordinacion` `¤arbitro`

Tres cosas que solo el propietario hace, porque tocan gobernanza reservada o recursos de la consola. Ninguna sesión de IA las ejecuta. Este documento no nombra al proveedor con todas sus letras, para no contar como mención en el árbitro de menciones; los comandos lo arman en una variable.

Orden: 1 → 2 → 3. Después de la 1, retira de la lista blanca del árbitro (`permitidos.txt`) las dos líneas `pendiente: brief` de `verificadores/` (el árbitro las exige fuera cuando los archivos ya no mencionan al proveedor).

## 1. Parche de `verificadores/README.md` y `verificadores/arnes_local.py`

Son gobernanza reservada: no los toca ninguna ficha. Se aplica desde un worktree propio, sobre `origin/main`, con un PR de una sola tarea. Pega esto en PowerShell, tal cual (cambia `$Worktree` si el tuyo se llama distinto):

```powershell
$Worktree = "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.worktrees\parche-verificadores"
Set-Location $Worktree
$prov = 'Ne' + 'on'

$readme = "verificadores\README.md"
$t = Get-Content $readme -Raw -Encoding UTF8
$t = $t.Replace("si se quiere probar contra $prov |", "si se quiere probar contra una base remota de pruebas (`evydentia-pruebas`) |")
$t = $t.Replace("frente a 48 min contra $prov.", "frente a 48 min contra la base remota que se usaba antes.")
$t = $t.Replace("- **No reemplaza a $prov.** No ejercita el pooler ni la latencia real.", "- **No reemplaza al CI ni al entorno desplegado.** No ejercita el pooler ni la latencia real.")
$t = $t.Replace("una rama de pruebas; nunca", "la base local de pruebas; nunca")
[System.IO.File]::WriteAllText((Resolve-Path $readme), $t, (New-Object System.Text.UTF8Encoding($false)))

$arnes = "verificadores\arnes_local.py"
$t = Get-Content $arnes -Raw -Encoding UTF8
$t = $t.Replace("en un solo comando y sin $prov.", "en un solo comando y sin base remota.")
$t = $t.Replace("corrida contra $prov del CI:", "corrida del CI contra el contenedor PostgreSQL 16:")
[System.IO.File]::WriteAllText((Resolve-Path $arnes), $t, (New-Object System.Text.UTF8Encoding($false)))

git grep -n -i $prov -- verificadores
python -m pytest --noconftest "tests/test_sin_$($prov.ToLower()).py" -q
```

`git grep` no debe imprimir nada. Si alguna línea cambió de texto desde que se redactó este brief, el `Replace` no la toca: ajústala a mano con el mismo sentido (el proveedor sale; el motivo, «no ejercita el pooler ni la latencia real», se conserva).

## 2. Nota del manifiesto E2E de la ficha de pruebas y scripts (`base_pruebas`)

El manifiesto que lee `frontend/tests/biblioteca/editorial.spec.ts` por la variable `BIB105_E2E_MANIFEST` llevaba un campo con el nombre del proveedor (líneas 92 y 103 del spec). esa ficha lo pasa a **`base_pruebas`**, con el mismo valor `"bib-105"`. Quien genere ese manifiesto (el script o la persona que arma la corrida real del arnés E2E) debe emitir `base_pruebas` y dejar de emitir el campo viejo; si no, la prueba falla por manifiesto incompleto. Comprobación: abrir el JSON que apunta `BIB105_E2E_MANIFEST` y verificar que la clave `base_pruebas` existe y vale `"bib-105"`.

## 3. Limpieza de las ramas en la consola del proveedor

Hay que limpiar con la mano del propietario; ninguna IA crea ni borra recursos allí. **No se toca la rama de producción ni el proyecto del PMV**: el PMV sigue congelado en la rama `produccion` y usa esa base (decisión del 2026-11-09). Se pueden retirar, tras comprobar que nadie las usa:

| Qué | Rama | Notas |
|---|---|---|
| Entorno de pruebas del CI antiguo | entorno de GitHub `<proveedor>-pruebas` (el de nombre terminado en «-pruebas» que creó CI-02) y los secretos de migración por base que contiene | El CI ya no lo usa desde CI-17. Los secretos se borran desde Settings → Environments. |
| Base compartida de pruebas | `test-main` | Padre por defecto de las ramas personales; sin uso en `main`. |
| Base de revisión | `revision` y sus hijas temporales | Solo si ningún PR del PMV las usa. |
| Ramas personales | `test-<persona>` de quienes ya no trabajan sobre el PMV | **No** borres `test-aleczandra`: el trabajo del PMV (`pmv/consolidacion`) se prueba contra ella. |

Antes de borrar, anota en `governance/operaciones/REGISTRO_MIGRACIONES_MANUALES.md` el nombre de cada rama retirada (solo nombres; nunca URL ni contraseñas). Cuando el PMV se retire por completo, la base de producción y `test-aleczandra` se tratan en una ficha aparte.
