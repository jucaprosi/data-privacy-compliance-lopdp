+++
id = "API-01"
titulo = "Sin datos inventados cuando el servidor falla: el frontend muestra el error"
ola = "D"
estado = "hecha"
sala = "frontend"
depende_de = ["MTGE-01", "RAT-02", "FE-11", "LEG-01"]
propiedad = ["frontend/src/lib/api.ts", "frontend/src/components/modules/RatModule.tsx", "frontend/src/components/modules/CapaModule.tsx", "frontend/src/components/modules/DiagnosticoModule.tsx", "frontend/src/components/modules/DpoCockpitModule.tsx", "frontend/src/components/modules/RagCopilotPanel.tsx", "tests/test_sin_respaldos_inventados.py", "frontend/tests/api/**", "frontend/tests/legal/citas.spec.ts"]
arbitro = "pytest tests/test_sin_respaldos_inventados.py + Playwright de frontend/tests/api + suite Playwright completa + tsc --noEmit; prueba de mutación documentada"
rastros = ["¤frontend-ide", "¤arbitro"]
+++

# API-01 · Sin datos inventados

**Hallazgo (2026-10-25, revisiones de MTGE-01 y RAT-02).** `frontend/src/lib/api.ts` tiene funciones que, si el servidor falla, **devuelven datos de ejemplo como si fueran reales**: `getPreguntasDiagnostico`, `evaluarDiagnostico`, `getInformeMarkdown`, `getActividadesRAT`, `crearActividadRAT`, `getBitacoraDPO`, `getTicketsCAPA`, `getEvidencias` y `consultarCopilotoRAG`. Un usuario puede ver un RAT, una bitácora del DPO o un diagnóstico que no son de su organización sin saberlo. MTGE-01 retiró el mismo patrón en la calculadora de gran escala.

## Entrega
- Cada función de `api.ts` deja de devolver datos inventados: si el servidor falla, lanza el error (mensaje legible y código HTTP).
- Las pantallas que las usan (`RatModule`, `CapaModule`, `DiagnosticoModule`, `DpoCockpitModule`, `RagCopilotPanel`) muestran un aviso con el motivo (`role="alert"`) y un estado vacío, nunca datos de ejemplo. Donde hoy solo hay `finally` sin `catch`, se añade el manejo del error.
- `tests/test_sin_respaldos_inventados.py`: árbitro estático que falla si una función exportada de `frontend/src/lib/api.ts` devuelve un valor literal (lista, objeto o texto) dentro de un `catch`; indica archivo y línea.
- Playwright en `frontend/tests/api/`: con la API simulada respondiendo 500, cada pantalla muestra el aviso y **ningún** dato de ejemplo (por ejemplo, «RAT-RRHH-001» o «DPO-DICT-01» no aparecen).
- Si alguna prueba existente dependía de los datos de ejemplo, se cambia para simular la API con `page.route`, como el resto del arnés.
- **Prueba de mutación documentada:** devolver una lista de ejemplo en un `catch` de `getActividadesRAT` y comprobar que el árbitro estático y la prueba de la pantalla fallan.

## Límites
- No cambia los colores de esas pantallas (FE-16 y FE-17, que dependen de esta tarea).

## Hecho cuando
- Su árbitro pasa y los checks `Playwright Frontend` y `Arnés Físico Determinista` del PR están en verde. No modificó ningún archivo fuera de su propiedad.
