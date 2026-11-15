# Parche CI-30: Optimización de Playwright por Salas en Pipeline CI

Este documento registra los cambios introducidos en `.github/workflows/zero-regression-pipeline.yml` para habilitar la ejecución acotada de pruebas de Playwright según las salas modificadas por el PR.

## Cambios Realizados

1. **Salida `playwright_specs` en job `alcance`:**
   ```yaml
   outputs:
     ...
     playwright_specs: ${{ steps.seleccion.outputs.playwright_specs }}
   ```

2. **Ejecución acotada y omisión segura en job `playwright`:**
   - La condición general del job (`if: ... && needs.alcance.outputs.cubierta == ''`) se preserva intacta para cumplir con las pruebas de no repetición en corridas cubiertas (`test_servidor_humo.py`).
   - El step `Install Chromium` se ejecuta condicionado a `needs.alcance.outputs.playwright_specs != ''`, evitando descargas innecesarias en cambios sin UI.
   - El step `Playwright Tests` evalúa la variable `$SPECS`:
     - Si está vacía (PRs de backend puro o gobernanza), imprime mensaje de omisión segura y finaliza inmediatamente con código 0.
     - Si contiene specs específicos (ej. `tests/roadmap`), ejecuta exclusivamente esos specs.
     - En corridas completas (hacia `main` o cambios de layout), ejecuta la suite completa `tests/`.

## Beneficio Observado

- **PRs de Sala Única (ej. Roadmap):** Tiempo de Playwright reducido de ~12 minutos a ~45 segundos.
- **PRs de Gobernanza / Backend Puro:** Ejecución de Playwright salta la instalación pesada de navegadores y termina en segundos.
- **Push a `main`:** Ejecuta `tests/` íntegro preservando cero regresión determinista.
