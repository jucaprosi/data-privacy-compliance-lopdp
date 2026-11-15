+++
id = "RET-04"
titulo = "Los proveedores de IA operan de forma nativa y exclusiva con Vertex AI"
ola = "backlog"
estado = "hecha"
sala = "inferencia"
depende_de = ["RET-00", "RET-01a", "IA-03", "IA-04", "IA-07", "DIAG-07"]
propiedad = ["app_core/ai/__init__.py", "features/ai_copilot/services/assistant_provider.py", "features/preanalisis/services/proveedor.py", "features/roadmap/ai/client.py", "tests/test_ai_copilot_motivo_neutro.py", "tests/test_preanalisis.py", "tests/test_preanalisis_motivo_neutro.py", "tests/test_ia07_asistente_inferencia.py"]
crea = []
arbitro = "pytest tests/test_ai_copilot_motivo_neutro.py tests/test_preanalisis.py tests/test_preanalisis_motivo_neutro.py tests/test_ia07_asistente_inferencia.py + suite completa en el CI"
rastros = ["¤arbitro", "¤esquema-asistente", "¤validar-salida-asistente"]
+++

# RET-04 · Inferencia nativa exclusiva con Vertex AI

Mapa del programa: `governance/partes/arquitecto/2026-11-14_COBERTURA_PLATAFORMA_UNICA.md` (fila RET-04). Especificación del Arquitecto: `governance/especificaciones/RET-04.md`. Modelo sugerido: sonnet.

**Problema.** Consolidar toda la capa de inferencia (asistente, preanálisis y roadmap) sobre la compuerta única `app_core/pasillo/inferencia.py` con Gemini en Vertex AI.

**Entrega.**
- Todos los módulos (`features/ai_copilot/services/assistant_provider.py`, `features/preanalisis/services/proveedor.py`, `features/roadmap/ai/client.py`) operan únicamente mediante `app_core/pasillo/inferencia.py` sobre Vertex AI.
- En `assistant_provider.py` permanecen los tokens `¤esquema-asistente` y `¤validar-salida-asistente` indexados en `VPA_MAP.md`.
- Sus cuatro pruebas de dominio (`test_ai_copilot_motivo_neutro`, `test_preanalisis`, `test_preanalisis_motivo_neutro`, `test_ia07_asistente_inferencia`) validan el comportamiento con el doble de `features/inferencia`.

**Orden.** Coordinada con `IA-03`, `IA-04`, `IA-06`, `IA-07` e `IA-08`.
