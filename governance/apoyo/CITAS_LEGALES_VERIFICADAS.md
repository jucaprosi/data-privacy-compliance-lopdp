# Citas legales verificadas (LEG-03)

`¤regulation-code` `¤seguridad`

> **Estado:** borrador para aprobación del propietario. El árbitro (`scripts/verificar_citas_legales.py`) comprueba la estructura; el contenido jurídico lo aprueba el propietario.
> **Ficha:** `LEG-03`, sala `gobernanza`. No edita código, el PRD ni `INVARIANTS.md`: sus propuestas las aplican el coordinador y las salas dueñas en sus propias tareas.

## Aviso sobre las fuentes (léase primero)

- **LOPDP.** El PDF de la SPDP (`spdp.gob.ec`, versión 2021 comprimida) no se pudo abrir: supera el límite de descarga de la herramienta. Se leyó el **texto íntegro** publicado en el portal de la Superintendencia de Economía Popular y Solidaria (`finanzaspopulares.gob.ec`). Es una compilación de Lexis (pie «FINDER LOYAL»), con la cabecera «Registro Oficial Suplemento 459 de 26-may.-2021 · Estado: Vigente». No es un resumen: tiene 77 artículos y el oficio de remisión. Aun así, conviene cotejarla una vez con el PDF del Registro Oficial antes de activar los parámetros.
- **Reglamento General (Decreto Ejecutivo 904).** Del PDF de la SPDP solo se pudo leer la portada: **Registro Oficial, Tercer Suplemento N.º 435, lunes 13 de noviembre de 2023, págs. 4 a 41**. Las páginas interiores están escaneadas y no tienen capa de texto, así que **ningún artículo del Reglamento General se cita como verificado** en este documento.
- **Reglamento del Delegado (Res. SPDP-SPD-2025-0028-R).** Lo verificó LEG-01. Aquí solo se consolida y no se volvió a leer.
- **Norma técnica de vulneraciones (Res. SPDP-SPD-2026-0040-R).** Se toma de LEG-02 (`governance/apoyo/NORMA_TECNICA_VULNERACIONES.md`), que la leyó en el Registro Oficial, Primer Suplemento N.º 376.
- **Guía de riesgos y EIPD (Res. SPDP-SPD-2025-0003-R) y metodología de multas (Res. SPDP-SPD-2025-0022-R).** No se leyeron en esta ficha. No se citan sus artículos.

## Identificación de las fuentes

| Fuente | Identificación oficial | URL | Leída en LEG-03 |
|---|---|---|---|
| LOPDP | Ley Orgánica de Protección de Datos Personales, Registro Oficial Suplemento 459, 26-may-2021 | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | Sí, texto íntegro (77 artículos) |
| Reglamento General | Decreto Ejecutivo 904, Registro Oficial Tercer Suplemento 435, 13-nov-2023 | https://www.spdp.gob.ec/wp-content/uploads/2026/09/03-Reglamento-General-de-la-Ley-Organica-de-Proteccion-de-Datos-Personales-2023.pdf | Solo la portada |
| Reglamento del Delegado | Resolución SPDP-SPD-2025-0028-R | https://www.spdp.gob.ec/wp-content/uploads/2025/12/028-R_compressed.pdf | No (verificado en LEG-01) |
| Norma técnica de vulneraciones | Resolución SPDP-SPD-2026-0040-R, Registro Oficial Primer Suplemento 376, 24-sep-2026 | https://www.spdp.gob.ec/wp-content/uploads/2026/10/SPDP-SPD-2026-0040-r.pdf | No (verificada en LEG-02) |
| Guía de riesgos y EIPD | Resolución SPDP-SPD-2025-0003-R | https://www.spdp.gob.ec/wp-content/uploads/2025/12/03.01.01-SPDP-SPD-2025-0003-R-Guia-Gest-de-Riesg-y-Ev-Imp-signed_compressed.pdf | No |

## Hallazgos que cambian el PRD

1. **Unidad de los plazos.** La LOPDP no usa la misma palabra para todos los plazos:
   - **«término»** para las vulneraciones: 5 días a la Autoridad y 2 días del encargado al responsable (art. 43), y 3 días al titular (art. 46);
   - **«término»** también para contestar el requerimiento directo del titular: 10 días (art. 62);
   - **«plazo de quince (15) días»** para atender los derechos de acceso, rectificación y actualización, eliminación y oposición (arts. 13 a 16).

   En la legislación ecuatoriana, «término» suele contarse en días hábiles y «plazo» en días calendario (Código Orgánico Administrativo). Ese código **no se leyó en esta ficha**, así que la unidad queda `no verificado`. Lo que sí se verifica es la palabra literal que usa la ley.
2. **Dos plazos para las solicitudes de derechos.** Los arts. 13 a 16 dan 15 días (plazo) y el art. 62 da 10 días (término) para «contestar afirmativa o negativamente, notificar y ejecutar». El parámetro «15 días» del PRD no recoge el art. 62. Lo decide el propietario con el abogado. **Resuelto el 2026-11-09:** véase «Criterio del abogado sobre los plazos por tipo de solicitud», más abajo.
3. **No hay «72 horas» en la LOPDP.** La interfaz y `report_generator.py` muestran «SLA 72h». La ley fija términos de días (arts. 43 y 46).
4. **No hay «registro de actividades de tratamiento» en la LOPDP.** La ley obliga a mantener el **Registro Nacional de Protección de Datos Personales** ante la Autoridad (art. 47 num. 12) y enumera su contenido (art. 51). Las interfaces citan el art. 35 o el art. 41 para el RAT, pero esos artículos tratan otra cosa: el acceso de terceros (35) y la determinación de medidas de seguridad (41). Las reglas del RAT estarían en el Reglamento General (arts. 38 y 39 según el código), que no se pudo leer.
5. **La «consulta previa» a la SPDP no aparece en la LOPDP.** El art. 42 obliga a la EIPD y dice que debe hacerse antes del tratamiento, pero no regula una consulta previa. Las citas «Art. 44 (consulta previa)» son incorrectas: el art. 44 trata el acceso para emergencias e incidentes informáticos.

## Tabla de verificación

