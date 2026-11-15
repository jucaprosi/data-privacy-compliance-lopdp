### BL-326 · inferencia-cliente-de-ia-anterior-retirado  (tanda 70)

**Contexto.** Sala: `inferencia`. Depende de: `RET-00`, `RET-01a`, `IA-04`, `DIAG-07`. Especificaciones: `governance/tareas/RET-04.md`.

**Objetivo** (en este orden):

1. `RET-04` — Cliente de IA de la plataforma anterior retirado; los proveedores hablan solo con Vertex AI

**Rastro ¤**:

- `¤arbitro`: registrado en `VPA_MAP.md`.
- `¤esquema-asistente`: registrado en `VPA_MAP.md`.
- `¤validar-salida-asistente`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `app_core/ai/deepseek_client.py`
  - `app_core/ai/__init__.py`
  - `features/ai_copilot/services/assistant_provider.py`
  - `features/preanalisis/services/proveedor.py`
  - `features/roadmap/ai/client.py`
  - `tests/test_ai_copilot_motivo_neutro.py`
  - `tests/test_preanalisis.py`
  - `tests/test_preanalisis_motivo_neutro.py`
  - `tests/test_ia07_asistente_inferencia.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- No uses la base ni el proyecto de producción.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `RET-04`: pytest tests/test_ai_copilot_motivo_neutro.py tests/test_preanalisis.py tests/test_preanalisis_motivo_neutro.py tests/test_ia07_asistente_inferencia.py + suite completa en el CI
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.
