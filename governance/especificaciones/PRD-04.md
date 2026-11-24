# PRD-04 · Las decisiones del 2026-11-24 en el PRD
`¤sdd` `¤triaje` `¤vpa` `¤cita-verificada` `¤plantillas-demo` `¤monitoreo-job` `¤transcripcion-normativa`

## 1. Datos

Sin datos persistentes. Cambia texto de `PRD.md`, `VPA_MAP.md`, `CITAS_PLANTILLAS_VERIFICADAS.md`, el brief del bucket, el README de especificaciones, seis fichas, seis especificaciones y la línea de rastros de tres archivos de NORM-04.

| Decisión | Ficha | Apartado del PRD |
| :--- | :--- | :--- |
| Plantilla publicable con cita verificada por sección o declarada informativa; la revisión jurídica es la validación normativa | BIB-403 | Módulo 7, «Publicación con cita verificada»; leyes 6 y 7 |
| Artefacto `CITAS_PLANTILLAS_VERIFICADAS.md` con la huella del PDF oficial | LEG-08 | Módulo 7, «Publicación con cita verificada»; ley 6 |
| Catálogo de plantillas ficticias en la demo | BIB-404 | Módulo 7, «Plantillas de la demo», y §5.6 |
| Monitoreo como Cloud Run Job con cuenta y usuario de base propios; el backend lee y lanza el Job | NORM-04, NORM-05 | Módulo 6.1, «Ejecución y reparto de privilegios»; ley 13 |
| Escaneados transcritos con Gemini en Vertex AI | NORM-06 | Módulo 6.3, «Transcripción de originales escaneados»; ley 7 |

## 2. API

Sin API nueva.

## 3. Reglas

- **R1 · En positivo y en su apartado.** Cada decisión dice qué hace el sistema, en el apartado del producto que trata ese tema, y nombra su ficha.
- **R2 · La §6 cita el PRD.** La §6 de cada una de las seis especificaciones abre con `- **PRD:**` y el apartado de §1. El resto de su §6 no cambia.
- **R3 · Para las especificaciones nuevas.** El README fija esa primera línea. Si la decisión no está en el PRD, la ficha la lleva al PRD; una especificación solo técnica nombra la ficha o el invariante del que sale.
- **R5 · Un rastro por decisión.** Alta en `VPA_MAP.md`, con su fila en el eje del módulo y el significado remitiendo al PRD:

  | Rastro | Eje | Fichas |
  | :--- | :--- | :--- |
  | `¤cita-verificada` | 1.3 (Biblioteca) | LEG-08, BIB-403 |
  | `¤plantillas-demo` | 1.3 (Biblioteca) | BIB-404 |
  | `¤monitoreo-job` | 1.4 (Inteligencia normativa) | NORM-04, NORM-05 |
  | `¤transcripcion-normativa` | 1.4 (Inteligencia normativa) | NORM-06 |
- **R6 · Difusión.** El rastro va en los `rastros` de cada ficha, en la línea de etiquetas y en la §6 de su especificación, en el apartado del PRD, en `CITAS_PLANTILLAS_VERIFICADAS.md`, en el brief del bucket y en la cabecera de `almacen_normativo.py`, `trabajo_monitoreo.py` y `test_norm04_almacen_y_trabajo.py`. Las fichas por fusionar (BIB-403, BIB-404, NORM-05 y NORM-06) lo ponen en la cabecera de los archivos que crean, según su §6.
- **R7 · Invariante.** «Solo el Job del monitoreo escribe el corpus normativo» se da de alta en positivo en `INVARIANTS.md` con NORM-05, cuyo árbitro conectado como `lopdp_app` (`test_norm05_privilegios_backend.py`) aún no existe en main. Darla de alta hoy dejaría una invariante sin árbitro ejecutable. Las otras tres decisiones son reglas de su módulo, con árbitro propio en su ficha, y no invariantes del sistema.
- **R4 · Sin árbitro mecánico de la §6 (decisión del Arquitecto).** `verificar_especificaciones.py` no cambia:
  - un árbitro solo podría comprobar que aparece el texto `PRD`, no que el apartado citado sustente la decisión, y eso invita a citas de trámite;
  - las especificaciones técnicas (CI, arneses, migraciones) no tienen apartado del PRD, y separarlas pediría un campo o una excepción más;
  - la comprobación real es de contenido; la hace el Arquitecto con la lista de validación al revisar cada ficha nueva;
  - los rastros ya tienen árbitro: `test_vpa_map.py` exige que todo rastro de una ficha figure en `VPA_MAP.md` y que `git grep` lo encuentre fuera de las fichas.
- **R-ADPA · Ortogonalidad ZERAG (`PRD-04`).** Solo los archivos de la propiedad.

## 4. Interfaz

Sin interfaz.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** las seis especificaciones, **entonces** conservan los seis apartados en orden y sus escenarios con prueba. | `scripts/verificar_especificaciones.py` |
| **Dado** el índice de tareas y el reparto, **entonces** PRD-04 entra sin choques de propiedad. | `scripts/generar_indice_tareas.py --verificar`, `scripts/verificar_reparto.py` |
| **Dado** los invariantes citados en el PRD, **entonces** siguen existiendo. | `tests/test_inv_citados_existen.py` |
| **Dado** los cuatro rastros nuevos, **entonces** figuran en `VPA_MAP.md` y `git grep -F` los encuentra fuera de `governance/tareas/`. | `tests/test_vpa_map.py` |
| **Dado** la cabecera de los `.py` de NORM-04, **entonces** las salas siguen aisladas y no hay generados compartidos. | `tests/test_adpa_bulkhead.py`, `tests/test_ci29_sin_generados_compartidos.py` |

## 6. Trazabilidad

- **PRD:** leyes fundacionales 6, 7 y 13; §4, Módulos 6.1, 6.3 y 7.
- Brief del CTO `ARQUITECTO_PRD_DECISIONES_2026-11-24.v2.md` (2026-11-24), que sustituye al primero; base `origin/main` 07bd95b5.
- Decisiones del propietario del 2026-11-24 recogidas en LEG-08, BIB-403, BIB-404, NORM-04, NORM-05 y NORM-06.
