# PRD-05 · Los documentos rectores con un solo modelo de generación
`¤sdd` `¤gemini-vertex`

## 1. Datos

Sin datos persistentes. Cambia el texto de los documentos rectores que nombraban modelos retirados:

| Archivo | Apartado |
| :--- | :--- |
| `governance/artefactos/PRD.md` | ley 7; Módulo 3 (EIPD); Módulo 5 (título y generación); Módulo 6 (análisis de impacto); 6.5 (modelos desplegados); NIIF 18; tabla de salas (`roadmap`, `ai_copilot`); diagrama de la Capa 4; resumen de módulos (6); árbitro 14; glosario (Context Caching) |
| `governance/artefactos/INVARIANTS.md` | invariante 20 `INV_LOPDP_GEMINI_VERTEX_NATIVE_MODELS` |
| `governance/artefactos/VPA_MAP.md` | filas `¤roadmap` y `¤gemini-vertex` |
| `governance/artefactos/TASKS.md` | resumen; filas de VTX-01 y NORM-03 |
| `governance/especificaciones/IA-06.md`, `VTX-01.md`, `NORM-03.md` | el modelo que usan |
| `governance/apoyo/LANZAMIENTO_TANDA_ORTOGONAL.md` | resumen de IA-06 |
| `governance/operaciones/BRIEF_PROPIETARIO_IA-11.md` | `$modelo` y la lista de modelos |

## 2. API

Sin API nueva.

## 3. Reglas

- **R1 · Una sola fuente.** El PRD (ley 7, 6.5 y árbitro 14), la invariante 20, la fila `¤gemini-vertex` y las especificaciones remiten a `features/inferencia/domain/modelos_permitidos.py` (IA-13 R1). Nombran `gemini-3.8-flash` solo como valor de hoy («hoy `gemini-3.8-flash`»); el próximo cambio de modelo se hace en ese archivo.
- **R2 · Un solo modelo de generación.** Toda la generación (Hoja de Ruta, EIPD, dictámenes, impacto normativo, NIIF 18, RAT, Assessment, Biblioteca, ARCOP+ y multimodal) usa `MODELO_GENERACION`, y los vectores usan `text-embedding-005`. El 6.5 del PRD y el diagrama de la Capa 4 dejan un solo nodo de generación.
- **R3 · En positivo.** Lo retirado se borra como si nunca hubiera estado, sin reglas que lo prohíban.
- **R4 · Historia intacta.** No cambian IA-13, IA-14, `APORTES_INEDITOS.md`, `alembic/`, las fichas de tareas hechas, `EVIDENCIA_HUMO_VERTEX.md` ni `BRIEF_PROPIETARIO_VERTEX.md`: registran mediciones y decisiones con su fecha.
- **R5 · Sin modelos nuevos.** Solo se nombran los modelos de `modelos_permitidos.py`; `gemini-3.5-flash-lite` no está ahí y no se añade.
- **R-ADPA · Ortogonalidad ZERAG (`PRD-05`).** Solo los archivos de la propiedad.

## 4. Interfaz

Sin interfaz.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** las especificaciones tocadas, **entonces** conservan los seis apartados y sus escenarios con prueba. | `scripts/verificar_especificaciones.py`, `tests/test_verificar_especificaciones.py` |
| **Dado** el índice y el reparto, **entonces** PRD-05 entra sin choques de propiedad. | `tests/test_indice_tareas.py`, `tests/test_reparto.py` |
| **Dado** los invariantes citados en el PRD, **entonces** siguen existiendo. | `tests/test_inv_citados_existen.py` |
| **Dado** las filas de VPA_MAP, **entonces** los rastros de las fichas figuran y se encuentran fuera de ellas. | `tests/test_vpa_map.py` |
| **Dado** el árbol, **entonces** no hay generados compartidos. | `tests/test_ci29_sin_generados_compartidos.py` |

## 6. Trazabilidad

- **PRD:** ley fundacional 7; §4, Módulo 6.5 «Arquitectura Cognitiva Nativa sobre Google Gemini en Vertex AI»; árbitro 14.
- Brief del CTO `ARQUITECTO_MODELOS_GEMINI_DOCUMENTOS.md` (2026-11-24), base `origin/main` c5f8c69a.
- IA-13 R1 y §1. La medición del propietario del 2026-11-24, recogida en el brief, coincide con ella: confirma `gemini-3.8-flash` (200) y descarta `gemini-2.0-flash` y `gemini-1.5-flash` (404).
