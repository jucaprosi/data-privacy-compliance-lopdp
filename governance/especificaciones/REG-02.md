# REG-02 · Centro de conocimiento: normativa de Ecuador, resúmenes y ayuda contextual que cita la base legal
`¤sdd` `¤regulation-code` `¤frontend-ide`

## 1. Datos

Sin tablas nuevas: lee el corpus de `regulacion_rag` (fuente, artículo, texto, versión).

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `GET /conocimiento/normativa?fuente=&q=` | cualquier usuario autenticado | — | `200 {"articulos": [{fuente, articulo, titulo, texto, version}]}` |
| `GET /conocimiento/ayuda?control_ref=\|articulo=` | cualquier usuario autenticado | — | `200 {"texto": str, "cita": {fuente, articulo, version}} \| 404 {"code": "SIN_FUENTE"}` |

## 3. Reglas

- **R1 · Cita obligatoria.** Toda respuesta de ayuda lleva `cita` completa o es 404 `SIN_FUENTE`; no existe un tercer caso (`INV_LOPDP_AI_RAG_STRICT_CITATION`).
- **R2 · Corpus único.** Solo lee el corpus versionado; sin generación de texto.

## 4. Interfaz

Menú Conocimiento con tres submenús; `AyudaContextual` como icono «?» en formularios con `control_ref`, que abre un panel con el texto y la cita.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** `control_ref = P12` con artículo en el corpus, **entonces** la ayuda trae texto y cita; **dado** uno sin fuente, 404 `SIN_FUENTE`. Mutación: devolver texto sin cita hace fallar la prueba. | `test_ayuda_con_cita_o_sin_fuente` |
| **Dado** `q = derechos`, **entonces** la búsqueda devuelve artículos con fuente y versión. | `test_normativa_busqueda` |
| **Dado** un formulario con «?», **cuando** se abre, **entonces** se ve la cita «Art. … LOPDP». | `frontend/tests/conocimiento/ayuda.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/REG-02.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD apartado 6; Doctrina 7; `INV_LOPDP_AI_RAG_STRICT_CITATION`.
