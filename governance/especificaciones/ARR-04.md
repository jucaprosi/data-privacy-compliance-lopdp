# ARR-04 · Prueba de presupuesto de arranque del backend
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas. Objetivo del CTO: arranque en frío de 5 s o menos en Cloud Run. En local, `import main` tarda 3,9 s con `.pyc`; con ARR-02 y ARR-03 baja al menos los 820 ms de `pandas`, `openpyxl` y `fpdf`.

## 2. API

No aplica.

## 3. Reglas

- **R1 · Librerías fuera del arranque.** Un subproceso `python -X importtime -c "import main"`, con `PYTHONDONTWRITEBYTECODE` vacío y `.pyc` ya generados, termina sin `pandas`, `openpyxl` ni `fpdf` en `sys.modules`.
- **R2 · Presupuesto.** La mediana de tres importaciones de `main` en subprocesos, con `.pyc`, queda por debajo de 4,0 s en el CI. El ingeniero mide en el CI y anota la mediana en la prueba. Si la mediana medida por 1,5 queda por debajo de 4,0 s, usa ese valor, redondeado a la décima.
- **R1a · Hueco del corte.** `features/niif18/engines/export_engine.py:11` importa `fpdf` al nivel del módulo, y ARR-02 R1 solo nombraba `pandas`, `openpyxl` y `numpy`. ARR-04 mueve esa importación dentro de las funciones que usan `FPDF`, sin cambiar firmas ni archivos generados. Medido por el Tech Lead en `main` b1cfda85: con `fpdf` cargado, la mediana local es de 4,16 s.
- **R3 · Sin red.** Las variables de entorno de la prueba son las del arnés; nada se conecta a la nube al importar.
- **R-SP · Sin prohibiciones** (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`ARR-04`).** Solo los archivos de la propiedad.

## 4. Interfaz

Sin pantalla.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** `main` tras ARR-02 y ARR-03, **entonces** `pandas`, `openpyxl` y `fpdf` no están cargados y la mediana queda bajo el umbral. Mutación m1: un `import pandas` al nivel del módulo en una sala da rojo. Mutación m2: un `time.sleep` de 5 s al importar `main` da rojo. | `tests/test_arr04_arranque.py` |

## 6. Trazabilidad

- Brief del CTO del 2026-11-27 (arranque en frío), pedido por el propietario. Corte del Arquitecto: ARR-01 a ARR-04. Ajustes de Cloud Run: ninguno gratuito que aplicar (§6 de ARR-01).
