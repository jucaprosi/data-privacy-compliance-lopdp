### NORM-02b · aviso-a-las-organizaciones-de-resoluciones-nuevas  (tanda 79)

**Contexto.** Sala: `inteligencia_normativa`. Depende de: `NORM-02`, `BOV-01`, `NOTIF-01`. Especificaciones: `governance/especificaciones/NORM-02b.md` (manda), `governance/tareas/NORM-02b.md`.

**Cómo se ejecuta** (esta sesión no tiene el contexto del equipo; todo lo necesario está aquí y en la ficha).

- **Rama:** `tarea/juan-carlos/norm-02b`, creada desde `origin/main` (`git fetch origin` y `git switch -c tarea/juan-carlos/norm-02b origin/main`), en un worktree propio fuera del escritorio.
- **Ficha:** en tu propio PR pon `estado = "en_curso"` en `governance/tareas/NORM-02b.md`. No la marques «hecha».
- **Un PR por ficha.** No lo fusiones: el propietario se lo pasa al CTO, que lo simula y lo fusiona.
- **Entorno:** sin `.env`; la configuración sale de variables de entorno. Las pruebas que abren la base usan el PostgreSQL 16 local (`.\scripts\entorno_local.ps1`) y `exigir_base_de_pruebas()`. Nunca producción ni una base compartida.
- **No edites** `.github/workflows/`, `verificadores/`, `AGENTS.md` ni `.claude/`.
- Archivos nuevos en LF; no cambies el estilo de líneas de los existentes. Pruebas sin `import yaml` (usa `tests/_lector_yaml.py`).
- Antes de pedir revisión: `python scripts/generar_indice_tareas.py --verificar`, `python scripts/verificar_reparto.py` y el árbitro de abajo, con su salida en el PR.

**Objetivo** (en este orden):

1. `NORM-02b` — Aviso a las organizaciones de resoluciones nuevas o modificadas

**Rastro ¤**:

- `¤inteligencia-normativa`, `¤vigilancia-spdp`, `¤seguridad-tenant`.

**Escribe** (lista exclusiva):

  - `features/plataforma/services/destinatarios_normativos_engine.py`
  - `tests/test_norm02b_avisos_organizaciones.py`

**Secciones (en tu PR).** Abre con su marca `# === NORM-02b ===` y `# === fin NORM-02b ===` tus secciones en `app_core/pasillo/plataforma.py`, `features/plataforma/plataforma_service.py`, `app_core/pasillo/notificaciones.py` y `features/inteligencia_normativa/inteligencia_normativa_service.py`, y amplía en el mismo PR la propiedad de la ficha con esas cuatro secciones (`ruta#NORM-02b`). Solo escribes dentro de tus marcas.

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; cruza salas solo por pasillo y compuerta.
- Lee las organizaciones con el mismo mecanismo que ya usa el operador de la plataforma. No crees un rol que salte la RLS ni añadas una política. Si con ese mecanismo no se pueden leer los roles de los usuarios, detente e infórmalo: es decisión del propietario y de Seguridad (R2).
- Ni los registros ni la bitácora guardan correos (R8). Ningún mensaje lleva destinatarios ni nombres de dos organizaciones (R3).
- No uses la base ni el proyecto de producción. No despliegues.
- No edites gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu brief.

**Hecho si** (árbitro exógeno):

- `NORM-02b`: pytest tests/test_norm02b_avisos_organizaciones.py contra un PostgreSQL 16 local en contenedor
- `python scripts/generar_indice_tareas.py --verificar` con código 0.
