+++
id = "RET-04"
titulo = "Cliente de IA de la plataforma anterior retirado; los proveedores hablan solo con Vertex AI"
ola = "backlog"
estado = "pendiente"
sala = "inferencia"
depende_de = ["RET-00", "RET-01a", "IA-03", "IA-04", "IA-07", "DIAG-07"]
propiedad = ["app_core/ai/deepseek_client.py", "app_core/ai/__init__.py", "features/ai_copilot/services/assistant_provider.py", "features/preanalisis/services/proveedor.py", "features/roadmap/ai/client.py", "tests/test_ai_copilot_motivo_neutro.py", "tests/test_preanalisis.py", "tests/test_preanalisis_motivo_neutro.py", "tests/test_ia07_asistente_inferencia.py"]
crea = []
arbitro = "pytest tests/test_ai_copilot_motivo_neutro.py tests/test_preanalisis.py tests/test_preanalisis_motivo_neutro.py tests/test_ia07_asistente_inferencia.py + suite completa en el CI"
rastros = ["¤arbitro", "¤esquema-asistente", "¤validar-salida-asistente"]
+++

# RET-04 · Cliente de IA anterior retirado

Mapa del programa: `governance/partes/arquitecto/2026-11-14_COBERTURA_PLATAFORMA_UNICA.md` (fila RET-04). Especificación del Arquitecto: `governance/especificaciones/RET-04.md` (por redactar; la ficha no se lanza sin ella). Modelo sugerido: sonnet.

**Problema.** El árbol conserva el cliente del proveedor de IA anterior y sus variables, y tres proveedores (asistente, preanálisis y roadmap) todavía conservan su rama. La IA de EVYDENTIA habla solo con Gemini en Vertex AI.

**Entrega.**
- Se borra el cliente de IA anterior en `app_core/ai/` (`deepseek_client.py`) y sus variables; `app_core/ai/__init__.py` deja de exportarlo.
- Se reescriben hacia Vertex AI `features/ai_copilot/services/assistant_provider.py`, `features/preanalisis/services/proveedor.py` y `features/roadmap/ai/client.py`: solo cambia la parte de la plataforma anterior; el contrato de cada proveedor y lo que afirma cada prueba no cambian.
- En `assistant_provider.py` los tokens `¤esquema-deepseek` y `¤validar-salida-deepseek` pasan a `¤esquema-asistente` y `¤validar-salida-asistente`, que ya están indexados en `VPA_MAP.md`.
- Se reescriben sus pruebas de dominio (`test_ai_copilot_motivo_neutro`, `test_preanalisis`, `test_preanalisis_motivo_neutro`, `test_ia07_asistente_inferencia`) sin nombrar la plataforma anterior.
- Árbitro: la suite existente en verde. Ningún árbitro ni invariante nombra la plataforma retirada.

**Cesiones y orden.** Toma `app_core/ai/deepseek_client.py` de IA-08 y los proveedores de IA-06 e IA-09: esas tres fichas dependen de RET-04. Depende de IA-04 y de DIAG-07, que poseen hoy `proveedor.py` y las pruebas de preanálisis. `requirements.txt` (el paquete `openai`) sigue siendo de IA-08.
