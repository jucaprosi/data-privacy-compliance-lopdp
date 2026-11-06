+++
id = "DIAG-13"
titulo = "PMV: el sello conserva la evidencia declarada por el DPO, marcada como no verificada, en lugar de sellarla como E0"
ola = "D"
estado = "pendiente"
sala = "diagnostico"
depende_de = ["DIAG-02", "DIAG-03", "DIAG-08", "DIAG-10", "RM-19"]
propiedad = ["features/diagnostico/services/resultados_engine.py", "features/diagnostico/services/report_generator.py", "features/roadmap/services/contexto_generacion.py", "tests/test_diag13_evidencia_declarada.py", "features/diagnostico/domain/resultados.py", "tests/test_diagnostico_resultados.py", "tests/test_diagnostico_escala_smartcidi.py", "features/diagnostico/diagnostico_service.py#DIAG-13"]
arbitro = "pytest tests/test_diag13_evidencia_declarada.py tests/test_diagnostico_resultados.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + vigilantes; prueba de mutación documentada"
rastros = ["¤diagnostico", "¤evidencias"]
+++

# DIAG-13 · PMV: evidencia declarada, no verificada

**Decisión del propietario (2026-11-05).** El PMV no guarda evidencias: genera el assessment, la hoja de ruta y la Biblioteca con lo que el DPO registra en el diagnóstico. En cada pregunta el DPO puede indicar que hay evidencia (nivel 0 a 4), pero la plataforma no la comprueba físicamente. Contrato: `PRD.md` (ley 3 y Módulo 1) e `INV_LOPDP_PMV_DECLARED_EVIDENCE`.

**Problema.** La regla de respaldo de `DIAG-03` sella como E0 todo control sin un documento comprobado por el servidor (`features/diagnostico/services/resultados_engine.py`, `sellado = declarado if con_documento else 0`). En el PMV nunca hay documentos comprobados, así que todo sale con evidencia 0 y la dimensión de calidad de evidencia queda siempre en cero.

## Entrega
- **Política por configuración** `EVIDENCIA_DIAGNOSTICO`, leída en un solo sitio de `resultados_engine.py`:
  - `declarada` (por defecto, el PMV): se sella el nivel declarado y cada control lleva `evidencia_verificada = false`;
  - `verificada` (EVYDENTIA, con `EVI-01`): se mantiene la regla de `DIAG-03`; `evidencia_verificada` es verdadero solo con documento comprobado.
  - Un valor desconocido hace fallar el arranque.
- **Resultado sellado:** el campo `evidencia_verificada` por control entra en el contenido de la huella. Los resultados ya sellados sin ese campo siguen verificando su cadena: el cálculo de la huella solo lo incluye si existe.
- **Reporte** (`report_generator.py`): junto al nivel de evidencia escribe «declarada, no verificada» cuando corresponde, en el informe ejecutivo y en el técnico.
- **Hoja de ruta** (`contexto_generacion.py`): el contexto que recibe la generación indica que la evidencia es declarada, para que las tareas pidan reunirla y no la den por verificada.
- No se tocan la pantalla ni las rutas de evidencia: en el PMV no se suben archivos al diagnóstico.

## Pruebas
- Con `declarada`, un control con nivel declarado 3 y sin documento se sella con 3 y `evidencia_verificada = false`.
- Con `verificada`, el mismo control se sella con 0 (la regla de `DIAG-03`).
- El reporte muestra «declarada, no verificada» y nunca «verificada» con la política `declarada`.
- Un resultado sellado antes de esta tarea sigue verificando su cadena de huellas.
- Mutación documentada: volver a `sellado = declarado if con_documento else 0` con la política `declarada`; la primera prueba debe fallar.

## Límites
- No cambia el cálculo por dimensión (`DIAG-08`) más allá del nivel de evidencia que recibe.
- No crea almacenamiento de archivos ni usa R2.

## Nota de coordinación
`DIAG-11` (EVYDENTIA, PR #413) también posee `resultados_engine.py`: cuando ambas estén en `main`, `DIAG-11` depende de esta.
