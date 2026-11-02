+++
id = "GOB-04"
titulo = "Flujo de trabajo en equipo: rama desde la punta remota, ciclo diario, dos carpetas de worktrees y un solo escritor de gobernanza"
ola = "D"
estado = "hecha"
sala = "gobernanza"
depende_de = []
propiedad = ["governance/METODOLOGIAS.md#13", "governance/METODOLOGIAS.md#15", ".gitignore", "AGENTS.md", "governance/tareas/GOB-04.md"]
arbitro = "python scripts/generar_indice_tareas.py --verificar; pytest tests/test_indice_tareas.py tests/test_reparto.py tests/test_vpa_map.py tests/test_escala_madurez.py; python verificadores/arnes_local.py"
rastros = ["¤arbitro"]
+++

# GOB-04 · Flujo de trabajo en equipo

**Objetivo.** Dejar escritas en la metodología 13 las directrices del propietario del 2026-11-01 para el trabajo en equipo, después de comprobar cada dato del brief contra el repositorio.

## Entrega
- Directriz: cada rama parte de la punta de `origin/dev/<persona>`, previo `git fetch origin`; el coordinador comprueba el punto de unión al integrar. `dev/<persona>` es el punto de integración de cada colaborador y no se retira.
- Ciclo diario de cuatro pasos: PR de `dev/<persona>` a `main` al cierre, CI en verde, `main` de vuelta a cada `dev/<persona>` por PR, y toda tarea nueva desde esa base.
- Dos carpetas de worktrees documentadas (`.worktrees/` y `.claude/worktrees/`); la segunda pasa a `.gitignore` porque solo estaba en el `info/exclude` local.
- Retirar el worktree al fusionar su PR; la carpeta principal solo para operar.
- Un solo escritor por día para `TASKS.md` y `BRIEFS_POR_BLOQUE.md`: el coordinador, en el PR de gobernanza que cierra la tanda.
- Metodología 15: procedimiento paso a paso, con comandos para Windows y Mac o Linux, para que cada colaborador y cada chat creen el worktree desde la punta remota, escriban su `.env`, verifiquen, abran el PR, retiren el worktree y cierren la jornada; incluye la comprobación de tres líneas que el coordinador repite al integrar.

## Lo comprobado y descartado del brief
- El workflow ya corre para `push` y `pull_request` en `dev/**`; los 53 PR fusionados hacia `dev/*` tienen checks. No hubo corrección de CI.
- `main` sí tiene reglas de rama: borrado y reescritura prohibidos, checks obligatorios con rama al día y fusión por PR.
- `arnes_cero_regresiones.py` ya recorre solo el árbol de git; `test_adpa_bulkhead.py` excluye `.worktrees/` pero no `.claude/`, y `test_sin_sql_interpolado.py` no excluye ninguna de las dos.

## No hagas
- No añadir pruebas, linters, hooks ni scripts; no hacer push ni fusiones a `main`; no tocar ramas ni máquinas de Aleczandra y José.
- No ejecutar las decisiones reservadas al propietario: protección de `main`, los cambios sin commit de la carpeta principal, `rat-06`, `rat-05-bde367`, `ensayo-pg` y el stash `feature/roadmap-ia`.

## Hecho cuando
El índice verifica con código 0, los árbitros de gobernanza pasan y la suite completa corre en primer plano con salida 0.
