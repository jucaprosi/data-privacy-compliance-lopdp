# ARR-02 · La sala NIIF 18 importa pandas al usarlo
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas. Medido por el CTO con `python -X importtime -c "import main"`: `features.niif18.niif18_service` tarda 644 ms y `pandas` 367 ms. Importan `pandas` u `openpyxl` al nivel del módulo:
- `features/niif18/niif18_service.py`
- `features/niif18/engines/classifier_engine.py`
- `features/niif18/engines/diagnostico_engine.py`
- `features/niif18/engines/export_engine.py`
- `features/niif18/engines/financials_engine.py`
- `features/niif18/engines/mpm_engine.py`
- `features/niif18/engines/parser_engine.py`

## 2. API

No aplica.

## 3. Reglas

- **R1 · Importación tardía.** Ningún archivo de la propiedad importa `pandas`, `openpyxl` ni `numpy` al nivel del módulo. Cada función que los usa los importa dentro.
- **R2 · Mismo comportamiento.** Las pruebas de la sala siguen en verde sin cambiarlas.
- **R-SP · Sin prohibiciones** (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`ARR-02`).** Solo los archivos de la propiedad.

## 4. Interfaz

Sin pantalla.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** un subproceso limpio que importa `features.niif18.niif18_service`, **entonces** `pandas` y `openpyxl` no están en `sys.modules`; ARR-04 lo comprueba sobre `main`. Mutación m1: volver a importar `pandas` arriba en `parser_engine.py` hace rojo ARR-04. | pruebas de la sala y `tests/test_arr04_arranque.py` |

## 6. Trazabilidad

- Brief del CTO del 2026-11-27 (arranque en frío), pedido por el propietario. Corte del Arquitecto: ARR-01 a ARR-04. Ajustes de Cloud Run: ninguno gratuito que aplicar (§6 de ARR-01).
