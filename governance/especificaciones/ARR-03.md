# ARR-03 · Las exportaciones de RAT y de la biblioteca importan sus librerías al usarlas
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas. Medido por el CTO: `features.rat.services.exportacion_engine` tarda 290 ms, `openpyxl` 232 ms y `fpdf` 221 ms. Importan `pandas`, `openpyxl` o `fpdf` al nivel del módulo:
- `features/rat/services/exportacion_engine.py`
- `features/biblioteca/services/generador_xlsx.py`

## 2. API

No aplica.

## 3. Reglas

- **R1 · Importación tardía.** Ningún archivo de la propiedad importa `pandas`, `openpyxl` ni `fpdf` al nivel del módulo.
- **R2 · Mismo comportamiento.** Las pruebas de exportación siguen en verde sin cambiarlas.
- **R-SP · Sin prohibiciones** (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`ARR-03`).** Solo los archivos de la propiedad.

## 4. Interfaz

Sin pantalla.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** un subproceso limpio que importa `main`, **entonces** `openpyxl` y `fpdf` no están en `sys.modules`. Mutación m1: volver a importar `openpyxl` arriba en `generador_xlsx.py` hace rojo ARR-04. | pruebas de las salas y `tests/test_arr04_arranque.py` |

## 6. Trazabilidad

- Brief del CTO del 2026-11-27 (arranque en frío), pedido por el propietario. Corte del Arquitecto: ARR-01 a ARR-04. Ajustes de Cloud Run: ninguno gratuito que aplicar (§6 de ARR-01).
