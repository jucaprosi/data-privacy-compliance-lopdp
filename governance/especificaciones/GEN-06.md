# GEN-06 · Alembic sin marca: archivo y revisión 20261031_diag_escala_madurez, con su descendiente y un docstring
`¤sdd` `¤adpa` `¤arbitro`

## 1. Datos

Programa: GEN-01 §0. Estado final:

| Archivo | Estado final |
| :--- | :--- |
| `alembic/versions/20261031_diagnostico_escala_madurez.py` (renombrado con `git mv`) | `revision = "20261031_diag_escala_madurez"`; docstring «Escala de madurez de 1 a 5 en las respuestas del diagnóstico (DIAG-08)»; `upgrade` y `downgrade` sin cambios |
| `alembic/versions/20261030_dpo_inscripcion.py:8` | `down_revision = "20261031_diag_escala_madurez"` |
| `alembic/versions/20261103_biblioteca_mis_plantillas.py:4` | docstring con el término de GEN-03 R3 |
| `tests/test_diagnostico_escala_1_5.py` | `MIGRACION` apunta al archivo renombrado |

Hecho medido en `origin/main` ea6d26bf: la revisión de la escala es ancestro de `20261030_dpo_inscripcion` (la fecha del nombre no es el orden). `alembic_version` guarda solo cabezas, así que renombrar un ancestro no toca ninguna base, salvo que un entorno esté parado justo en esa revisión.

## 2. API

Sin rutas.

## 3. Reglas

- **R1 · Lectura previa del propietario.**
  - Antes de fusionar, el propietario lee `SELECT version_num FROM alembic_version` en producción, pruebas y demo, con el brief `GEN-propietario-recuentos.md`.
  - Si ningún entorno devuelve la revisión que se renombra, se fusiona.
  - Si alguno la devuelve, ese entorno se actualiza primero hasta la cabeza (`alembic upgrade head`, en su procedimiento) y se vuelve a leer.
- **R2 · Una cabeza por sala.** Después del cambio, `alembic heads` da una cabeza por sala (`governance/operaciones/FUSION_ALEMBIC.md`), y la cadena `down_revision` no tiene huecos.
- **R3 · El SQL no cambia.** Solo cambian el nombre del archivo, el identificador, el docstring y el puntero del descendiente.
- **R-ADPA · Ortogonalidad ZERAG (`GEN-06`).** Solo la propiedad.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** `alembic/`, **entonces** hay una cabeza por sala y `upgrade head` sobre una base vacía termina. Mutación m1: dejar `20261030_dpo_inscripcion.py` con el `down_revision` anterior da rojo (dos raíces o revisión inexistente). | `tests/test_alembic_cabeza_por_sala.py` |
| **Dado** la base del arnés, **entonces** las pruebas de la escala pasan con la migración renombrada. | `tests/test_diagnostico_escala_1_5.py` |
| **Dado** los tres entornos, **entonces** ninguno está en la revisión renombrada. | lectura del propietario (R1) |

## 6. Trazabilidad

- Programa GEN-01 §0. Condición §5.2 del brief del CTO.
- Depende de GEN-02 (crea la prueba renombrada) y de las fichas hechas que comparten estos archivos: DIAG-08, DPO-02 y BIB-103.
