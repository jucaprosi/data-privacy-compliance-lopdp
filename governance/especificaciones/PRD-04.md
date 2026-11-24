# PRD-04 · Las decisiones del 2026-11-24 en el PRD
`¤sdd` `¤triaje`

## 1. Datos

Sin datos persistentes. Cambia texto de `governance/artefactos/PRD.md`, de `governance/especificaciones/README.md` y de la §6 de seis especificaciones.

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
- **R4 · Sin árbitro mecánico (decisión del Arquitecto).** `verificar_especificaciones.py` no cambia:
  - un árbitro solo podría comprobar que aparece el texto `PRD`, no que el apartado citado sustente la decisión, y eso invita a citas de trámite;
  - las especificaciones técnicas (CI, arneses, migraciones) no tienen apartado del PRD, y separarlas pediría un campo o una excepción más;
  - la comprobación real es de contenido; la hace el Arquitecto con la lista de validación al revisar cada ficha nueva.
- **R-ADPA · Ortogonalidad ZERAG (`PRD-04`).** Solo los archivos de la propiedad.

## 4. Interfaz

Sin interfaz.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** las seis especificaciones, **entonces** conservan los seis apartados en orden y sus escenarios con prueba. | `scripts/verificar_especificaciones.py` |
| **Dado** el índice de tareas y el reparto, **entonces** PRD-04 entra sin choques de propiedad. | `scripts/generar_indice_tareas.py --verificar`, `scripts/verificar_reparto.py` |
| **Dado** los invariantes citados en el PRD, **entonces** siguen existiendo. | `tests/test_inv_citados_existen.py` |

## 6. Trazabilidad

- **PRD:** leyes fundacionales 6, 7 y 13; §4, Módulos 6.1, 6.3 y 7.
- Brief del CTO `ARQUITECTO_PRD_DECISIONES_2026-11-24.md` (2026-11-24), base `origin/main` 07bd95b5.
- Decisiones del propietario del 2026-11-24 recogidas en LEG-08, BIB-403, BIB-404, NORM-04, NORM-05 y NORM-06.
