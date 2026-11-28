+++
id = "ARR-03"
titulo = "Las exportaciones de RAT y de la biblioteca importan sus librerías al usarlas"
ola = "D"
estado = "hecha"
tanda = 121
sala = "rat, biblioteca"
depende_de = []
propiedad = ["features/rat/services/exportacion_engine.py", "features/biblioteca/services/generador_xlsx.py"]
crea = []
arbitro = "pytest tests/ -k \"rat or biblioteca\"; pytest tests/test_adpa_bulkhead.py; mutación m1."
rastros = ["¤arbitro"]
+++

# ARR-03 · Las exportaciones de RAT y de la biblioteca importan sus librerías al usarlas

**Contrato:** `governance/especificaciones/ARR-03.md` (manda sobre esta ficha).

**Origen.** Brief del CTO `ARQUITECTO_ARRANQUE_EN_FRIO_BACKEND.md` (2026-11-27): el arranque en frío tarda hasta 20 s, y casi todo son importaciones de Python. Sin coste nuevo: `min-instances` sigue en 0.

## Entrega
- `pandas`, `openpyxl` y `fpdf` se importan dentro de las funciones de exportación.

## Límites
- Solo mueve importaciones. No cambia firmas, archivos generados ni textos.
- Archivo nuevo con el aviso de autor; LF.
