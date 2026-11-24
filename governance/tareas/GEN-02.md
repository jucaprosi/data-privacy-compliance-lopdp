+++
id = "GEN-02"
titulo = "Escala de madurez de 1 a 5 sin marca: versión madurez_1_5, contrato, servidor, pantalla y archivo de assessment"
ola = "backlog"
estado = "pendiente"
tanda = 100
sala = "diagnostico, frontend, gobernanza"
depende_de = ["GEN-01", "DIAG-08", "DIAG-09", "DIAG-10", "DIAG-13"]
propiedad = ["governance/contratos/escala_madurez.json", "governance/ESCALA_MADUREZ.md", "Assessment_Madurez_SGPDP.xlsx", "INFORME_SEGURIDAD_PRESENTACION_LOPDP.md", "scripts/verificar_escala_madurez.py", "features/diagnostico/domain/models.py", "features/diagnostico/domain/resultados.py", "features/diagnostico/domain/errores.py", "features/diagnostico/services/dimensiones_sgpdp.py", "features/diagnostico/services/estados_engine.py", "features/diagnostico/services/respuestas_engine.py", "features/diagnostico/services/resultados_engine.py", "api/routers/diagnostico.py", "app_core/pasillo/diagnostico.py", "frontend/src/components/AuditHistory.tsx", "frontend/src/components/DiagnosticCanvas.tsx", "frontend/src/lib/diagnostico/clienteRespuestas.ts", "frontend/src/lib/diagnostico/escala.ts", "frontend/src/lib/diagnostico/indicadores.ts", "frontend/src/lib/dimensionesSGPDP.ts", "frontend/src/store/useAuditStore.ts", "frontend/src/types/index.ts", "frontend/tests/diagnostico/escala-activa.spec.ts", "frontend/tests/diagnostico/escala.spec.ts", "frontend/tests/diagnostico/estados.spec.ts", "frontend/tests/diagnostico/paridad.json", "frontend/tests/diagnostico/paridad.spec.ts", "frontend/tests/diagnostico/simulador.ts", "frontend/tests/cartera/cartera.spec.ts", "frontend/tests/layout/ficha-resumen.spec.ts", "tests/test_diagnostico_escala_1_5.py", "tests/test_diagnostico_resultados.py", "tests/test_roadmap_hallazgos.py", "tests/test_assessment_matriz.py", "tests/test_auditoria_grilla.py", "tests/test_diag07b_siembra_como_admin.py", "tests/duraciones.json"]
crea = ["Assessment_Madurez_SGPDP.xlsx", "tests/test_diagnostico_escala_1_5.py"]
arbitro = "pytest tests/test_diagnostico_escala_1_5.py tests/test_diagnostico_resultados.py tests/test_roadmap_hallazgos.py tests/test_assessment_matriz.py tests/test_auditoria_grilla.py tests/test_escala_madurez.py tests/test_diag07b_siembra_como_admin.py contra PostgreSQL; python scripts/verificar_escala_madurez.py; Playwright frontend/tests/diagnostico/ + cartera.spec.ts + ficha-resumen.spec.ts + tsc --noEmit + npm run build; mutaciones m1 a m3; recuento previo del propietario (R1)."
rastros = ["¤diagnostico-scoring", "¤arbitro"]
+++

# GEN-02 · Escala de madurez de 1 a 5 sin marca: versión madurez_1_5, contrato, servidor, pantalla y archivo de assessment

**Contrato:** `governance/especificaciones/GEN-02.md` (manda sobre esta ficha). Programa: governance/especificaciones/GEN-01.md §0.

**Origen.** Decisión del propietario (2026-11-24), brief del CTO `ARQUITECTO_APP_GENERICA_SIN_MARCA_OPERADOR.md`, medido en `origin/main` ea6d26bf: la aplicación es genérica y la marca del operador sale de forma estructural.

## Entrega
- `ESCALA_SELLADA = "madurez_1_5"` y el contrato `escala_madurez.json` con esa versión y el archivo `Assessment_Madurez_SGPDP.xlsx`, con la misma huella.
- Servidor, pasillo, router, pantalla, almacén y pruebas con el vocabulario final. La prueba de la escala se renombra a `tests/test_diagnostico_escala_1_5.py`.

## Límites
- No se lanza sin el recuento del propietario (especificación R1). Un resultado sellado no se reescribe nunca.
- La migración de Alembic la renombra GEN-06; el contrato OpenAPI lo regenera GEN-05.
