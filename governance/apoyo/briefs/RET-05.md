### BL-314 · operaciones-una-sola-entrada-de-la-api  (tanda 72)

**Contexto.** Sala: `operaciones, frontend`. Depende de: `RET-01`, `RET-03`, `CI-29`. Especificaciones: `governance/tareas/RET-05.md`.

**Objetivo** (en este orden):

1. `RET-05` — Una sola entrada de la API y despliegue solo en Cloud Run

**Rastro ¤**:

- `¤arquitectura`: registrado en `VPA_MAP.md`.
- `¤frontend-ide`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `vercel.json`
  - `frontend/vercel.json`
  - `api/index.py`
  - `frontend/public/vercel.svg`
  - `.gitignore`
  - `frontend/.gitignore`
  - `tests/test_vercel_despliegue.py`
  - `tests/test_cabeceras_seguridad.py`
  - `tests/test_health_routers.py`
  - `tests/test_gcp03_frontend_cloudrun.py`
  - `tests/test_ret05_una_entrada.py`
  - `pytest.ini`
  - `app_core/security.py`
  - `app_core/bucle_eventos.py`
  - `api/routers/firma_anf.py`
  - `features/roadmap/services/generacion_en_linea.py`
  - `frontend/src/lib/auth/modo.ts`
  - `frontend/next.config.cloudrun.ts`
  - `tests/humo/servidor_humo.py`
  - `tests/test_servidor_humo.py`
  - `tests/plataforma_unica/pendientes/RET-05.txt`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- No uses la base ni el proyecto de producción.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `RET-05`: pytest tests/test_ret05_una_entrada.py tests/test_cabeceras_seguridad.py tests/test_health_routers.py tests/test_sec16_secretos_obligatorios.py tests/test_sec17_configuracion_nube.py + Playwright de frontend/tests/humo/01_arranque.spec.ts + tsc --noEmit + npm run build + suite completa; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

