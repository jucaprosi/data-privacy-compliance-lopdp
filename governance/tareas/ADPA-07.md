+++
id = "ADPA-07"
titulo = "Sembrar secciones #ID en registros y componentes Frontend compartidos para eliminar contención"
ola = "C"
estado = "hecha"
sala = "plataforma, diagnostico, evidencias, biblioteca"
depende_de = ["FE-22", "BIB-101", "DIAG-09"]
propiedad = ["frontend/src/components/layout/menus/index.ts#ADPA-07", "frontend/src/components/layout/pantallas/index.tsx#ADPA-07", "frontend/src/components/layout/DashboardHeader.tsx#ADPA-07", "frontend/src/store/useBibliotecaStore.ts#ADPA-07", "frontend/src/components/DiagnosticCanvas.tsx#ADPA-07", "frontend/src/components/modules/EvidenciasModule.tsx#ADPA-07", "tests/test_adpa07_secciones_frontend.py"]
arbitro = "pytest tests/test_adpa07_secciones_frontend.py + npm --prefix frontend run build"
rastros = ["¤adpa", "¤frontend-ide"]
+++
# ADPA-07 · Sembrar secciones `#ID` en registros y componentes Frontend compartidos para eliminar contención

## Entrega
- Añadir bloques `// --- INICIO <ID> ---` / `// --- FIN <ID> ---` en `menus/index.ts` y `pantallas/index.tsx` para `CAPA-04`, `DIAG-07`, `DPO-03`, `FIRMA-02`, `FOR-01`, `INC-02`, `MTGE-03`, `ORG-18`, `ORG-20`, `CON-01`.
- Sembrar `#FE-25` en `DashboardHeader.tsx` y `#BIB-110` en `useBibliotecaStore.ts`.
- Sembrar `#EVI-01`, `#DIAG-05`, `#DIAG-07` en `DiagnosticCanvas.tsx` y `#EVI-01`, `#EVI-02` en `EvidenciasModule.tsx`, liberando a `DIAG-05` y `DIAG-07` de la dependencia artificial sobre `EVI-01`.

## Pruebas
- `pytest tests/test_adpa07_secciones_frontend.py` verifica que todos los bloques `// --- INICIO <ID> ---` y `// --- FIN <ID> ---` existen y `npm --prefix frontend run build` pasa sin errores.
