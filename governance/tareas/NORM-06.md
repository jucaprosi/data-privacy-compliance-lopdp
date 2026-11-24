+++
id = "NORM-06"
titulo = "El análisis de impacto lee los PDF escaneados: detección del escaneo, transcripción con Gemini en Vertex AI una sola vez por sha256 y falla cerrada"
ola = "backlog"
estado = "pendiente"
tanda = 105
sala = "inteligencia_normativa"
depende_de = ["NORM-03", "NORM-05", "IA-10", "IA-12", "IA-13", "IA-17"]
propiedad = ["features/inteligencia_normativa/services/extraccion.py", "features/inteligencia_normativa/services/impacto.py", "features/inferencia/inferencia_service.py", "features/inferencia/services/cliente_vertex.py", "app_core/pasillo/inferencia.py", "alembic/salas.py", "features/inteligencia_normativa/domain/transcripcion.py", "features/inteligencia_normativa/services/transcripcion_engine.py", "alembic/versions/norm06_transcripciones.py", "tests/test_norm06_pdf_escaneados.py"]
crea = ["features/inteligencia_normativa/domain/transcripcion.py", "features/inteligencia_normativa/services/transcripcion_engine.py", "alembic/versions/norm06_transcripciones.py", "tests/test_norm06_pdf_escaneados.py"]
arbitro = "pytest tests/test_norm06_pdf_escaneados.py tests/test_norm03_impacto_hitl.py tests/test_alembic_cabeza_por_sala.py contra PostgreSQL, con el modelo sustituido por un doble; mutaciones m1 a m7."
rastros = ["¤inteligencia-normativa", "¤copiloto-ia", "¤arbitro"]
+++

# NORM-06 · El análisis de impacto lee los PDF escaneados

**Contrato:** `governance/especificaciones/NORM-06.md` (manda sobre esta ficha).

**Origen.** Decisión del propietario (2026-11-24): los originales escaneados se leen con Gemini en Vertex AI, ni Tesseract ni Document AI. Brief del CTO `ARQUITECTO_NORM_PDF_ESCANEADOS_GEMINI.md`, medido en `origin/main` 38259fcb.

## Entrega
- Una regla pura que distingue un PDF escaneado de uno con texto.
- `transcribir_pdf` en la sala de inferencia y en su pasillo, que manda el PDF como parte `application/pdf`.
- Una tabla `normativa_transcripciones` con una transcripción por `sha256`, con su modelo, su prompt y su fecha.
- El análisis registra si su texto viene de la capa de texto o de una transcripción.
- Falla cerrada: nunca se analiza con las cabeceras del sello.

## Límites
- Sin cambios de cuenta de servicio, variables ni permisos de Vertex: usa los de IA-13 e IA-17.
- Los PDF reales no entran al repositorio. Las pruebas generan los suyos.
