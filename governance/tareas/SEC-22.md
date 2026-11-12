+++
id = "SEC-22"
titulo = "Sin clave de API en el registro del copiloto"
ola = "backlog"
estado = "en_curso"
sala = "ai_copilot"
depende_de = ["ADPA-03"]
propiedad = ["features/ai_copilot/services/inference_engine.py", "tests/test_sec22_sin_clave_en_log.py"]
crea = ["tests/test_sec22_sin_clave_en_log.py"]
arbitro = "pytest tests/test_sec22_sin_clave_en_log.py (con OPENAI_API_KEY=clave-falsa-123, la cadena no aparece en ningún registro capturado con caplog) + suite de ai_copilot; mutación documentada: reponer la línea 38 hace fallar la prueba"
rastros = ["¤seguridad"]
+++

# SEC-22 · Sin clave de API en el registro del copiloto

Diseño del Arquitecto ADPA, 2026-11-12 (`governance/partes/arquitecto/2026-11-12_DISENO_IA10_TRAZABILIDAD.md`, hallazgo de seguridad del CTO). Urgente: no depende de nada, no lleva migración.

## Entrega
- Se borra la línea 38 de `features/ai_copilot/services/inference_engine.py` (`logger.info(f"Intentando invocar LLM con API KEY {api_key}")`) y el `APILoggerFilter`. El filtro no protege: solo mira `record.msg`, solo en ese logger, y la fuga venía del mismo módulo. No se toca nada más del archivo.
- IA-05 pasa a depender de SEC-22, porque las dos poseen ese archivo.

## Árbitro
`tests/test_sec22_sin_clave_en_log.py` captura los registros con `caplog`, fija `OPENAI_API_KEY=clave-falsa-123` y comprueba que la cadena no aparece en ningún registro. Mutación: reponer la línea 38 y la prueba falla.

## Reglas
- Valores simulados; la clave de la prueba es falsa. Sin `import yaml` en pruebas; sin secretos ni URL de conexión.
- No uses el `.env` de la carpeta principal.