| Dato | Dónde en el PRD | Artículo literal | Fuente | URL | Valor confirmado | Estado |
|---|---|---|---|---|---|---|
| Derecho a la información | §5 Derechos de los titulares (línea 186) | LOPDP art. 12, «Derecho a la información» | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | Derecho a ser informado; plazo de 30 días si los datos no se obtuvieron del titular | verificado |
| Derecho de acceso | §5 Derechos (186) | LOPDP art. 13, «Derecho de acceso»: «deberá ser atendido dentro del plazo de quince (15) días» | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | 15 días, «plazo» | verificado |
| Derecho de rectificación y actualización | §5 Derechos (186) | LOPDP art. 14 | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | 15 días, «plazo» | verificado |
| Derecho de eliminación | §5 Derechos (186) | LOPDP art. 15: «en el plazo de quince (15) días de recibida la solicitud» | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | 15 días desde que se recibe la solicitud | verificado |
| Derecho de oposición | §5 Derechos (186) | LOPDP art. 16: «deberá ser atendida dentro del plazo de quince (15) días» | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | 15 días, «plazo» | verificado |
| Derecho a la portabilidad | §5 Derechos (186) | LOPDP art. 17, «Derecho a la portabilidad» | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | Existe el derecho | verificado |
| Excepciones a los derechos | §5 Derechos (186) | LOPDP art. 18 | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | Existen excepciones | verificado |
| Suspensión del tratamiento | §5 Derechos (186) | LOPDP art. 19, «Derecho a la suspensión del tratamiento» | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | Existe el derecho | verificado |
| No ser objeto de decisiones automatizadas | §5 Derechos (186) | LOPDP art. 20; art. 21 para niñas, niños y adolescentes | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | Existe el derecho | verificado |
| Consulta, educación digital y ejercicio de derechos | §5 Derechos (186) | LOPDP arts. 22, 23 y 24 | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | No son derechos ante el responsable: la consulta es ante el Registro Nacional; la educación digital y el ejercicio de derechos son deberes del Estado | verificado |
| Plazo para contestar al titular | §5 Derechos (186), «15 días (*)» | LOPDP art. 62: «contará con un término de diez (10) días para contestar» | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | 10 días, «término»; contradice el parámetro único de 15 días | verificado |
| Unidad de «plazo» y «término» | §5 Derechos (186), «unidad por confirmar» | LOPDP arts. 13 a 16 («plazo»), 43, 46 y 62 («término»); la equivalencia en días está en el Código Orgánico Administrativo (no leído) | LOPDP (palabras literales) | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | Unidad en días sin confirmar | no verificado |
| Registro ante la Autoridad | §5 Panel del DPO (205), «datos para el registro (*)» | LOPDP art. 47 num. 12 y art. 51, «Registro Nacional de protección de datos personales» | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | 9 elementos que se reportan (art. 51, nums. 1 a 9) | verificado |
| Registro de actividades de tratamiento | §5 RAT (184) | Reglamento General, arts. 38 y 39 según el código (no leídos) | Reglamento General | https://www.spdp.gob.ec/wp-content/uploads/2026/09/03-Reglamento-General-de-la-Ley-Organica-de-Proteccion-de-Datos-Personales-2023.pdf | Sin confirmar | no verificado |
| Medidas de seguridad | §5 Matriz de riesgos (197) | LOPDP art. 37, «Seguridad de datos personales»; arts. 38 a 41 | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | El art. 38 se refiere solo al sector público | verificado |
| Evaluación de impacto | §5 Matriz de riesgos y EIPD (197) | LOPDP art. 42: «será de carácter obligatoria en caso de» a), b) y c); «deberá efectuarse previo al inicio del tratamiento» | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | 3 supuestos obligatorios; la Autoridad puede añadir otros | verificado |
| Consulta previa a la SPDP | §5 Matriz de riesgos y EIPD (197), «(*)» | No aparece en la LOPDP leída | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | Sin base en la LOPDP | no verificado |
| Metodología de riesgos de la SPDP | §5 Matriz de riesgos (197), «(*)» | Res. SPDP-SPD-2025-0003-R (no leída) | Guía de riesgos y EIPD | https://www.spdp.gob.ec/wp-content/uploads/2025/12/03.01.01-SPDP-SPD-2025-0003-R-Guia-Gest-de-Riesg-y-Ev-Imp-signed_compressed.pdf | Sin confirmar | no verificado |
| Plazo del encargado al responsable | §5 Vulneraciones (187), «2 días (*)» | LOPDP art. 43: «a más tardar dentro del término de dos (2) días contados a partir de la fecha en la que tenga conocimiento de ella» | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | 2 días, «término», desde que lo conoce | verificado |
| Plazo del responsable a la SPDP | §5 Vulneraciones (187), «5 días (*)» | LOPDP art. 43: «a más tardar en el término de cinco (5) días después de que haya tenido constancia de ella» | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | 5 días, «término», desde que tiene constancia; se notifica también a la Agencia de Regulación y Control de las Telecomunicaciones; si se pasa el término, deben indicarse los motivos | verificado |
| Plazo del responsable al titular | §5 Vulneraciones (187), «3 días (*)» | LOPDP art. 46: «dentro del término de tres días contados a partir de la fecha en la que tuvo conocimiento del riesgo» | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | 3 días, «término», desde que conoce el riesgo, cuando hay riesgo para los derechos | verificado |
| Canal de notificación a la Autoridad | §5 Vulneraciones (187) | Res. SPDP-SPD-2026-0040-R art. 3.3 (SISPDP, https://servicios.spdp.gob.ec), según LEG-02 | Norma técnica de vulneraciones | https://www.spdp.gob.ec/wp-content/uploads/2026/10/SPDP-SPD-2026-0040-r.pdf | SISPDP | verificado |
| Delegado: cuándo se designa | §5 Panel del DPO (205) | LOPDP art. 48, «Delegado de protección de datos personales», nums. 1 a 4 | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | 4 supuestos | verificado |
| Delegado: funciones y garantías | §5 Panel del DPO (205) | LOPDP arts. 49 y 50 | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | Funciones (art. 49); no se le puede destituir ni sancionar por el correcto desempeño de sus funciones y se relaciona directamente con el más alto nivel (art. 50) | verificado |
| Delegado: reglamento | §5 Panel del DPO (205) | Res. SPDP-SPD-2025-0028-R (verificada en LEG-01) | Reglamento del Delegado | https://www.spdp.gob.ec/wp-content/uploads/2025/12/028-R_compressed.pdf | Se consolida de LEG-01 sin releer | no verificado |
| Transferencias internacionales | §5 Ubicación de los datos (452) | LOPDP arts. 55 a 61: art. 56, países con nivel adecuado; art. 57, garantías adecuadas; art. 58, normas corporativas vinculantes; art. 59, autorización; art. 60, casos excepcionales; art. 61, control continuo | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | El «Art. 60» de la interfaz solo cubre los casos excepcionales | verificado |
| Bases de legitimación | §6 Paquete normativo (425) | LOPDP art. 7, nums. 1 a 8 | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | 8 bases: consentimiento, obligación legal, orden judicial, interés público, contrato, intereses vitales, bases de acceso público e interés legítimo | verificado |
| Categorías especiales y datos sensibles | §6 Paquete normativo (425) | LOPDP art. 25 (a a d); art. 4, definición de datos sensibles; art. 26 | LOPDP | https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf | Categorías especiales: datos sensibles, de niñas, niños y adolescentes, de salud y de personas con discapacidad. Datos sensibles: etnia, identidad de género, identidad cultural, religión, ideología, filiación política, pasado judicial, condición migratoria, orientación sexual, salud, datos biométricos y genéticos | verificado |

## Valor propuesto por parámetro del paquete normativo

Solo se propone un valor si tiene cita verificada. Lo que no la tiene queda «sin proponer».

| Parámetro | Valor propuesto | Cita |
|---|---|---|
| `plazo.vulneracion.encargado_a_responsable` | 2 días, «término», desde que el encargado conoce la vulneración | LOPDP, art. 43 |
| `plazo.vulneracion.responsable_a_autoridad` | 5 días, «término», desde que el responsable tiene constancia de ella | LOPDP, art. 43 |
| `plazo.vulneracion.responsable_a_titular` | 3 días, «término», desde que conoce el riesgo | LOPDP, art. 46 |
| `plazo.derechos.atencion` | 15 días, «plazo», desde que se recibe la solicitud | LOPDP, arts. 13 a 16 |
| `plazo.derechos.contestacion` | 10 días, «término», desde que se presenta el requerimiento (decisión pendiente frente al de 15) | LOPDP, art. 62 |
| `plazo.unidad` | Sin proponer: depende del Código Orgánico Administrativo (no leído) | no verificado |
| `autoridad` | Autoridad de Protección de Datos Personales; en las vulneraciones, también la Agencia de Regulación y Control de las Telecomunicaciones | LOPDP, arts. 43 y 75 |
| `canal.notificacion` | SISPDP, https://servicios.spdp.gob.ec | Res. SPDP-SPD-2026-0040-R, art. 3.3 (LEG-02) |
| `derechos.tipos` | información, acceso, rectificación y actualización, eliminación, oposición, portabilidad, suspensión del tratamiento, no ser objeto de decisiones automatizadas | LOPDP, arts. 12 a 17, 19 y 20 |
| `bases_legitimacion` | las 8 del art. 7 | LOPDP, art. 7 |
| `categorias_sensibles` | la lista del art. 4; categorías especiales del art. 25 | LOPDP, arts. 4 y 25 |

## Inventario de citas de la interfaz

Lo genera `python scripts/verificar_citas_legales.py --pares` con los `git grep` de la ficha sobre `frontend/src` y `features`. Hay una fila por par (archivo, cita). «Cita correcta» sigue la tabla anterior. `verificado` quiere decir que la cita correcta se localizó en el texto leído. `no verificado` quiere decir que la norma citada no se leyó en esta ficha, o que no se pudo fijar la cita correcta. Es una lista para las salas dueñas (frontend, regulación, organización, riesgos): esta ficha no edita código.

| Archivo | Cita | Norma que cita | Cita correcta | Estado |
|---|---|---|---|---|
| `features/biblioteca/domain/reglas.py` | Art. 38 | Reglamento General | Reglamento General, art. 38 (texto no leído en LEG-03) | no verificado |
| `features/biblioteca/domain/reglas.py` | Art. 42 | LOPDP | LOPDP, art. 42 (Evaluación de impacto del tratamiento de datos personales) | verificado |
| `features/biblioteca/domain/reglas.py` | Art. 47 | LOPDP | LOPDP, art. 47 (Obligaciones del responsable y encargado del tratamiento de datos personales) | verificado |
| `features/biblioteca/domain/reglas.py` | Art. 48 | LOPDP | LOPDP, art. 47 num. 11 (encargado); el art. 48 es el delegado | verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 10 | LOPDP | LOPDP, art. 10 (Principios) | verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 17 | LOPDP | LOPDP, art. 17 (texto no leído en LEG-03) | no verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 18 | LOPDP | LOPDP, art. 18 (Excepciones a los derechos de rectificación, actualización, eliminación, oposición, anulación y portabilidad) | verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 21 | LOPDP | LOPDP, art. 21 trata decisiones automatizadas sobre niñas, niños y adolescentes, no la representación legal; la cita correcta no se pudo fijar | no verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 22 | LOPDP | LOPDP, art. 62 (requerimiento directo del titular al responsable) | verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 25 | LOPDP | LOPDP, art. 25 (Categorías especiales de datos personales) | verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 26 | LOPDP | LOPDP, art. 26 (Tratamiento de datos sensibles) | verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 30 | LOPDP | LOPDP, art. 62 (requerimiento directo del titular); el art. 30 trata datos de salud | verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 31 | LOPDP | LOPDP, arts. 13 a 16 (plazo de quince días) y art. 62 (término de diez días para contestar) | verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 35 | LOPDP | LOPDP, art. 47 num. 12 y art. 51 (Registro Nacional); la LOPDP no regula un «registro de actividades de tratamiento» | verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 38 | LOPDP | LOPDP, art. 37 (seguridad) y art. 39 (diseño y por defecto); el art. 38 es solo para el sector público | verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 39 | LOPDP | LOPDP, art. 39 (Protección de datos personales desde el diseño y por defecto) | verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 40 | LOPDP | LOPDP, art. 43 (término de 5 días a la Autoridad; 2 días del encargado) y art. 46 (término de 3 días al titular) | verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 41 | LOPDP | LOPDP, art. 43 (término de 5 días a la Autoridad; 2 días del encargado) y art. 46 (término de 3 días al titular) | verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 42 | LOPDP | LOPDP, art. 42 (Evaluación de impacto del tratamiento de datos personales) | verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 43 | LOPDP | LOPDP, art. 42 (evaluación de impacto); el art. 43 es la notificación de vulneraciones | verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 44 | LOPDP | Consulta previa: no aparece en el texto leído de la LOPDP; el art. 44 trata emergencias e incidentes informáticos | no verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 46 | LOPDP | LOPDP, art. 47 num. 10 y 11 (contratos y garantías con el encargado) | verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 47 | LOPDP | LOPDP, art. 47 (Obligaciones del responsable y encargado del tratamiento de datos personales) | verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 48 | Res. SPDP-SPD-2026-0005-R | Res. SPDP-SPD-2026-0005-R, art. 48 (texto no leído en LEG-03) | no verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 56 | LOPDP | LOPDP, art. 56 (Transferencia o comunicación internacional de datos personales a países declarados como nivel adecuado de protección) | verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 57 | LOPDP | LOPDP, art. 57 (Transferencia o comunicación mediante garantías adecuadas) | verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 7 | LOPDP | LOPDP, art. 7 (Tratamiento legítimo de datos personas) | verificado |
| `features/diagnostico/domain/banco_preguntas.json` | Art. 8 | LOPDP | LOPDP, art. 8 (Consentimiento) | verificado |
| `features/diagnostico/services/report_generator.py` | Art. 42 | LOPDP | LOPDP, art. 43 (término de 5 días a la Autoridad; 2 días del encargado) y art. 46 (término de 3 días al titular); no hay plazo de 72 horas | verificado |
| `features/diagnostico/services/report_generator.py` | Art. 50 | LOPDP | LOPDP, art. 47 num. 10 y 11 (contratos y garantías con el encargado) | verificado |
| `features/dpo_cockpit/domain/models.py` | Art. 50 | LOPDP | LOPDP, art. 50 (Consideraciones especiales para el delegado de protección de datos personales) | verificado |
| `features/dpo_cockpit/services/bitacora_service.py` | Art. 50 | LOPDP | LOPDP, art. 50 (Consideraciones especiales para el delegado de protección de datos personales) | verificado |
| `features/organizacion/domain/roles.py` | Art. 15 | Reglamento del Delegado | Reglamento del Delegado, art. 15 (consolidado de LEG-01; texto no releído en LEG-03) | no verificado |
| `features/organizacion/domain/roles.py` | Art. 18 | Reglamento del Delegado | Reglamento del Delegado, art. 18 (consolidado de LEG-01; texto no releído en LEG-03) | no verificado |
| `features/organizacion/services/designacion_engine.py` | Art. 15 | Reglamento del Delegado | Reglamento del Delegado, art. 15 (consolidado de LEG-01; texto no releído en LEG-03) | no verificado |
| `features/organizacion/services/designacion_engine.py` | Art. 17 | Reglamento del Delegado | Reglamento del Delegado, art. 17 (consolidado de LEG-01; texto no releído en LEG-03) | no verificado |
| `features/organizacion/services/designacion_engine.py` | Art. 3 | Reglamento del Delegado | Reglamento del Delegado, art. 3 (consolidado de LEG-01; texto no releído en LEG-03) | no verificado |
| `features/organizacion/services/designacion_engine.py` | Art. 4 | Reglamento General | Reglamento General, art. 4 (texto no leído en LEG-03) | no verificado |
| `features/organizacion/services/designacion_engine.py` | Art. 49 | Reglamento General | Reglamento General, art. 49 (texto no leído en LEG-03) | no verificado |
| `features/organizacion/services/designacion_engine.py` | Art. 5 | Reglamento del Delegado | Reglamento del Delegado, art. 5 (consolidado de LEG-01; texto no releído en LEG-03) | no verificado |
| `features/organizacion/services/designacion_engine.py` | Art. 56 | Reglamento General | Reglamento General, art. 56 (texto no leído en LEG-03) | no verificado |
| `features/organizacion/services/estructura_engine.py` | Art. 15 | Reglamento del Delegado | Reglamento del Delegado, art. 15 (consolidado de LEG-01; texto no releído en LEG-03) | no verificado |
| `features/organizacion/services/estructura_engine.py` | Art. 16 | Reglamento del Delegado | Reglamento del Delegado, art. 16 (consolidado de LEG-01; texto no releído en LEG-03) | no verificado |
| `features/organizacion/services/estructura_engine.py` | Art. 18 | Reglamento del Delegado | Reglamento del Delegado, art. 18 (consolidado de LEG-01; texto no releído en LEG-03) | no verificado |
| `features/organizacion/services/estructura_engine.py` | Art. 50 | LOPDP | LOPDP, art. 50 (Consideraciones especiales para el delegado de protección de datos personales) | verificado |
| `features/organizacion/services/estructura_engine.py` | Art. 56 | Reglamento General | Reglamento General, art. 56 (texto no leído en LEG-03) | no verificado |
| `features/organizacion/services/excepcion_sod_engine.py` | Art. 18 | Reglamento del Delegado | Reglamento del Delegado, art. 18 (consolidado de LEG-01; texto no releído en LEG-03) | no verificado |
| `features/regulacion_rag/services/conocimiento_engine.py` | Art. 12 | Ejemplo de formato | No es una cita: ejemplo del formato de búsqueda | verificado |
| `features/regulacion_rag/services/conocimiento_engine.py` | Art. 7 | Ejemplo de formato | No es una cita: ejemplo del formato de búsqueda | verificado |
| `features/regulacion_rag/services/diff_engine.py` | Art. 12 | LOPDP | LOPDP, art. 12 (Derecho a la información) | verificado |
| `features/regulacion_rag/services/diff_engine.py` | Art. 14 | LOPDP | LOPDP, art. 14 (Derecho de rectificación y actualización) | verificado |
| `features/regulacion_rag/services/rag_orchestrator.py` | Art. 12 | LOPDP | LOPDP, art. 12 (Derecho a la información) | verificado |
| `features/riesgos_mtge/domain/models.py` | Art. 12 | Res. SPDP-SPD-2026-0005-R | Res. SPDP-SPD-2026-0005-R, art. 12 (texto no leído en LEG-03) | no verificado |
| `features/riesgos_mtge/domain/models.py` | Art. 14 | Res. SPDP-SPD-2026-0005-R | Res. SPDP-SPD-2026-0005-R, art. 14 (texto no leído en LEG-03) | no verificado |
| `features/riesgos_mtge/domain/models.py` | Art. 8 | Res. SPDP-SPD-2026-0005-R | Res. SPDP-SPD-2026-0005-R, art. 8 (texto no leído en LEG-03) | no verificado |
| `features/riesgos_mtge/services/mtge_calculator.py` | Art. 10 | Res. SPDP-SPD-2026-0005-R | Res. SPDP-SPD-2026-0005-R, art. 10 (texto no leído en LEG-03) | no verificado |
| `features/riesgos_mtge/services/mtge_calculator.py` | Art. 8 | Res. SPDP-SPD-2026-0005-R | Res. SPDP-SPD-2026-0005-R, art. 8 (texto no leído en LEG-03) | no verificado |
| `features/riesgos_mtge/services/mtge_calculator.py` | Art. 9 | Res. SPDP-SPD-2026-0005-R | Res. SPDP-SPD-2026-0005-R, art. 9 (texto no leído en LEG-03) | no verificado |
| `features/riesgos_mtge/services/obligaciones_engine.py` | Art. 16 | Res. SPDP-SPD-2026-0005-R | Res. SPDP-SPD-2026-0005-R, art. 16 (texto no leído en LEG-03) | no verificado |
| `features/riesgos_mtge/services/obligaciones_engine.py` | Art. 17 | Res. SPDP-SPD-2026-0005-R | Res. SPDP-SPD-2026-0005-R, art. 17 (texto no leído en LEG-03) | no verificado |
| `features/riesgos_mtge/services/obligaciones_engine.py` | Art. 18 | Res. SPDP-SPD-2026-0005-R | Res. SPDP-SPD-2026-0005-R, art. 18 (texto no leído en LEG-03) | no verificado |
| `frontend/src/components/AyudaContextual.tsx` | Art. 7 | Ejemplo de formato | No es una cita: ejemplo del formato de búsqueda | verificado |
| `frontend/src/components/CommandPalette.tsx` | Art. 21 | LOPDP | LOPDP, arts. 12 a 20 (derechos del titular) | verificado |
| `frontend/src/components/CommandPalette.tsx` | Art. 37 | LOPDP | LOPDP, arts. 13 a 16 (plazo de quince días) y art. 62 (término de diez días para contestar) | verificado |
| `frontend/src/components/CommandPalette.tsx` | SLA 15 | LOPDP | LOPDP, arts. 13 a 16 (plazo de quince días) y art. 62 (término de diez días para contestar) | verificado |
| `frontend/src/components/CommandPalette.tsx` | SLA 72 | LOPDP | LOPDP, art. 43 (término de 5 días a la Autoridad; 2 días del encargado) y art. 46 (término de 3 días al titular) | verificado |
| `frontend/src/components/conocimiento/AyudaView.tsx` | Art. 7 | Ejemplo de formato | No es una cita: ejemplo del formato de búsqueda | verificado |
| `frontend/src/components/modules/ArcoModule.tsx` | Art. 13 | LOPDP | LOPDP, art. 13 (Derecho de acceso) | verificado |
| `frontend/src/components/modules/DpoCockpitModule.tsx` | Art. 17 | Reglamento del Delegado | Reglamento del Delegado, art. 17 (consolidado de LEG-01; texto no releído en LEG-03) | no verificado |
| `frontend/src/components/modules/DpoCockpitModule.tsx` | Art. 4 | Reglamento General | Reglamento General, art. 4 (texto no leído en LEG-03) | no verificado |
| `frontend/src/components/modules/DpoCockpitModule.tsx` | Art. 49 | LOPDP | LOPDP, art. 49 (Funciones del delegado de protección de datos personales) | verificado |
| `frontend/src/components/modules/DpoCockpitModule.tsx` | Art. 50 | LOPDP | LOPDP, art. 50 (Consideraciones especiales para el delegado de protección de datos personales) | verificado |
| `frontend/src/components/modules/MtgeModule.tsx` | Art. 48 | LOPDP | LOPDP, art. 48 (Delegado de protección de datos personales) | verificado |
| `frontend/src/components/modules/RatModule.tsx` | Art. 41 | LOPDP | LOPDP, art. 47 num. 12 y art. 51 (Registro Nacional); la LOPDP no regula un «registro de actividades de tratamiento» | verificado |
| `frontend/src/components/modules/mtge/ObligacionesGranEscala.tsx` | Art. 12 | Res. SPDP-SPD-2026-0005-R | Res. SPDP-SPD-2026-0005-R, art. 12 (texto no leído en LEG-03) | no verificado |
| `frontend/src/components/modules/mtge/ObligacionesGranEscala.tsx` | Art. 14 | Res. SPDP-SPD-2026-0005-R | Res. SPDP-SPD-2026-0005-R, art. 14 (texto no leído en LEG-03) | no verificado |
| `frontend/src/components/modules/mtge/ObligacionesGranEscala.tsx` | Art. 16 | Res. SPDP-SPD-2026-0005-R | Res. SPDP-SPD-2026-0005-R, art. 16 (texto no leído en LEG-03) | no verificado |
| `frontend/src/components/modules/roadmap/admin/DesignacionesTab.tsx` | Art. 3 | Reglamento del Delegado | Reglamento del Delegado, art. 3 (consolidado de LEG-01; texto no releído en LEG-03) | no verificado |
| `frontend/src/components/modules/roadmap/admin/DesignacionesTab.tsx` | Art. 49 | Reglamento General | Reglamento General, art. 49 (texto no leído en LEG-03) | no verificado |
| `frontend/src/components/modules/roadmap/admin/DesignacionesTab.tsx` | Art. 5 | Reglamento del Delegado | Reglamento del Delegado, art. 5 (consolidado de LEG-01; texto no releído en LEG-03) | no verificado |
| `frontend/src/lib/bancoPreguntas/bloque1.ts` | Art. 10 | LOPDP | LOPDP, art. 10 (Principios) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque1.ts` | Art. 25 | LOPDP | LOPDP, art. 25 (Categorías especiales de datos personales) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque1.ts` | Art. 26 | LOPDP | LOPDP, art. 26 (Tratamiento de datos sensibles) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque1.ts` | Art. 35 | LOPDP | LOPDP, art. 47 num. 12 y art. 51 (Registro Nacional); la LOPDP no regula un «registro de actividades de tratamiento» | verificado |
| `frontend/src/lib/bancoPreguntas/bloque1.ts` | Art. 47 | LOPDP | LOPDP, art. 47 (Obligaciones del responsable y encargado del tratamiento de datos personales) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque1.ts` | Art. 48 | Res. SPDP-SPD-2026-0005-R | Res. SPDP-SPD-2026-0005-R, art. 48 (texto no leído en LEG-03) | no verificado |
| `frontend/src/lib/bancoPreguntas/bloque1.ts` | Art. 7 | LOPDP | LOPDP, art. 7 (Tratamiento legítimo de datos personas) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque1.ts` | Art. 8 | LOPDP | LOPDP, art. 8 (Consentimiento) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque2.ts` | Art. 10 | LOPDP | LOPDP, art. 10 (Principios) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque2.ts` | Art. 17 | LOPDP | LOPDP, art. 17 (texto no leído en LEG-03) | no verificado |
| `frontend/src/lib/bancoPreguntas/bloque2.ts` | Art. 18 | LOPDP | LOPDP, art. 18 (Excepciones a los derechos de rectificación, actualización, eliminación, oposición, anulación y portabilidad) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque2.ts` | Art. 21 | LOPDP | LOPDP, art. 21 trata decisiones automatizadas sobre niñas, niños y adolescentes, no la representación legal; la cita correcta no se pudo fijar | no verificado |
| `frontend/src/lib/bancoPreguntas/bloque2.ts` | Art. 22 | LOPDP | LOPDP, art. 62 (requerimiento directo del titular al responsable) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque2.ts` | Art. 25 | LOPDP | LOPDP, art. 25 (Categorías especiales de datos personales) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque2.ts` | Art. 26 | LOPDP | LOPDP, art. 26 (Tratamiento de datos sensibles) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque2.ts` | Art. 30 | LOPDP | LOPDP, art. 62 (requerimiento directo del titular); el art. 30 trata datos de salud | verificado |
| `frontend/src/lib/bancoPreguntas/bloque2.ts` | Art. 31 | LOPDP | LOPDP, arts. 13 a 16 (plazo de quince días) y art. 62 (término de diez días para contestar) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque2.ts` | Art. 35 | LOPDP | LOPDP, art. 47 num. 12 y art. 51 (Registro Nacional); la LOPDP no regula un «registro de actividades de tratamiento» | verificado |
| `frontend/src/lib/bancoPreguntas/bloque2.ts` | Art. 38 | LOPDP | LOPDP, art. 37 (seguridad) y art. 39 (diseño y por defecto); el art. 38 es solo para el sector público | verificado |
| `frontend/src/lib/bancoPreguntas/bloque2.ts` | Art. 39 | LOPDP | LOPDP, art. 39 (Protección de datos personales desde el diseño y por defecto) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque2.ts` | Art. 46 | LOPDP | LOPDP, art. 47 num. 10 y 11 (contratos y garantías con el encargado) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque2.ts` | Art. 47 | LOPDP | LOPDP, art. 47 (Obligaciones del responsable y encargado del tratamiento de datos personales) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque2.ts` | Art. 56 | LOPDP | LOPDP, art. 56 (Transferencia o comunicación internacional de datos personales a países declarados como nivel adecuado de protección) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque2.ts` | Art. 57 | LOPDP | LOPDP, art. 57 (Transferencia o comunicación mediante garantías adecuadas) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque2.ts` | Art. 7 | LOPDP | LOPDP, art. 7 (Tratamiento legítimo de datos personas) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque2.ts` | Art. 8 | LOPDP | LOPDP, art. 8 (Consentimiento) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque3.ts` | Art. 10 | LOPDP | LOPDP, art. 10 (Principios) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque3.ts` | Art. 25 | LOPDP | LOPDP, art. 25 (Categorías especiales de datos personales) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque3.ts` | Art. 26 | LOPDP | LOPDP, art. 26 (Tratamiento de datos sensibles) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque3.ts` | Art. 38 | LOPDP | LOPDP, art. 37 (seguridad) y art. 39 (diseño y por defecto); el art. 38 es solo para el sector público | verificado |
| `frontend/src/lib/bancoPreguntas/bloque3.ts` | Art. 39 | LOPDP | LOPDP, art. 39 (Protección de datos personales desde el diseño y por defecto) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque3.ts` | Art. 40 | LOPDP | LOPDP, art. 43 (término de 5 días a la Autoridad; 2 días del encargado) y art. 46 (término de 3 días al titular) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque3.ts` | Art. 41 | LOPDP | LOPDP, art. 43 (término de 5 días a la Autoridad; 2 días del encargado) y art. 46 (término de 3 días al titular) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque3.ts` | Art. 42 | LOPDP | LOPDP, art. 42 (Evaluación de impacto del tratamiento de datos personales) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque3.ts` | Art. 43 | LOPDP | LOPDP, art. 42 (evaluación de impacto); el art. 43 es la notificación de vulneraciones | verificado |
| `frontend/src/lib/bancoPreguntas/bloque3.ts` | Art. 44 | LOPDP | Consulta previa: no aparece en el texto leído de la LOPDP; el art. 44 trata emergencias e incidentes informáticos | no verificado |
| `frontend/src/lib/bancoPreguntas/bloque3.ts` | Art. 47 | LOPDP | LOPDP, art. 47 (el num. 3 trata verificación y evaluación periódica, no capacitación) | verificado |
| `frontend/src/lib/bancoPreguntas/bloque3.ts` | Art. 7 | LOPDP | LOPDP, art. 7 (Tratamiento legítimo de datos personas) | verificado |
| `frontend/src/lib/bancoPreguntas/perfil.ts` | Art. 25 | LOPDP | LOPDP, art. 25 (Categorías especiales de datos personales) | verificado |
| `frontend/src/lib/bancoPreguntas/perfil.ts` | Art. 38 | Reglamento General | Reglamento General, art. 38 (texto no leído en LEG-03) | no verificado |
| `frontend/src/lib/bancoPreguntas/perfil.ts` | Art. 4 | LOPDP | LOPDP, art. 4 (Términos y definiciones) | verificado |
| `frontend/src/lib/bancoPreguntas/perfil.ts` | Art. 42 | LOPDP | LOPDP, art. 42 (Evaluación de impacto del tratamiento de datos personales) | verificado |
| `frontend/src/lib/bancoPreguntas/perfil.ts` | Art. 48 | LOPDP | LOPDP, art. 48 (Delegado de protección de datos personales) | verificado |
| `frontend/src/lib/conocimiento/api.ts` | Art. 7 | Ejemplo de formato | No es una cita: ejemplo del formato de búsqueda | verificado |
| `frontend/src/types/arco.ts` | Art. 21 | LOPDP | LOPDP, arts. 12 a 20 (derechos del titular) | verificado |
| `frontend/src/types/arco.ts` | Art. 37 | LOPDP | LOPDP, arts. 13 a 16 (plazo de quince días) y art. 62 (término de diez días para contestar) | verificado |
| `frontend/src/types/capa.ts` | Art. 10 | LOPDP | LOPDP, art. 10 (Principios) | verificado |
| `frontend/src/types/index.ts` | Art. 21 | LOPDP | LOPDP, arts. 12 a 20 (derechos del titular) | verificado |
| `frontend/src/types/rat.ts` | Art. 10 | LOPDP | LOPDP, art. 10 (Principios) | verificado |
| `frontend/src/types/rat.ts` | Art. 25 | LOPDP | LOPDP, art. 25 (Categorías especiales de datos personales) | verificado |
| `frontend/src/types/rat.ts` | Art. 35 | LOPDP | LOPDP, art. 47 num. 12 y art. 51 (Registro Nacional); la LOPDP no regula un «registro de actividades de tratamiento» | verificado |
| `frontend/src/types/rat.ts` | Art. 44 | LOPDP | LOPDP, art. 42 (evaluación de impacto) | verificado |
| `frontend/src/types/rat.ts` | Art. 48 | LOPDP | LOPDP, art. 48 (Delegado de protección de datos personales) | verificado |
| `frontend/src/types/rat.ts` | Art. 7 | Res. SPDP-SPD-2025-0041-R | Res. SPDP-SPD-2025-0041-R, art. 7 (texto no leído en LEG-03) | no verificado |

## Criterio para las fichas de frontend (UX/UI y Arquitecto)

- La cita siempre con la forma «LOPDP, art. 47» o «Reglamento General, art. 56».
- Nada de «SLA»: el plazo completo, con su unidad y desde cuándo cuenta. Mientras la unidad sea `no verificado`, se usa la palabra literal de la ley («término de cinco días», «plazo de quince días»).
- Sin artículos en los subtítulos del menú: van en `AyudaContextual`.
- Una cita no verificada no se muestra: basta el nombre de la obligación.

## Cómputo de plazos y términos (2026-11-08)

Ficha `LEG-04`. Textos leídos y cotejados por el CTO el 2026-11-08 a pedido del propietario. Completa el hallazgo 1, que dejaba la unidad como `no verificado`.

- **Remisión al COA.** LOPDP, Disposición General Primera: «En lo dispuesto al procedimiento administrativo se estará a lo previsto en el Código Orgánico Administrativo».
- **Código Orgánico Administrativo** (RO 2S 31, 7-VII-2017; última reforma RO S 623, 21-I-2022):
  - art. 158: los términos solo se fijan en días y los plazos en meses o años; ambos se computan desde el día hábil siguiente a la presentación de la petición;
  - art. 159: «Se excluyen del cómputo de términos los días sábados, domingos y los declarados feriados». Es decir, **término = días hábiles**;
  - art. 160: el plazo se computa de fecha a fecha. Es decir, **plazo = días corridos**.
- **LOPDP art. 64:** si el responsable no contesta «en el término establecido» (art. 62: término de 10 días para contestar, notificar y ejecutar), el titular puede reclamar ante la Autoridad.
- **Reglamento General** (DE 904, RO 3S 435, 13-XI-2023), leído en la compilación de `cosede.gob.ec`:
  - art. 14: el responsable puede pedir aclaración una sola vez, en el término de 5 días desde que recibe la solicitud; el titular tiene un término de 10 días, desde el día siguiente a la notificación, para aclarar;
  - art. 16: el reclamo se tramita según el COA;
  - el Reglamento no fija otro plazo de respuesta.

**Propuesta de parámetro.** Vence lo primero entre 10 días hábiles (art. 62, con el COA art. 159) y 15 días corridos (arts. 13 a 16). Estado: **propuesto, pendiente del abogado**.

**Criterio del abogado sobre los plazos por tipo de solicitud (2026-11-09).** Sustituye la propuesta anterior en lo que fija. Fuente: la descripción de los PR #557 y #558 de Aleczandra y la comunicación del propietario; no es el texto de un artículo leído aquí.
- **15 días:** acceso, rectificación, eliminación y oposición (LOPDP, arts. 13 a 16). Estado: validado por un abogado local, comunicado por el propietario el 2026-11-09; el documento del abogado no consta en el repositorio.
- **10 días:** portabilidad, suspensión, decisiones automatizadas y quejas (LOPDP, art. 62). Estado: validado por un abogado local, comunicado por el propietario el 2026-11-09; el documento del abogado no consta en el repositorio. La «queja» es una solicitud al responsable con el plazo del art. 62; la reclamación ante la Autoridad es otro procedimiento (arts. 63 y 64, no leídos aquí) y no se modela ni se le afirma plazo.
- **Unidad (hábiles o corridos): sigue pendiente.** El propietario no la mencionó. Con la lectura del COA (arts. 158 a 160) de este mismo apartado, «término» son días hábiles, y el art. 62 dice «término de diez (10) días»; eso es una lectura nuestra, **no resuelta por el abogado**. La regla provisional de DER-05 son días corridos, que es la más estricta, y va marcada como estimada en la interfaz.
- No cambia lo de Vertex (otro dictamen) ni las plantillas con «PENDIENTE VALIDACIÓN» fuera de las seis ya validadas.

**Advertencias para el abogado.**
1. El COA regula a la administración pública. Extenderlo al responsable privado es una interpretación, sostenida por la remisión de la Disposición General Primera.
2. La LOPDP fija un «plazo» en días, cuando el art. 158 del COA reserva el plazo para meses o años.
3. Los textos leídos son compilaciones (Lexis, `casadelacultura.gob.ec`, `cosede.gob.ec`), no el PDF del Registro Oficial.

**Fuentes.**
- COA: https://casadelacultura.gob.ec/lotaip/16/2023/Mayo/C%c3%b3digo%20Org%c3%a1nico%20Administrativo%20COA.pdf
- Reglamento General: https://www.cosede.gob.ec/wp-content/uploads/2023/12/REGLAMENTO-GENERAL-A-LA-LEY-ORG%C3%81NICA-DE-PROTECCION-DE-DATOS-PERSONALES_compressed-1.pdf

## No verificado

- El texto de todos los artículos del Reglamento General (Decreto Ejecutivo 904). Solo se leyó la portada, porque el PDF está escaneado.
- La equivalencia entre «término» y días hábiles, y entre «plazo» y días calendario (Código Orgánico Administrativo).
- La consulta previa a la SPDP como trámite.
- La Guía de gestión de riesgos y EIPD (Res. SPDP-SPD-2025-0003-R) y la metodología de multas (Res. SPDP-SPD-2025-0022-R).
- Las resoluciones SPDP-SPD-2026-0005-R (gran escala), 2025-0041-R (interés legítimo) y 2026-0039-R (biometría), que cita el código.
- El Reglamento del Delegado: no se releyó; se remite a LEG-01.
- El cotejo de la compilación de la LOPDP con el PDF del Registro Oficial Suplemento 459.

## Anexo: índice de artículos de la LOPDP leídos

Títulos tal como aparecen en el texto leído; base de la columna «Cita correcta».

| Art. | Título |
|---|---|
| 1 | Objeto y finalidad |
| 2 | Ámbito de aplicación material |
| 3 | Ámbito de aplicación territorial |
| 4 | Términos y definiciones |
| 5 | Integrantes del sistema de protección de datos personales |
| 6 | Normas aplicables al ejercicio de derechos |
| 7 | Tratamiento legítimo de datos personas |
| 8 | Consentimiento |
| 9 | Interés legítimo |
| 10 | Principios |
| 11 | Normativa especializada |
| 12 | Derecho a la información |
| 13 | Derecho de acceso |
| 14 | Derecho de rectificación y actualización |
| 15 | Derecho de eliminación |
| 16 | Derecho de oposición |
| 18 | Excepciones a los derechos de rectificación, actualización, eliminación, oposición, anulación y portabilidad |
| 19 | Derecho a la suspensión del tratamiento |
| 20 | Derecho a no ser objeto de una decisión basada única o parcialmente en valoraciones automatizadas |
| 21 | Derecho de niñas, niños y adolescentes a no ser objeto de una decisión basada única o parcialmente en valoraciones automatizadas |
| 22 | Derecho de consulta |
| 23 | Derecho a la educación digital |
| 24 | Ejercicio de derechos |
| 25 | Categorías especiales de datos personales |
| 26 | Tratamiento de datos sensibles |
| 27 | Datos personales de personas fallecidas |
| 28 | Datos crediticios |
| 29 | Derechos de los Titulares de Datos Crediticios |
| 30 | Datos relativos a la salud |
| 31 | Tratamiento de datos relativos a la salud |
| 32 | Tratamiento de datos de salud por entes privados y públicos con fines de investigación |
| 33 | Transferencia o comunicación de datos personales |
| 34 | Acceso a datos personales por parte del encargado |
| 35 | Acceso a datos personales por parte de terceros |
| 36 | Excepciones de consentimiento para la transferencia o comunicación de datos personales |
| 37 | Seguridad de datos personales |
| 38 | Medidas de seguridad en el ámbito del sector público |
| 39 | Protección de datos personales desde el diseño y por defecto |
| 40 | Análisis de riesgo, amenazas y vulnerabilidades |
| 41 | Determinación de medidas de seguridad aplicables |
| 42 | Evaluación de impacto del tratamiento de datos personales |
| 43 | Notificación de vulneración de seguridad |
| 44 | Acceso a datos personales para atención a emergencias e incidentes informáticos |
| 45 | Garantía del secreto de las comunicaciones y seguridad de datos personales |
| 46 | Notificación de vulneración de seguridad al titular |
| 47 | Obligaciones del responsable y encargado del tratamiento de datos personales |
| 48 | Delegado de protección de datos personales |
| 49 | Funciones del delegado de protección de datos personales |
| 50 | Consideraciones especiales para el delegado de protección de datos personales |
| 51 | Registro Nacional de protección de datos personales |
| 52 | Autorregulación |
| 53 | Códigos de conducta |
| 54 | Entidades de Certificación |
| 55 | Transferencia o comunicación internacional de datos personales |
| 56 | Transferencia o comunicación internacional de datos personales a países declarados como nivel adecuado de protección |
| 57 | Transferencia o comunicación mediante garantías adecuadas |
| 58 | Normas corporativas vinculantes |
| 59 | Autorización para transferencia internacional |
| 60 | Casos excepcionales de transferencias o comunicaciones internacionales |
| 61 | Control continuo |
| 62 | Requerimiento directo del titular del dato de carácter personal al responsable del tratamiento |
| 63 | Actuaciones previas |
| 64 | Procedimiento administrativo |
| 65 | Medidas correctivas |
| 66 | Aplicación de medidas correctivas |
| 67 | Infracciones leves del Responsable de protección de datos |
| 68 | Infracciones graves del Responsable de protección de datos |
| 69 | Infracciones leves del Encargado de protección de datos |
| 70 | Infracciones graves del Encargado de protección de datos |
| 71 | Sanciones por infracciones leves |
| 72 | Sanciones por infracciones graves |
| 73 | Volumen de negocio |
| 74 | Medidas provisionales o cautelares |
| 75 | Autoridad de protección de datos personales |
| 76 | Funciones atribuciones y facultades |
| 77 | Del titular de la Autoridad de Protección de Datos |

<!-- --- INICIO LEG-05 --- -->
<!-- --- FIN LEG-05 --- -->
