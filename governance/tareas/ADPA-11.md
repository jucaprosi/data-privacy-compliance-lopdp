+++
id = "ADPA-11"
titulo = "Sembrar la sección #DIAG-14 alrededor de los botones de nivel y de evidencia en DiagnosticCanvas.tsx"
ola = "C"
estado = "pendiente"
sala = "diagnostico"
depende_de = ["ADPA-07", "DIAG-03", "DIAG-05", "DIAG-09", "FE-16", "FE-26"]
propiedad = ["frontend/src/components/DiagnosticCanvas.tsx", "tests/test_adpa11_seccion_solo_dpo.py"]
crea = ["tests/test_adpa11_seccion_solo_dpo.py"]
siembra = ["frontend/src/components/DiagnosticCanvas.tsx#DIAG-14"]
arbitro = "pytest tests/test_adpa11_seccion_solo_dpo.py + tsc --noEmit + npx playwright test tests/diagnostico/escala.spec.ts; mutación documentada"
rastros = ["¤adpa", "¤frontend-ide"]
+++

# ADPA-11 · Sección #DIAG-14 en DiagnosticCanvas.tsx

**Origen.** Revisión del Arquitecto a la ficha «solo DPO» de UX/UI (2026-11-08). `DiagnosticCanvas.tsx` tiene tres dueñas vivas por sección (EVI-01, DIAG-07 y DIAG-11), y los botones de nivel y de evidencia quedan fuera de todas. Mismo patrón que ADPA-07.

## Entrega
- Bloques `// --- INICIO DIAG-14 ---` / `// --- FIN DIAG-14 ---` alrededor de los dos grupos de botones (nivel y evidencia), sin cambiar su comportamiento.

## Pruebas (`tests/test_adpa11_seccion_solo_dpo.py`)
1. Los bloques `#DIAG-14` existen, están balanceados y contienen los dos grupos de botones.
2. El diff contra main solo añade líneas de comentario.
3. Las marcas `#EVI-01`, `#DIAG-05`, `#DIAG-07` y `#DIAG-11` quedan intactas.
- `tsc --noEmit` y `escala.spec.ts` en verde.

**Mutación:** cambiar una línea de código hace fallar la prueba 2.

**Orden (Arquitecto, 2026-11-08).** Va primero, porque solo añade comentarios. EVI-01, DIAG-07 y DIAG-11 dependen de ADPA-11. **Validada por el Arquitecto ADPA (2026-11-08).**
