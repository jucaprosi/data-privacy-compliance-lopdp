### BL-327 · notificaciones-boceto-de-correo-anterior-retirado  (tanda 70)

**Contexto.** Sala: `notificaciones`. Depende de: `RET-00`, `RET-01a`. Especificaciones: `governance/tareas/RET-08.md`.

**Objetivo** (en este orden):

1. `RET-08` — Boceto del proveedor de correo anterior retirado; queda el puerto con su doble de pruebas

**Rastro ¤**:

- `¤arbitro`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `features/notificaciones/services/adaptadores.py`
  - `features/notificaciones/services/__init__.py`
  - `features/notificaciones/notificaciones_service.py`
  - `tests/test_notificaciones.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- No uses la base ni el proyecto de producción.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `RET-08`: pytest tests/test_notificaciones.py + suite completa en el CI
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.
