+++
id = "PMV-02"
titulo = "Reporte ejecutivo del Assessment: tablero HTML descargable con el nivel 1 a 5 por dimensión, la cobertura, el mapa de dimensiones y las prioridades, sin cifra única"
ola = "indep"
estado = "pendiente"
sala = "frontend"
depende_de = ["DIAG-08", "DIAG-09", "DIAG-13", "PMV-01"]
propiedad = ["frontend/src/lib/reportes/generarReporteAssessment.ts", "frontend/src/lib/reportes/modeloReporteEjecutivo.ts", "frontend/src/lib/reportes/marcaEvydentia.ts", "frontend/src/components/modules/ReportesModule.tsx", "frontend/tests/reportes/reporte-ejecutivo.spec.ts"]
crea = ["frontend/src/lib/reportes/modeloReporteEjecutivo.ts", "frontend/src/lib/reportes/marcaEvydentia.ts", "frontend/tests/reportes/reporte-ejecutivo.spec.ts"]
arbitro = "Playwright de frontend/tests/reportes/reporte-ejecutivo.spec.ts con la API simulada + suite Playwright completa + tsc --noEmit + npm run build; prueba de mutación documentada (añadir un puntaje o nivel de la organización al documento)"
rastros = ["¤diagnostico-reporte", "¤tablero-dimensiones"]
+++

# PMV-02 · Reporte ejecutivo del Assessment

**Origen.** Maqueta de la propietaria «Diagnóstico de Madurez del SGPDP | EVYDENTIA» (carpeta `outputs/…/dashboard-evydentia-propuesta`, fuera del repositorio) y PRD, Módulo 1, apartado «Reporte ejecutivo del Assessment».

**Decisión de la propietaria (2026-11-12).** Las columnas «implicación» y «acción recomendada» de la maqueta quedan fuera: el resultado no las trae y la acción de cada hallazgo vive en la hoja de ruta (`INV_LOPDP_SINGLE_ACTION_PLAN`).

**Contrato:** `governance/especificaciones/PMV-02.md` (manda sobre esta ficha en datos, interfaz y aceptación).

## Entrega
- `generarReporteAssessment.ts`: el documento HTML autocontenido pasa a ser el tablero de la especificación (encabezado, aviso de alcance, indicadores, radar, cobertura por dimensión, mapa de las diez dimensiones, prioridades y anexo), y deja de mostrar puntaje, nivel o porcentaje de la organización.
- `modeloReporteEjecutivo.ts`: funciones puras que derivan del resultado el estado, el orden y el horizonte de las prioridades y los datos del radar; el generador solo da formato.
- `marcaEvydentia.ts`: el logo y los colores de la marca, embebidos (sin recursos externos).
- `ReportesModule.tsx`: la tarjeta del reporte deja de anunciar «Score ponderado» y «nivel de madurez ajustado».
- Todo texto del resultado y de la organización se escapa antes de entrar en el HTML.

## Pruebas
- Los escenarios del apartado 5 de la especificación, uno por prueba.
- Mutación documentada: añadir al documento un puntaje o nivel de la organización y comprobar que la prueba de «sin cifra única» falla.

## Límites
- Sin API nueva, sin datos persistentes, sin migración; nada de Google Cloud.
- No calcula madurez: lee el resultado que ya devuelve `calcularResultadoAssessment("declarado")`.
- Las columnas «implicación» y «acción recomendada» no entran en esta versión.
