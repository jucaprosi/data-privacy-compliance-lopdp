### API-02b · webhooks-firmados-con-techo  (tanda 1)

**Contexto.** Salas: `pasillo_central`, `frontend`. Depende de: nada abierto. Especificaciones: `governance/tareas/API-02b.md` y `governance/especificaciones/API-02b.md`.

**Cómo se ejecuta** (esta sesión no tiene el contexto del equipo; todo lo necesario está aquí y en la ficha).

- **Rama:** `tarea/juan-carlos/api-02b`, creada desde `origin/main` (`git fetch origin` y `git switch -c tarea/juan-carlos/api-02b origin/main`), en un worktree propio fuera del escritorio.
- **Ficha:** en tu propio PR pon `estado = "en_curso"` en `governance/tareas/API-02b.md`. No la marques «hecha».
- **Un PR por ficha.** No lo fusiones: el propietario se lo pasa al CTO, que lo simula y lo fusiona.
- **Entorno:** sin `.env`; la configuración sale de variables de entorno. Las pruebas que abren la base usan el PostgreSQL 16 local (`.\scripts\entorno_local.ps1`) y `exigir_base_de_pruebas()`. Nunca producción ni una base compartida.
- **No edites** `.github/workflows/`, `verificadores/`, `AGENTS.md` ni `.claude/`.
- Archivos nuevos en LF; no cambies el estilo de líneas de los existentes. Pruebas sin `import yaml` (usa `tests/_lector_yaml.py`).
- Antes de pedir revisión: `python scripts/generar_indice_tareas.py --verificar`, `python scripts/verificar_reparto.py` y el árbitro de abajo, con su salida en el PR.

**Objetivo** (en este orden):

1. `API-02b` — Webhooks firmados HMAC-SHA256 con techo del paquete

**Rastro ¤**:

- `¤seguridad`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `alembic/versions/api02b_webhooks_suscripciones.py`
  - `app_core/integraciones/webhooks.py`
  - `app_core/integraciones/techos.py#API-02b`
  - `api/routers/integraciones_webhooks.py`
  - `tests/test_api02b_webhooks.py`
  - `tests/matriz/API-02b.py`
  - `frontend/src/components/integraciones/IntegracionesView.tsx#API-02b`
  - `frontend/src/components/integraciones/WebhooksPanel.tsx`
  - `frontend/src/lib/integraciones/webhooks.ts`
  - `frontend/tests/integraciones/webhooks.spec.ts`
  - `governance/operaciones/BRIEF_PROPIETARIO_SECRETO_WEBHOOKS.md`

**No hagas:**

- No escribas fuera de la lista anterior.
- Cumple el contrato de `governance/especificaciones/API-02b.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No toques producción ni una base compartida. El secreto `WEBHOOKS_CLAVE_CIFRADO` lo crea el propietario con su brief.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `API-02b`: pytest tests/test_api02b_webhooks.py + test_matriz_permisos.py + Playwright frontend/tests/integraciones/webhooks.spec.ts + tsc --noEmit + build; mutaciones m1 a m5
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.
