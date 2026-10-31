+++
id = "DIAG-09"
titulo = "Escala SMARTCIDI en la pantalla: responder el nivel 1 a 5 con su criterio y la evidencia 0 a 4, y retirar el porcentaje global del panel ejecutivo"
ola = "D"
estado = "pendiente"
sala = "frontend"
depende_de = ["DIAG-08", "DIAG-10", "FE-17", "FE-22"]
propiedad = ["frontend/src/components/DiagnosticCanvas.tsx", "frontend/src/lib/estadosCumplimiento.ts", "frontend/src/lib/diagnostico/clienteRespuestas.ts", "frontend/src/lib/diagnostico/indicadores.ts", "frontend/src/lib/diagnostico/escala.ts", "frontend/src/lib/dimensionesSGPDP.ts", "frontend/src/lib/assessmentReferencia.ts", "frontend/src/app/actions/scoringActions.ts", "frontend/src/components/dashboard/AssessmentExecutiveSummary.tsx", "frontend/src/components/AuditHistory.tsx", "frontend/src/lib/reportes/generarReporteAssessment.ts", "frontend/src/types/index.ts", "frontend/tests/diagnostico/escala.spec.ts", "frontend/tests/assessmentDashboard.spec.ts", "frontend/tests/utiles.ts#DIAG-09", "frontend/src/store/useAuditStore.ts", "frontend/src/components/dashboard/AssessmentTasksPanel.tsx", "frontend/src/components/preanalisis/PanelPreanalisis.tsx", "frontend/tests/diagnostico/simulador.ts", "frontend/tests/diagnostico/persistencia.spec.ts", "frontend/tests/diagnostico/paridad.spec.ts", "frontend/tests/diagnostico/paridad.json", "frontend/tests/diagnostico/sellado.spec.ts", "frontend/tests/commandPalette.spec.ts", "governance/contratos/escala_madurez.json"]
arbitro = "Playwright de frontend/tests/diagnostico/escala.spec.ts con la API simulada + suite Playwright completa + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤diagnostico", "¤frontend-ide"]
+++

# DIAG-09 · Escala SMARTCIDI en la pantalla

**Decisión del propietario (2026-10-29).** Ver DIAG-08: la madurez sigue la metodología del archivo de assessment SMARTCIDI. Esta tarea lleva la escala a la pantalla.

**Contrato:** `governance/especificaciones/DIAG-09.md` (manda sobre esta ficha en datos, interfaz y aceptación).

## Entrega
- `DiagnosticCanvas.tsx`: el control «Estado de implementación» (tres botones) pasa a **cinco niveles** con su nombre y su criterio operativo visibles; el control de evidencia pasa de E0–E3 a **cinco escalones** (verbal, informal, documental, operativa, revisada). La escala vive en `frontend/src/lib/diagnostico/escala.ts`, sin repetirla en otros archivos.
- El estado («Implementado», «Parcial», «No implementado») se muestra como dato **derivado** que devuelve el servidor, no como entrada.
- `AssessmentExecutiveSummary.tsx` deja de mostrar el puntaje ponderado de la organización («Puntaje según respuestas», «Puntaje con evidencia vinculada») y muestra los niveles por dimensión.
- Un resultado sellado con la escala anterior se muestra con el aviso del contrato, sin convertirlo.
- Llamadas a la API por `fetchAutenticado`; colores solo con las variables del tema; sin tokens de gobernanza en la interfaz.

## Pruebas
- Los escenarios del contrato, con la API simulada.
- Mutación documentada: volver a los tres botones hace fallar la prueba de los cinco niveles.

## Límites
- No cambia el cálculo: todo valor sale de la API de DIAG-08.
- No toca el tablero (`CentralDashboard.tsx`, `tableros/**`), que es de FE-24.
- El modelo de respuesta del diagnóstico vive en `frontend/src/store/useAuditStore.ts`: esta tarea lo cambia a la escala nueva (nivel asignado 1 a 5, evidencia 0 a 4, sin puntaje global) junto con `AssessmentTasksPanel.tsx` y `PanelPreanalisis.tsx`, que leen `cumple` (propiedad ampliada el 2026-10-30). EVI-01 y BIB-110, que también escriben el store, van después de esta tarea y parten del store ya cambiado.
- **Propiedad ampliada (2026-10-31).** El cambio de escala rompe cinco pruebas de tareas «hechas» o sin dueño: `tests/diagnostico/simulador.ts` (FE-22), `persistencia.spec.ts` (DIAG-01), `commandPalette.spec.ts` (TEST-02), `sellado.spec.ts` y `paridad.spec.ts` con su `paridad.json`; esta tarea las adapta a la escala nueva. Además, `governance/contratos/escala_madurez.json` pierde por `scripts/verificar_escala_madurez.py --escribir` las anotaciones cumplidas de DIAG-09 y la de EVI-01 en `useAuditStore.ts`; no se editan a mano ni se tocan las anotaciones de EVI-01 en `models.py` y `evidencias.py`.
- Si una prueba fuera de la lista de propiedad se rompe por el cambio de escala, detente e informa; no la edites.
