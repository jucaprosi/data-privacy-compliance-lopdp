### BL-325 · plataforma-alta-idempotente-de-organizaciones-sinteticas  (tanda 74)

**Contexto.** Sala: `plataforma`. Depende de: `EP-03`, `ORG-11`, `ORG-20`. Especificaciones: `governance/tareas/PLAT-01.md`.

**Objetivo** (en este orden):

1. `PLAT-01` — Alta idempotente de organizaciones sintéticas en plataforma_service, sin invitación

**Rastro ¤**:

- `¤seguridad-tenant`: registrado en `VPA_MAP.md`.
- `¤adpa`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `features/plataforma/plataforma_service.py`
  - `features/plataforma/services/organizacion_sintetica_engine.py`
  - `scripts/datos_sinteticos/organizaciones.py`
  - `tests/test_plat01_organizacion_sintetica.py`
  - `tests/test_ep03_sembrar_entorno.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- No uses la base ni el proyecto de producción.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Riesgo R5 (aviso del CTO, 2026-11-14).** Mientras `exigir_base_de_pruebas()` (RET-01a) no esté en `main`, una prueba NUEVA que use la base choca con R5 y no puede registrarse como deuda ni esquivarse. Si `tests/test_plat01_organizacion_sintetica.py` usa la base, entrega primero el motor y las pruebas sin base, y deja esa parte para cuando RET-01a esté.

**Hecho si** (árbitro exógeno):

- `PLAT-01`: pytest tests/test_plat01_organizacion_sintetica.py tests/test_ep03_sembrar_entorno.py + suite completa; mutación documentada; revisión de Seguridad antes del reparto
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.
