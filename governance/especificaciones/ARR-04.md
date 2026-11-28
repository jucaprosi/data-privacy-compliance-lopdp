# ARR-04 · Prueba de presupuesto de arranque del backend
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas. Objetivo del CTO: arranque en frío de 5 s o menos en Cloud Run. En local, `import main` tarda 3,9 s con `.pyc`; con ARR-02 y ARR-03 baja al menos los 820 ms de `pandas`, `openpyxl` y `fpdf`.

## 2. API

No aplica.

## 3. Reglas

- **R1 · Librerías fuera del arranque.** Un subproceso `python -X importtime -c "import main"`, con `PYTHONDONTWRITEBYTECODE` vacío y `.pyc` ya generados, termina sin `pandas`, `openpyxl` ni `fpdf` en `sys.modules`.
- **R2 · Presupuesto de CPU.** Se mide el tiempo de CPU del subproceso (usuario más sistema), no el de reloj. Con la suite en paralelo (`pytest -n auto`, `.github/workflows/zero-regression-pipeline.yml:230` y `:245`), el reloj se infla por la carga de los otros workers sin que el arranque cambie: en el run 46093368213 dio 4,17 s frente a los 3,0 s medidos en el PR de ARR-04. Para cada una de tres importaciones de `main` con `.pyc`, se toma `resource.getrusage(resource.RUSAGE_CHILDREN)` antes y después del subproceso (o `os.wait4`), y se resta `ru_utime + ru_stime`. La mediana queda por debajo del umbral. El umbral sale de la mediana de CPU medida en el CI multiplicada por 1,5, redondeada a la décima y con un máximo de 4,0 s, y se anota en la prueba con la fecha y el run. Fuera de Linux, donde no hay `resource`, la R2 se salta con el motivo y la R1 sigue.
- **R1a · Hueco del corte.** `features/niif18/engines/export_engine.py:11` importa `fpdf` al nivel del módulo, y ARR-02 R1 solo nombraba `pandas`, `openpyxl` y `numpy`. ARR-04 mueve esa importación dentro de las funciones que usan `FPDF`, sin cambiar firmas ni archivos generados. Medido por el Tech Lead en `main` b1cfda85: con `fpdf` cargado, la mediana local es de 4,16 s.
- **R3 · Sin red.** Las variables de entorno de la prueba son las del arnés; nada se conecta a la nube al importar.
- **R-SP · Sin prohibiciones** (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`ARR-04`).** Solo los archivos de la propiedad.

## 4. Interfaz

Sin pantalla.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** `main` tras ARR-02 y ARR-03, **entonces** `pandas`, `openpyxl` y `fpdf` no están cargados y la mediana queda bajo el umbral. Mutación m1: un `import pandas` al nivel del módulo en una sala da rojo. Mutación m2: un bucle que consume 5 s de CPU al importar `main` da rojo. Un `time.sleep` no cuenta, porque no consume CPU. | `tests/test_arr04_arranque.py` |

## 6. Trazabilidad

- Brief del CTO del 2026-11-27 (arranque en frío), pedido por el propietario. Corte del Arquitecto: ARR-01 a ARR-04. Ajustes de Cloud Run: ninguno gratuito que aplicar (§6 de ARR-01).
