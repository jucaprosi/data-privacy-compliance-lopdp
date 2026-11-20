+++
id = "ADPA-11"
titulo = "Sembrar la sección #DIAG-14 alrededor de los botones de nivel y de evidencia en DiagnosticCanvas.tsx"
ola = "C"
estado = "hecha"
sala = "diagnostico"
depende_de = ["ADPA-07", "DIAG-03", "DIAG-05", "DIAG-09", "FE-16", "FE-26"]
propiedad = ["frontend/src/components/DiagnosticCanvas.tsx"]
crea = []
siembra = ["frontend/src/components/DiagnosticCanvas.tsx#DIAG-14"]
arbitro = "tsc --noEmit + npx playwright test tests/diagnostico/escala.spec.ts tests/diagnostico/solo-dpo.spec.ts + pytest tests/test_diagnostico_quien_responde.py"
rastros = ["¤adpa", "¤frontend-ide"]
+++

# ADPA-11 · Sección #DIAG-14 en DiagnosticCanvas.tsx

**Origen.** Revisión del Arquitecto a la ficha «solo DPO» de UX/UI (2026-11-08). `DiagnosticCanvas.tsx` tiene tres dueñas vivas por sección (EVI-01, DIAG-07 y DIAG-11), y los botones de nivel y de evidencia quedan fuera de todas. Mismo patrón que ADPA-07.

## Entrega
- Bloques `// --- INICIO DIAG-14 ---` / `// --- FIN DIAG-14 ---` alrededor de los dos grupos de botones (nivel y evidencia), sin cambiar su comportamiento.

## Pruebas
- `tsc --noEmit`, `escala.spec.ts` y `solo-dpo.spec.ts` en verde; `tests/test_diagnostico_quien_responde.py::test_dpo_no_responde` cubre la regla en el servidor.

**Orden (Arquitecto, 2026-11-08).** Va primero, porque solo añade comentarios. EVI-01, DIAG-07 y DIAG-11 dependen de ADPA-11. **Validada por el Arquitecto ADPA (2026-11-08).**
