+++
id = "EVI-01b"
titulo = "Pantalla de evidencias guardadas en el servidor: subida firmada, store desde el servidor y specs adaptados"
ola = "backlog"
estado = "en_curso"
sala = "frontend"
depende_de = ["CI-15", "EVI-01", "DIAG-04", "FE-14", "FE-16", "FE-26", "DIAG-09", "DIAG-11", "ADPA-07", "ADPA-11"]
propiedad = ["frontend/src/lib/evidencias/**", "frontend/src/components/evidencias/**", "frontend/src/components/modules/EvidenciasModule.tsx#EVI-01", "frontend/src/components/config/CargaEvidencias.tsx", "frontend/src/components/DiagnosticCanvas.tsx#EVI-01", "frontend/src/store/useAuditStore.ts", "frontend/tests/evidencias/**", "frontend/tests/utiles.ts", "frontend/tests/diagnostico/escala-activa.spec.ts", "frontend/tests/purga/purga-normativa-activa.spec.ts", "frontend/tests/roadmap/e2e/criterio12_roles-activa.spec.ts", "frontend/tests/firma/aceptacion.spec.ts", "frontend/tests/ergonomia/colores-diagnostico-activa.spec.ts", "frontend/tests/pmv/sin-subida.spec.ts", "frontend/tests/pmv/sin-subida-activa.spec.ts", "frontend/tests/roadmap/integracion-activa.spec.ts"]
crea = []
arbitro = "npx playwright test frontend/tests/evidencias + los ocho specs adaptados + tsc --noEmit + npm run build; mutaciones documentadas"
rastros = ["¤frontend-ide", "¤evidencias", "¤arbitro"]
+++

# EVI-01b · Pantalla de evidencias guardadas en el servidor: subida firmada, store desde el servidor y specs adaptados

Parte frontend de la ficha original, partida el 2026-11-09 por el Arquitecto ADPA y aprobada por el CTO. **No se lanza hasta que EVI-01 esté fusionada.** Va en una tanda posterior a DIAG-04. BIB-110, EVI-02, DIAG-15 y FIRMA-02 dependen de esta ficha.

## Entrega
- **Enciende la bandera** `EVIDENCIAS_SUBIDA_FIRMADA` y lee `subida_firmada` del estado de evidencias del servicio.
- `registro.ts` sube por el flujo de tres pasos (pedir la subida, subir a la URL firmada, confirmar). El archivo se sigue recordando en la sesión para el preanálisis.
- El store (`useAuditStore.ts`) carga las evidencias de la organización desde el servidor al hidratarse y al iniciar sesión, como las respuestas (DIAG-01). Vincular y desvincular pasan por el servidor. La etiqueta «Temprano explícito» de `useAuditStore.ts` pasa a la escala de EVI-01.
- Hasta el sello del real solo el `dpo` ve el botón de subir y los controles para vincular (`CargaEvidencias.tsx`); después, el `dpo` no ve el botón de subir: ve las evidencias nuevas para validarlas o rechazarlas.
- `DiagnosticCanvas.tsx#EVI-01`: se retira el aviso que dice que los documentos «se guardan solo en este navegador»; el resumen previo al sellado cuenta como respaldados solo los controles con documento registrado en el servidor.
- `EvidenciasModule.tsx#EVI-01` muestra, para cada documento, si está registrado y comprobado en el servidor. Un error de subida (almacén no configurado, tipo rechazado, huella distinta) se muestra tal cual; nunca se registra el documento solo en el navegador como si se hubiera guardado. Colores solo con las variables del tema.
- No toca `frontend/src/lib/config/evidenciaFisica.ts` ni la bandera `__LOPDP_EVIDENCIA_PRUEBAS__`: el interruptor sigue distinguiendo PMV (apagado) de EVYDENTIA (encendido).

## Función de prueba compartida para la subida simulada
Vive **solo** en `frontend/tests/utiles.ts` (sin otra dueña). Mockea con `page.route` las dos rutas nuevas y el PUT a la URL firmada; el mock comprueba que el PUT lleva `x-goog-if-generation-match: 0` y falla si no; admite modos de error (almacén no configurado y huella distinta con 422). Cada spec adaptado cambia **una línea** para usarla y no se reescriben diez. Una guardia (`frontend/tests/evidencias/sin-mocks-sueltos.spec.ts`) comprueba que ningún spec mockea esas rutas por su cuenta; mutación: un `page.route` suelto.

## Specs que se adaptan (solo el flujo de subida y el texto de la carga; no cambies ninguna otra aserción)
- `frontend/tests/diagnostico/escala-activa.spec.ts`
- `frontend/tests/purga/purga-normativa-activa.spec.ts`
- `frontend/tests/roadmap/e2e/criterio12_roles-activa.spec.ts`
- `frontend/tests/firma/aceptacion.spec.ts`
- `frontend/tests/ergonomia/colores-diagnostico-activa.spec.ts`
- `frontend/tests/pmv/sin-subida.spec.ts`
- `frontend/tests/pmv/sin-subida-activa.spec.ts`
- `frontend/tests/roadmap/integracion-activa.spec.ts`
`frontend/tests/incidentes/bitacora.spec.ts` y `frontend/tests/humo/03_descarga.spec.ts` **no** entran: el Arquitecto los midió y no se ven afectados (su «huella» es la de la bitácora de incidentes y la de la exportación del RAT). FIRMA-02 es la dueña de `firma/aceptacion.spec.ts` y depende de esta ficha.

## Pruebas de ausencia
Regla: cada `toHaveCount(0)` o `not.toBeVisible` va precedido, **en el mismo test**, de una aserción positiva del control que lo rodea (no pasa en vacío). Se revisan una por una: `pmv/sin-subida.spec.ts` líneas 118, 125, 130, 142 y 143; `pmv/sin-subida-activa.spec.ts` 83; `diagnostico/escala-activa.spec.ts` 76; `purga/purga-normativa-activa.spec.ts` 108, 109, 119, 120 y 135. `colores-diagnostico-activa` no tiene ausencias.
**El título «Registro de Evidencias con Huella SHA-256» no cambia, o la comprobación pasa a un `data-testid` de la carga**: `pmv/sin-subida.spec.ts:118` comprueba con `toHaveCount(0)` que el título NO aparece con el interruptor apagado, y si se renombra esa aserción deja de proteger nada. Mutación: montar la carga con el interruptor apagado debe hacer fallar `sin-subida.spec.ts` y `sin-subida-activa.spec.ts`.

## Árbitros
- Playwright de `frontend/tests/evidencias`: el DPO sube un documento (con la función compartida) y lo vincula; otra pestaña lo ve tras cargar del servidor; un error de subida se muestra y no deja el documento como guardado.
- Los ocho specs de arriba en verde, `tsc --noEmit` y build.
- Mutación: omitir la confirmación del servidor deja el registro sin crear y el spec lo detecta.

## Límites
Sin backend ni migración: eso es de EVI-01. No cambia las evidencias de la Hoja de Ruta. Textos nuevos de interfaz pasan por UX/UI.
