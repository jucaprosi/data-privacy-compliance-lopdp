### GCP-03b · client-id-de-google-incrustado-al-compilar-la-imagen-web-y-e  (tanda 89)

**Prioridad: incidente de producción.** Va antes que cualquier otra ficha. Es la corrección del login: la revisión `evydentia-web-00004-xkg` muestra «Falta configurar NEXT_PUBLIC_GOOGLE_CLIENT_ID». El propietario ya volvió a `web:v2` y el frontend nuevo espera esta corrección.

**Contexto.** Sala: `frontend`. Depende de: `EP-02`, `GCP-01`, `GCP-03`, `GCP-08`, `GCP-09`, `GCP-10`, `QA-12`, `RET-05`. Especificaciones: `governance/tareas/GCP-03b.md` y `governance/especificaciones/GCP-03b.md` (manda la especificación).

**Cómo se ejecuta** (esta sesión no tiene el contexto del equipo; todo lo necesario está aquí y en la ficha).

- **Rama:** `tarea/juan-carlos/gcp-03b`, creada desde `origin/main` (`git fetch origin` y `git switch -c tarea/juan-carlos/gcp-03b origin/main`), en un worktree propio fuera del escritorio.
- **Ficha:** en tu propio PR pon `estado = "en_curso"` en `governance/tareas/GCP-03b.md`. No la marques «hecha».
- **Un PR por ficha.** No lo fusiones: el propietario se lo pasa al CTO, que lo simula y lo fusiona.
- **Entorno:** sin `.env`; la configuración sale de variables de entorno. Las pruebas que abren la base usan el PostgreSQL 16 local (`.\scripts\entorno_local.ps1`) y `exigir_base_de_pruebas()`. Nunca producción ni una base compartida.
- **No edites** `.github/workflows/`, `verificadores/`, `AGENTS.md` ni `.claude/`. Las líneas `node-version` del workflow las cambia el propietario.
- Archivos nuevos en LF; no cambies el estilo de líneas de los existentes. Pruebas sin `import yaml` (usa `tests/_lector_yaml.py`).
- Antes de pedir revisión: `python scripts/generar_indice_tareas.py --verificar`, `python scripts/verificar_reparto.py` y el árbitro de abajo, con su salida en el PR.

**Objetivo** (en este orden):

1. `GCP-03b` — Client id de Google incrustado al compilar la imagen web y etiqueta por commit

- La etapa `builder` del Dockerfile declara `NEXT_PUBLIC_GOOGLE_CLIENT_ID` como argumento, y un árbitro impide que se pierda.
- La imagen web se etiqueta con el commit (`_ETIQUETA`), no con `v2`.

**Rastro ¤**:

- `¤arbitro`, `¤seguridad`.

**Escribe** (lista exclusiva):

  - `frontend/Dockerfile.cloudrun`
  - `frontend/cloudbuild.yaml`
  - `tests/test_gcp03_frontend_cloudrun.py`

**No hagas:**

- No escribas fuera de la lista anterior. No cambies los YAML de `governance/operaciones/entornos/`.
- No construyas ni publiques la imagen en producción: lo hace el propietario después de la fusión.
- No toques producción ni una base compartida; no despliegues.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `GCP-03b`: pytest tests/test_gcp03_frontend_cloudrun.py; mutaciones m1 a m4; tras la fusión, el propietario construye con _ETIQUETA=<commit> y el login muestra «Continuar con Google».
- Condición 1: construir la imagen en local con `docker build -f Dockerfile.cloudrun --build-arg NEXT_PUBLIC_GOOGLE_CLIENT_ID=<id> .` y comprobar que el id aparece en `.next/static`.
- Condición 2: `frontend/cloudbuild.yaml` falla si no se pasa `_ETIQUETA`.
- `python scripts/generar_indice_tareas.py --verificar` con código 0.
