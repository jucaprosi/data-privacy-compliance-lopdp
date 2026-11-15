# RET-00 · Eliminación de las pruebas que vigilaban plataformas retiradas
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Se eliminan archivos de `tests/`. Su historia queda en git.

| Se elimina | Qué era |
| :--- | :--- |
| `tests/plataforma_unica/` (catálogos, `catalogos.py` y `pendientes/`) y `tests/test_plataforma_unica.py` | el árbitro de catálogos cerrados |
| la carpeta de la guardia de huellas de la base anterior en `tests/` (permitidos y pendientes) y su prueba | la guardia de menciones |
| `tests/test_ci17_…` | la comprobación de que el CI no usaba la base anterior |
| `tests/test_vercel_despliegue.py` | la prueba del despliegue anterior |

La ficha confirma la lista al empezar, con los nombres exactos de `origin/main`.

## 2. API

No aplica.

## 3. Reglas

- **R1 · Eliminación completa.** Cada archivo de §1 se borra entero. No se deja un sustituto, una lista vacía ni una prueba que compruebe que se borró.
- **R2 · Referencias.** Se retiran las referencias a esos archivos en los workflows, en `pytest.ini`, en `tests/duraciones.json`, en las fichas y en los briefs. Si un workflow nombra uno de estos archivos, el cambio va en un brief al propietario.
- **R3 · Lo que se conserva.** La guardia de base de pruebas local, `exigir_base_de_pruebas()`, es de RET-01a y no se toca.
- **R4 · Verde.** La suite existente pasa sin estos archivos.
- **R-ADPA · Ortogonalidad ZERAG (`RET-00`).** Solo `tests/` y gobernanza. `verificadores/` y `.github/` son del propietario y van en su brief.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** `main` con la ficha fusionada, **entonces** ninguno de los archivos de §1 existe. | criterio de revisión del PR |
| **Dado** el CI, **entonces** la suite completa pasa. | la suite existente |
| **Dado** `pytest.ini`, `tests/duraciones.json` y las fichas, **entonces** ninguno nombra un archivo eliminado. | `tests/test_indice_tareas.py` y `tests/test_reparto.py`, que ya existen |

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-00.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Mapa del programa: `governance/partes/arquitecto/2026-11-14_COBERTURA_PLATAFORMA_UNICA.md`.
- Orden: RET-00 va primero. Sin estas pruebas, cada ficha de eliminación siguiente borra su código y su árbitro es la suite en verde, sin listas que mantener.
