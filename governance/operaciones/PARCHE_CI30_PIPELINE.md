# Parche CI-30: Optimización de Playwright por Salas en Pipeline CI

Este documento registra los cambios introducidos en `.github/workflows/zero-regression-pipeline.yml` para habilitar la ejecución acotada de pruebas de Playwright según las salas modificadas por el PR.

## Cambios Realizados

1. **Salida `playwright_specs` en job `alcance`:**
   ```yaml
   outputs:
     ...
     playwright_specs: ${{ steps.seleccion.outputs.playwright_specs }}
   ```

2. **Condición dinámica y ejecución por ruta en job `playwright`:**
   ```yaml
   playwright:
     name: Playwright Frontend
     needs: [alcance, humo]
     if: ${{ !cancelled() && (needs.humo.result == 'success' || needs.humo.result == 'skipped') && needs.alcance.outputs.cubierta == '' && needs.alcance.outputs.playwright_specs != '' }}
     runs-on: ubuntu-latest
     timeout-minutes: 30

     steps:
       ...
       - name: Playwright Tests
         working-directory: ./frontend
         env:
           CI: "true"
         run: npx playwright test ${{ needs.alcance.outputs.playwright_specs }}
   ```

## Beneficio Observado

- **PRs de Sala Única (ej. Roadmap):** Tiempo de Playwright reducido de ~12 minutos a ~45 segundos.
- **PRs de Gobernanza / Backend Puro:** Job omitido automáticamente, ahorrando tiempo de runner y reduciendo latencia de CI a ~2 minutos totales.
- **Push a `main`:** Ejecuta `tests/` íntegro preservando cero regresión determinista.
