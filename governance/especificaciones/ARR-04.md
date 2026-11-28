# ARR-04 · Prueba de presupuesto de arranque del backend
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas. Objetivo del CTO: arranque en frío de 5 s o menos en Cloud Run. En local, `import main` tarda 3,9 s con `.pyc`; con ARR-02 y ARR-03 baja al menos los 820 ms de `pandas`, `openpyxl` y `fpdf`.

## 2. API

No aplica.

## 3. Reglas

- **R1 · Librerías fuera del arranque.** Un subproceso `python -X importtime -c "import main"`, con `PYTHONDONTWRITEBYTECODE` vacío y `.pyc` ya generados, termina sin `pandas`, `openpyxl` ni `fpdf` en `sys.modules`.
- **R2 · Presupuesto de módulos.** En el mismo subproceso de R1, tras `import main`, `len(sys.modules)` queda por debajo de un tope. El tope es la cifra medida en el CI más un 10 %, redondeada hacia arriba, y se anota en la prueba con la fecha y el run. Es una medida determinista: vigila lo que de verdad hace crecer el arranque y no depende del runner. El tiempo no se mide en el CI: con el mismo código, la mediana de CPU dio 4,199 s en el run 46094645681 y 2,435 s en el 46095228291 (runner compartido de 4 CPU con `-n auto`), y el reloj, 4,17 s en el 46093368213. El objetivo de 5 s se comprueba en el arranque en frío de Cloud Run tras el despliegue del propietario, de «Starting new instance» a «Application startup complete», y se anota en el parte.
- **R1a · Hueco del corte.** `features/niif18/engines/export_engine.py:11` importa `fpdf` al nivel del módulo, y ARR-02 R1 solo nombraba `pandas`, `openpyxl` y `numpy`. ARR-04 mueve esa importación dentro de las funciones que usan `FPDF`, sin cambiar firmas ni archivos generados. Medido por el Tech Lead en `main` b1cfda85: con `fpdf` cargado, la mediana local es de 4,16 s.
- **R3 · Sin red.** Las variables de entorno de la prueba son las del arnés; nada se conecta a la nube al importar.
- **R-SP · Sin prohibiciones** (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`ARR-04`).** Solo los archivos de la propiedad.

## 4. Interfaz

Sin pantalla.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** `main` tras ARR-02 y ARR-03, **entonces** `pandas`, `openpyxl` y `fpdf` no están cargados y `sys.modules` queda bajo el tope. Mutación m1: un `import pandas` al nivel del módulo en una sala da rojo. Mutación m2: importar una librería pesada nueva (por ejemplo `pandas`) al nivel del módulo en una sala hace crecer `sys.modules` por encima del tope y da rojo. | `tests/test_arr04_arranque.py` |

## 6. Trazabilidad

- Brief del CTO del 2026-11-27 (arranque en frío), pedido por el propietario. Corte del Arquitecto: ARR-01 a ARR-04. Ajustes de Cloud Run: ninguno gratuito que aplicar (§6 de ARR-01).
