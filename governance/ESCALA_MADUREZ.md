# Escala de madurez del SGPDP
`¤diagnostico-scoring`

**Vigente desde el 2026-10-29, por decisión del propietario.** La madurez de la plataforma sigue el archivo de assessment SMARTCIDI (`Assessment_Madurez_SGPDP_COAC_SMARTCIDI (2).xlsx`) y sustituye a la escala 0 a 3 y a los estados «no implementado, parcial, implementado» como entrada del diagnóstico.

## 1. Fuente única

`governance/contratos/escala_madurez.json` manda sobre cualquier otro texto. PRD, metodologías, fichas, especificaciones, servidor y pantalla remiten a ese contrato; ninguno define otra escala ni copia sus números a mano. Las tablas de este documento se generan desde él.

El árbitro es `scripts/verificar_escala_madurez.py`, que corre en la suite con `tests/test_escala_madurez.py`.

## 2. Valores

<!-- tablas-generadas:inicio -->
### Nivel asignado

| Nivel | Nombre | Criterio | Puntaje de dimensión |
| :--- | :--- | :--- | :--- |
| 1 | Inicial / Reactivo | No existe o se gestiona informalmente | 0 a 39 |
| 2 | Básico / Repetible | Prácticas aisladas o documentos iniciales | 40 a 59 |
| 3 | Definido / Documentado | Políticas, matrices, procedimientos y responsables definidos | 60 a 74 |
| 4 | Gestionado / Demostrable | Se aplica, se revisa, tiene seguimiento y métricas | 75 a 89 |
| 5 | Optimizado / Mejora continua | Integrado a gobierno, riesgos y seguridad, con mejora demostrable | 90 a 100 |

### Nivel de evidencia

| Nivel | Nombre |
| :--- | :--- |
| 0 | Verbal: sin evidencia |
| 1 | Informal: correo, captura, práctica no formalizada |
| 2 | Documental: política, matriz, procedimiento, contrato |
| 3 | Operativa: registros de aplicación |
| 4 | Revisada: auditada o revisada por la dirección |

### Umbrales

| Regla | Valor |
| :--- | :--- |
| Riesgo crítico desde | 15 |
| Riesgo alto desde | 9 |
| Riesgo medio desde | 5 |
| Criticidad de un control bloqueante | 5 |
| Control degradado con nivel efectivo menor que | 3 |
| Tope de la dimensión por control bloqueante degradado | 2 |
| Criticidad desde la que se exige evidencia | 4 |
| Evidencia exigible | 2 |
| Tope de la dimensión por evidencia insuficiente | 3 |
| Cobertura mínima para emitir nivel | 60 % |

### Dimensiones

| Id | Dimensión | Peso |
| :--- | :--- | :--- |
| D01 | Gobierno y responsabilidad proactiva | 0.12 |
| D02 | Inventario, RAT, finalidades y legitimación | 0.14 |
| D03 | Transparencia e información al titular | 0.08 |
| D04 | Derechos de titulares | 0.08 |
| D05 | Procesos críticos y ciclo de vida de datos | 0.10 |
| D06 | Encargados, proveedores y transferencias | 0.10 |
| D07 | Seguridad de datos personales | 0.14 |
| D08 | Incidentes y vulneraciones | 0.08 |
| D09 | Riesgos, EIPD, LIA y privacidad desde el diseño | 0.11 |
| D10 | Capacitación, cultura, auditoría y mejora continua | 0.05 |
<!-- tablas-generadas:fin -->

## 3. Cálculo

Por control aplicable:

- `nivel efectivo = MIN(nivel asignado, nivel de evidencia + 1)`. La evidencia limita lo que se reconoce: con evidencia documental (2) el máximo es 3.
- `score = nivel efectivo / 5 × criticidad`.
- `riesgo de brecha = (5 − nivel efectivo) × criticidad`.
- Sin responder computa como cero y sigue en el denominador. `Aplica = No` sale del cálculo.

Por dimensión:

