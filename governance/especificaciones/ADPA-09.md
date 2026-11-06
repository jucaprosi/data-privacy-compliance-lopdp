# ADPA-09 · Andamiaje de `features/formacion` y `features/conservacion` (Catálogo PRD §7.1)
`¤sdd` `¤adpa` `¤formacion` `¤conservacion`

## 1. Datos

Sin tablas nuevas (las tablas se crean en `FOR-01` y `CON-01`).

## 2. API

Sin rutas nuevas.

## 3. Reglas

- **R1 · Completitud de las 22 salas del PRD §7.1.** Cada sala declarada en `PRD.md` §7.1 existe como paquete en `features/<sala>/` y posee su compuerta canónica.
- **R2 · Secciones `#FOR-01` y `#CON-01` listas.** `formacion_service.py`, `conservacion_service.py`, sus `domain/errores.py` y sus pasillos en `app_core/pasillo/` incluyen las secciones `#FOR-01` y `#CON-01`.

## 4. Interfaz

Sin interfaz propia.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el catálogo de 22 salas en `PRD.md` §7.1, **cuando** corre `test_adpa09_salas_prd.py`, **entonces** las 22 carpetas `features/<sala>/` y sus compuertas existen en el repositorio. | `test_todas_las_salas_del_prd_existen_con_compuerta` |

## 6. Trazabilidad

- PRD §7.1 (Catálogo canónico de salas).
