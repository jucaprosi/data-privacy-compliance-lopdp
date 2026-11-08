+++
id = "ADPA-11"
titulo = "Sembrar la sección #DIAG-14 alrededor de los botones de nivel y de evidencia en DiagnosticCanvas.tsx"
ola = "C"
estado = "pendiente"
sala = "diagnostico"
depende_de = ["EVI-01", "DIAG-07", "DIAG-11"]
propiedad = ["frontend/src/components/DiagnosticCanvas.tsx", "tests/test_adpa11_seccion_solo_dpo.py"]
crea = ["tests/test_adpa11_seccion_solo_dpo.py"]
siembra = ["frontend/src/components/DiagnosticCanvas.tsx#DIAG-14"]
arbitro = "pytest tests/test_adpa11_seccion_solo_dpo.py + npm --prefix frontend run build + tsc --noEmit"
rastros = ["¤adpa", "¤frontend-ide"]
+++

# ADPA-11 · Sección #DIAG-14 en DiagnosticCanvas.tsx

**Origen.** Revisión del Arquitecto a la ficha «solo DPO» de UX/UI (2026-11-08). `DiagnosticCanvas.tsx` tiene tres dueñas vivas por sección (EVI-01, DIAG-07 y DIAG-11), y los botones de nivel y de evidencia quedan fuera de todas. Mismo patrón que ADPA-07.

## Entrega
- Bloques `// --- INICIO DIAG-14 ---` / `// --- FIN DIAG-14 ---` alrededor de los dos grupos de botones (nivel y evidencia), sin cambiar su comportamiento.

## Pruebas
- `tests/test_adpa11_seccion_solo_dpo.py`: los bloques existen, están balanceados y contienen los dos grupos de botones.
- El build y `tsc --noEmit` pasan.

**Orden.** Posee el archivo entero, así que va después de las tres dueñas de sección. Si el propietario quiere adelantarla, las tres pasan a depender de ADPA-11.