- `puntaje = Σ score / Σ criticidad × 100`, sobre los controles aplicables.
- El nivel sale de los rangos de la tabla.
- Por debajo de la cobertura mínima el nivel es 0, «Sin evaluación suficiente». Es falta de datos, no un nivel bajo.

Regla práctica de calificación (hoja «Guía Aplicación Comercio»): si el control debería existir y no existe, nivel 1 y evidencia 0; documento sin uso, máximo 3; con registros de aplicación, 4; con indicadores y mejora continua, 5.

## 4. Diferencias deliberadas con el archivo

El archivo es la referencia, pero la plataforma se aparta de él en estos puntos. Ninguno es un olvido; cambiarlos exige decisión del propietario.

| El archivo | La plataforma | Motivo |
| :--- | :--- | :--- |
| Calcula «Madurez global ponderada», «Nivel final ajustado» y «Resultado ejecutivo» (hoja Dashboard) | **No hay cifra ni nivel de la organización.** Los pesos quedan en el catálogo, pero no combinan dimensiones | `INV_LOPDP_MULTIDIMENSIONAL_METRICS`: un promedio esconde brechas jurídicas |
| Aplica los topes por bloqueantes y por evidencia insuficiente al nivel global | Los aplica **dentro de cada dimensión** | Al no haber nivel global, el tope limita la dimensión donde está la brecha |
| Marca «Bloqueante de madurez» control por control | Es bloqueante todo control de criticidad 5 | Son equivalentes en los 80 controles; el árbitro lo comprueba contra el archivo |
| Evidencia 4: «gestionada» en Catálogos y «revisada» en la Guía | «Revisada» | El propio archivo usa dos nombres |
| Criterios de nivel y de evidencia en texto largo | Textos abreviados para la pantalla | El nivel y su sentido no cambian |
| Dimensión 5: «Procesos críticos de comercio y ciclo de vida de datos» | «Procesos críticos y ciclo de vida de datos» | La plataforma es multisectorial. El nombre del archivo dice COAC y su contenido, sector comercio |
| No tiene estado de conformidad por control | El servidor deriva `estado`: 1 No Conforme, 2 y 3 Parcial, 4 y 5 Conforme, sin nivel Pendiente | Hoja de ruta, preanálisis y hallazgos leen ese campo. Nunca es una entrada |

El archivo no es una certificación legal, y su propia nota lo advierte. Tampoco la madurez es conformidad jurídica: ambas se muestran por separado.

## 5. Datos existentes

Los resultados ya sellados son inmutables y conservan su forma; al leerlos llevan `escala = "anterior"`. En las respuestas guardadas, la evidencia sube un nivel (1→2, 2→3, 3→4) y `nivel_asignado` queda vacío, porque un «Parcial» antiguo no permite saber si era 2 o 3. Esas preguntas cuentan como pendientes hasta volver a responderlas. El detalle está en `governance/especificaciones/DIAG-08.md`.

## 6. Cómo cambiar la escala

El orden evita lo ocurrido con DIAG-08, que retiró `score_ponderado` y `nivel_ajustado` mientras `features/roadmap/services/contexto_generacion.py`, de otra sala, los seguía leyendo.

1. El propietario decide el cambio y queda anotado aquí.
2. Se cambia primero el contrato y se regeneran las tablas con `python scripts/verificar_escala_madurez.py --escribir`.
3. Antes de retirar un campo o un nombre se añade a `vocabulario_retirado`. El árbitro lista entonces todos sus consumidores, en cualquier sala, y cada uno se corrige en el mismo PR o se anota en `consumidores_pendientes` con la tarea que lo retira.
4. `consumidores_pendientes` solo puede encoger: un uso nuevo falla, y una anotación cumplida también, hasta quitarla.
5. Si la tarea que retira un campo no incluye a un consumidor en su `propiedad`, se amplía la ficha antes de empezar, no al final con el CI en rojo.
6. Un campo legítimo para leer resultados antiguos va en `lectura_historica`, con su motivo.
7. Si cambia el archivo de assessment, el árbitro falla por su huella: se revisa el contrato y solo entonces se actualiza `fuente.sha256`.
