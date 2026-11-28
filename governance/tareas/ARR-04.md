+++
id = "ARR-04"
titulo = "Prueba de presupuesto de arranque del backend (librerías y módulos)"
ola = "D"
estado = "en_curso"
tanda = 122
sala = "pruebas"
depende_de = ["ARR-02", "ARR-03"]
propiedad = ["tests/test_arr04_arranque.py", "features/niif18/engines/export_engine.py"]
crea = ["tests/test_arr04_arranque.py"]
arbitro = "pytest tests/test_arr04_arranque.py; mutaciones m1 y m2."
rastros = ["¤arbitro"]
+++

# ARR-04 · Prueba de presupuesto de arranque del backend

**Contrato:** `governance/especificaciones/ARR-04.md` (manda sobre esta ficha).

**Origen.** Brief del CTO `ARQUITECTO_ARRANQUE_EN_FRIO_BACKEND.md` (2026-11-27): el arranque en frío tarda hasta 20 s, y casi todo son importaciones de Python. Sin coste nuevo: `min-instances` sigue en 0.

## Entrega
- Prueba que importa `main` en un subproceso limpio, comprueba las librerías cargadas y el número de módulos (R2).

## Límites
- Su prueba y, en `features/niif18/engines/export_engine.py`, solo mover `from fpdf import FPDF` (l. 11) dentro de las funciones que usan `FPDF`; ARR-02 R1 no nombraba fpdf. Si el tope no se cumple en el CI, se informa al Arquitecto: no se sube el tope desde la ficha.
- Archivo nuevo con el aviso de autor; LF.
