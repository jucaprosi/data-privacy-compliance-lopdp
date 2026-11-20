# Tareas libres y cómo lanzarlas
`¤adpa` `¤arbitro` `¤roadmap` `¤demo` `¤gobernanza`

> **Corte de `origin/main`:** `045ddf7d` (merge de #898, 2026-11-20). Hoja del CTO; se rehace desde `origin/main` en cada corte.
> **Regla de esta hoja (CI-31):** el brief de cada ficha vive solo en `governance/apoyo/briefs/<ID>.md`. Aquí no se copian briefs, para que no se desfasen: cada tarea lleva su estado y la orden de lanzamiento que apunta a su brief.

## 1. Estado de las cuatro tareas

| ID | Brief | Sala | Modelo | Estado al corte | Qué desbloquea |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CI-33` | `briefs/CI-33.md` (#897) | `gobernanza` | Por defecto | **Lista para lanzar.** Ficha y especificación en #895. | R5 del reparto admite la ficha propia y las secciones por sembrar: acaba con el rojo de QA-11 y NORM-02b. |
| `RM-25b` | `briefs/RM-25b.md` (#882, #885) | `roadmap` | Fable | **En curso.** Rama `tarea/juan-carlos/rm-25b` (`b9615eb5`), en el worktree `rm-25b`, sin PR. No se relanza. | `RM-27`, en la misma sesión Fable. |
| `RM-27` | `briefs/RM-27.md` (#882, #885) | `roadmap`, `frontend` | Fable | **Encadenada.** Arranca en la misma sesión cuando el PR de RM-25b esté abierto. Su migración cuelga de `roadmap@head`. | Cierra la revisión humana a cuatro ojos de la hoja de ruta. |
| `DEMO-05d` | Brief pedido al Tech Lead | `demo` | Por defecto | **Bloqueada por DEMO-05c.** Especificación en #901 (`aa8f5958`): cinco triggers, tenant vencido y mutaciones m1 a m6. DEMO-05c tiene la rama terminada (`1ecd7a49`, en el worktree `demo-05c`), pero aún sin PR. | Cierra la purga de la demo con filas de la biblioteca y de las consultas al DPO. |

## 2. Órdenes de lanzamiento

Cada orden se pega en una sesión nueva de VS Code con superpowers. El brief es autosuficiente: rama, «Escribe», «No hagas» y árbitro están en él.

### CI-33 (lanzar ya)

```text
Ejecuta la tarea CI-33 siguiendo al pie de la letra su brief governance/apoyo/briefs/CI-33.md de origin/main (haz git fetch origin antes de leerlo). El contrato es governance/especificaciones/CI-33.md. Trabaja en un worktree propio en C:/Users/Juan Carlos/worktrees-evydentia/ci-33 con la rama tarea/juan-carlos/ci-33 creada desde origin/main. Abre un PR hacia main y no lo fusiones: lo simula y lo fusiona el CTO. Escribe en español.
```

### RM-25b y RM-27 (ya en marcha; no lanzar otra sesión)

La sesión Fable que trabaja en el worktree `rm-25b` sigue con su brief. Cuando abra el PR de RM-25b, continúa en la misma sesión con esta orden:

```text
Con el PR de RM-25b abierto, ejecuta la tarea RM-27 siguiendo su brief governance/apoyo/briefs/RM-27.md de origin/main. Rama tarea/juan-carlos/rm-27 desde origin/main, en su propio worktree. Si RM-25b aún no está fusionado, crea la rama desde la de RM-25b y, cuando se fusione, cambia la base del PR a main (gh pr edit --base main) y revisa el diff. La migración de RM-27 cuelga de roadmap@head. Un PR por ficha; no lo fusiones. Escribe en español.
```

### DEMO-05c (paso previo a DEMO-05d)

La rama está terminada y le falta el PR. La sesión que la hizo, o el propietario, lo abre así:

```powershell
cd "C:\Users\Juan Carlos\worktrees-evydentia\demo-05c"; git fetch origin; git merge origin/main; gh pr create --base main --title "DEMO-05c: purga de la demo con políticas por rol, sin BYPASSRLS" --body "Brief governance/apoyo/briefs/DEMO-05c.md; contrato governance/especificaciones/DEMO-05c.md (#893)."
```

El diff también toca `APORTES_INEDITOS.md` y `FUENTES_Y_BIBLIOGRAFIA.md`, que no están en su «Escribe». Al simular lo reviso: o salen del PR o los justifica el brief.

### DEMO-05d (todavía no)

El orden es:
1. ~~el Arquitecto escribe la especificación~~: hecha en #901;
2. el Tech Lead escribe `briefs/DEMO-05d.md`;
3. se fusiona DEMO-05c;
4. el CTO añade aquí su orden de lanzamiento.

La especificación cumple los seis criterios del CTO de `governance/tareas/DEMO-05d.md` (`d40c9ad1`) y las decisiones de DEMO-05c del 2026-11-19 (#893). La purga corre fuera de las horas de demostración.

## 3. Después de cada fusión

- **Producción:** RM-25b y RM-27 traen migraciones. Se aplican en Cloud SQL junto con las seis pendientes, con el brief `BRIEF_PROPIETARIO_MIGRACION_COMPLETA.md`, pasos 2 a 8.
- **Cierres formales pendientes:** IA-08, IA-09, ORG-23, BOV-04, API-02b, QA-11 (con las dos excepciones del inventario, #900), QA-12 y NORM-02b.
