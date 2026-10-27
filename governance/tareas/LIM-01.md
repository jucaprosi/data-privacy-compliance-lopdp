+++
id = "LIM-01"
titulo = "Se retiran el módulo de diagnóstico y el panel de copiloto antiguos, que nadie monta"
ola = "D"
estado = "hecha"
sala = "frontend"
depende_de = ["API-01", "FE-17", "FE-16"]
propiedad = ["frontend/src/components/modules/DiagnosticoModule.tsx", "frontend/src/components/modules/RagCopilotPanel.tsx", "frontend/src/lib/api.ts", "frontend/tests/api/**", "frontend/tests/legal/citas.spec.ts", "tests/test_sin_respaldos_inventados.py", "tests/test_sin_codigo_huerfano.py"]
arbitro = "pytest tests/test_sin_codigo_huerfano.py tests/test_sin_respaldos_inventados.py + suite Playwright completa + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤frontend-ide", "¤arbitro"]
+++

# LIM-01 · Retiro de pantallas reemplazadas

**Hallazgo (2026-10-26, revisión de API-01).** Dos componentes ya no se usan en ninguna parte:
- `DiagnosticoModule.tsx` (722 líneas): la sala de diagnóstico usa `NormativaWorkspace`;
- `RagCopilotPanel.tsx`: el copiloto del panel derecho es `CopilotWorkspace`.

Nadie los importa, salvo pruebas que solo leen su código. Confunden a quien mantiene la plataforma y obligan a cuidar código muerto (API-01 tuvo que corregirlos sin poder verlos en pantalla).

## Entrega
- Se borran `DiagnosticoModule.tsx` y `RagCopilotPanel.tsx`.
- En `frontend/src/lib/api.ts` se retiran las funciones que solo ellos usaban: `getPreguntasDiagnostico`, `evaluarDiagnostico`, `getInformeMarkdown` y `consultarCopilotoRAG`. También `getEvidencias`, que nadie usa. Antes de borrar cada una, se comprueba con una búsqueda que no tenga otros usos.
- Se ajustan las pruebas que los leían: el caso «módulos no cableados» de `frontend/tests/api/sin-respaldos.spec.ts` y las referencias de `frontend/tests/legal/citas.spec.ts`.
- **Árbitro nuevo `tests/test_sin_codigo_huerfano.py`:** falla si un archivo de `frontend/src/components/modules/` no lo importa ningún archivo de `frontend/src` (sin contar pruebas), indicando el archivo.
  - `CapaModule.tsx` queda en una lista de excepción con la nota «se monta en CAPA-01». CAPA-01 debe retirarlo de la lista al montarlo.
- **Prueba de mutación documentada:** crear un componente sin importar en `modules/` y comprobar que el árbitro falla.

## Límites
- No toca las rutas del servidor (`/diagnostico/*`, `/rag/*`): siguen en uso o se revisan aparte.
- No toca `CapaModule.tsx`, `CapaBoard.tsx` ni `capaActions.ts` (son de CAPA-01).

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y los checks del PR están en verde. No modificó ningún archivo fuera de su propiedad.
