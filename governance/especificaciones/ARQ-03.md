# ARQ-03 · Principios con árbitro
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Un documento aparte y una prueba:

- `governance/arquitectura/PRINCIPIOS_ARBITROS.md`: una tabla con las columnas `principio`, `árbitro` y `nota`.
  - `principio` es el encabezado exacto de `governance/DOCTRINAS.md`.
  - `árbitro` es la ruta de una prueba o de un script que existe, o la marca `sin árbitro`.

Medido en `origin/main` 4eca5af2: `DOCTRINAS.md` tiene doce doctrinas, con encabezados `## 1.` a `## 12.`.

## 2. API

No aplica.

## 3. Reglas

- **R1 · `DOCTRINAS.md` no se toca (decisión del CTO, 2026-11-13).** Sus encabezados, tokens y candados son normativos. El mapa vive en otro archivo y cita cada principio por su encabezado.
- **R2 · Todo principio, en el mapa.** Cada encabezado `## n.` de `DOCTRINAS.md` tiene una fila, y cada fila corresponde a un encabezado que existe.
- **R3 · Árbitro real.**
  - Una ruta de árbitro existe en el repositorio y es una prueba o un script que el CI ejecuta.
  - La nota dice qué parte del principio comprueba.
  - Un árbitro que cubre el principio solo en parte se anota así, no como cobertura completa.
- **R4 · Sin árbitro.** Los principios marcados `sin árbitro` se listan al final del documento y se envían al CTO para que decida: cubrirlos con una ficha nueva o eliminarlos. La ficha no los elimina ni crea pruebas nuevas.
- **R-ADPA · Ortogonalidad ZERAG (`ARQ-03`).** Solo gobernanza.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** `DOCTRINAS.md`, **entonces** cada encabezado de doctrina tiene una fila en el mapa. Mutación: borrar una fila hace fallar la prueba. | `test_todo_principio_en_el_mapa` |
| **Dado** el mapa, **entonces** cada fila cita un encabezado que existe. Mutación: cambiar el texto de un encabezado en el mapa hace fallar la prueba. | `test_filas_citan_encabezados_existentes` |
| **Dado** una fila con árbitro, **entonces** la ruta existe. Mutación: apuntar a una prueba inexistente hace fallar la prueba. | `test_arbitros_existen` |

Todas en `tests/test_arq03_principios_arbitros.py`, sin base de datos y sin `import yaml`.

Criterio de revisión del PR, no prueba permanente: el PR de ARQ-03 no cambia `DOCTRINAS.md`. Ya lo garantiza `verificar_alcance_pr.py`, porque ese archivo no está en su propiedad. Una prueba permanente congelaría `DOCTRINAS.md` y bloquearía los cambios que decida el propietario. Si el archivo cambia sin que se actualice el mapa, lo detectan las dos primeras pruebas (R2).

## 6. Trazabilidad

- Ficha: `governance/tareas/ARQ-03.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Origen: propuesta TOGAF aprobada por el CTO (2026-11-13) y doctrina 11 (arbitraje exógeno).
- Propiedad: `governance/arquitectura/PRINCIPIOS_ARBITROS.md` y `tests/test_arq03_principios_arbitros.py` (crea los dos). Lee `governance/DOCTRINAS.md`; no lo edita.
- R1 cita una decisión del CTO, así que enlaza su ADR (regla R4 de ARQ-01). Orden en `depende_de`: ARQ-01 → ARQ-02 → ARQ-03.
- Va en la tanda de gobernanza con ARQ-01 y ARQ-02. Entrega al CTO la lista de los principios sin árbitro.
