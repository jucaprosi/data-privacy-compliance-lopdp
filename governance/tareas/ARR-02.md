+++
id = "ARR-02"
titulo = "La sala NIIF 18 importa pandas al usarlo"
ola = "D"
estado = "hecha"
tanda = 121
sala = "niif18"
depende_de = []
propiedad = ["features/niif18/niif18_service.py", "features/niif18/engines/classifier_engine.py", "features/niif18/engines/diagnostico_engine.py", "features/niif18/engines/export_engine.py", "features/niif18/engines/financials_engine.py", "features/niif18/engines/mpm_engine.py", "features/niif18/engines/parser_engine.py"]
crea = []
arbitro = "pytest tests/ -k niif; pytest tests/test_adpa_bulkhead.py; mutación m1."
rastros = ["¤arbitro"]
+++

# ARR-02 · La sala NIIF 18 importa pandas al usarlo

**Contrato:** `governance/especificaciones/ARR-02.md` (manda sobre esta ficha).

**Origen.** Brief del CTO `ARQUITECTO_ARRANQUE_EN_FRIO_BACKEND.md` (2026-11-27): el arranque en frío tarda hasta 20 s, y casi todo son importaciones de Python. Sin coste nuevo: `min-instances` sigue en 0.

## Entrega
- `pandas` y `openpyxl` se importan dentro de las funciones que los usan, no al cargar la sala.

## Límites
- Solo mueve importaciones. No cambia firmas, resultados ni textos.
- Las anotaciones de tipos usan `from __future__ import annotations` o `TYPE_CHECKING`.
- Archivo nuevo con el aviso de autor; LF.
