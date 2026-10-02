# Propuesta: bloque «Perfil de operación» al inicio del diagnóstico

Estado: **implementado** en la ficha organizacional (frontend). Ver sección 8 para la validación normativa y lo pendiente.

## 1. Problema

Hoy el cuestionario se adapta **solo por número de empleados** (`tamanoMinimo` en cada pregunta). Con eso, de las 80 preguntas del banco:

| Tamaño | Preguntas que recibe |
|---|---|
| Microempresa (1-9) | 39 |
| Pequeña (10-49) | 59 |
| Mediana (50-199) | 73 |
| Corporativo (200 o más) | 80 |

El tamaño no dice qué hace la organización con los datos, y falla en dos sentidos:

- **Pregunta de más.** Una organización grande que vende solo a otras empresas y no recibe datos por internet igual responde las preguntas 18 y 35 (canales en línea y cookies), que no le corresponden. Esto produce brechas artificiales y la frustración que ya reportan las usuarias.
- **Pregunta de menos.** Una organización de 8 empleados que maneja datos sensibles (por ejemplo, salud) recibe solo 39 preguntas y no ve controles críticos para su riesgo real, como la evaluación del Delegado de Protección de Datos (3), el registro de accesos (52), la clasificación de incidentes (59), el análisis de riesgos (65) o la seudonimización (40). El diagnóstico queda incompleto aunque la persona haya respondido todo.

## 2. Idea central

Agregar, antes de las 80 preguntas, un bloque de selectores **Sí / No**, como los de la imagen de referencia. Las respuestas definen un **perfil de operación** que actúa en paralelo al tamaño:

> Preguntas que se hacen = (las que corresponden por tamaño) **+** (las que el perfil obliga a incluir) **−** (las que el perfil descarta)

Reglas fijas:

1. **Solo existen «Sí» y «No».** No hay «No sé»: la persona a cargo del diagnóstico consulta al área correspondiente y responde con certeza antes de continuar.
2. **Lo que obliga a incluir gana sobre lo que descarta.** Si un control es descartado por una respuesta y exigido por otra, se pregunta.
3. **Los controles estructurales nunca se descartan:** 9 (inventario), 10 (RAT), 13 (datos sensibles) y 28 (verificación de identidad).
4. Todo control descartado queda **registrado como «No aplica por perfil»**, con la respuesta que lo motivó. No desaparece del informe.

## 3. Selectores propuestos

### 3.1 Los que descartan preguntas (respuesta «No»)

| N.º | Pregunta al usuario | Si responde «No», se descartan | Cantidad |
|---|---|---|---|
| S1 | ¿Recibe datos de personas por internet (página web, formularios en línea, redes sociales, aplicación o tienda en línea)? | 18, 35 | 2 |
| S2 | ¿Usa los datos de las personas para enviarles publicidad, promociones, encuestas u otros fines para los que necesite su permiso? | 21, 22, 36 | 3 |
| S3 | ¿Tiene cámaras de seguridad? | 38 | 1 |
| S4 | ¿Trabaja con terceros que ven o guardan datos de personas (contador, empresa de nómina, mensajería, servicios en internet, soporte técnico)? | 41, 42, 43, 44, 47, 48 | 6 |
| S5 | ¿Guarda información o usa programas contratados por internet (la «nube»)? | 45 | 1 |
| S6 | ¿Envía o guarda datos de personas fuera del país (incluye servicios cuyos servidores están en el exterior)? | 46 | 1 |
| S7 | ¿Desarrolla o prueba sistemas propios, o hace estadísticas o análisis con datos de personas? | 40, 55 | 2 |
| S8 | ¿Toma decisiones sobre personas con programas automáticos (aprobar créditos, calificar, seleccionar personal)? | 72 | 1 |

Más una regla combinada: la pregunta **67** (evaluación de impacto realizada) se descarta solo si S8 y S9 y S10 son «No» a la vez.

Máximo de preguntas que se pueden descartar: **19** (incluye la 4 si responde «No» a S11).

### 3.2 Los que obligan a incluir preguntas (respuesta «Sí»)

| N.º | Pregunta al usuario | Si responde «Sí», se agregan aunque el tamaño no las pida |
|---|---|---|
| S9 | ¿Maneja datos sensibles: salud, huellas digitales o biometría, religión, origen étnico, orientación sexual, antecedentes penales o datos de niñas, niños y adolescentes? | **Paquete de datos sensibles:** 3, 4, 40, 52, 59, 61, 63, 64, 65, 71 (10 preguntas). Si además respondió «Sí» en S4: 42, 47, 48. Además sube a criticidad máxima las preguntas 49, 50, 51, 53, 57 y 58. |
| S10 | ¿Maneja datos de una gran cantidad de personas? (más de 10.000 en 12 meses, o geolocalización de personas) | **Paquete de escala:** 3, 4, 5, 6, 8, 16, 34, 65, 76 (9 preguntas) |

La cifra que define «gran cantidad» y la lista de datos sensibles deben validarse con la LOPDP y su Reglamento antes de fijarse en el sistema. Aquí son ejemplos de redacción, no criterio legal.

### 3.2 bis. Selector del Delegado de Protección de Datos

| N.º | Pregunta al usuario | Efecto |
|---|---|---|
| S11 | ¿Está obligada a tener un Delegado de Protección de Datos (DPO)? Responda Sí si es una entidad pública, si vigila de forma constante a las personas o si maneja datos sensibles de muchas personas. | «Sí»: se agregan las preguntas 3 y 4. «No»: se descarta la 4. Si responde «No» pero la ficha indica sector público, o datos sensibles y gran cantidad de personas, se muestra un aviso (no bloquea). |

Fundamento: LOPDP Art. 48 (se designa Delegado cuando el tratamiento lo realiza el sector público, cuando la actividad exige un control permanente y sistematizado, o cuando se tratan categorías especiales de datos a gran escala). Texto contrastado con el de la ley.

### 3.3 Preguntas informativas (no cambian la cantidad)

No descartan nada. Sirven para ajustar el texto de los ejemplos y para el informe:

- ¿Atiende principalmente a personas (consumidores o socios) o a otras empresas?
- ¿Trata datos por encargo de otras organizaciones (por ejemplo, procesa nóminas o atiende llamadas para terceros)?

Aunque la organización venda solo a otras empresas, sigue tratando datos personales de sus contactos, empleados y proveedores. Por eso estas preguntas no pueden usarse para descartar el derecho de acceso, el aviso de privacidad ni la seguridad.

## 4. Cómo afecta al compendio de 80 preguntas

- **El banco no cambia.** Siguen siendo 80 preguntas con sus identificadores 1 a 80. Se mantiene la regla de que nunca se muestran más de 80.
- **Cambia el subconjunto que se pregunta**, que ahora depende de tamaño y perfil.
- **Rango posible:** un corporativo recibe entre 61 (todos los «No») y 80 preguntas. Una microempresa recibe entre 31 (todos los «No») y 58 (con ambos paquetes reforzados y terceros).

### Ejemplos ilustrativos

Las respuestas son supuestas. No son criterios ni datos de las organizaciones mencionadas.

| Caso | Base por tamaño | Ajuste por perfil | Resultado |
|---|---|---|---|
| Organización grande que vende a empresas y no recibe datos en internet (S1 «No», S8 «No») | 80 | −2 (18, 35) −1 (72) | 77 |
| La misma, además sin publicidad y sin cámaras (S2 «No», S3 «No») | 80 | −2 −1 −3 −1 | 73 |
| Microempresa de 8 empleados con datos de salud, sin internet, sin publicidad, sin terceros, sin decisiones automáticas | 39 | +10 (paquete S9) −1 (35) −3 (21, 22, 36) −2 (41, 43) −1 (72) | 42 |

En el tercer caso el número casi no varía, pero el contenido cambia: se quitan preguntas que no corresponden y entran las críticas para datos sensibles, como la 3, 4, 52, 59, 61, 63, 64, 65, 71 y 40.

### Efecto en la puntuación

- El porcentaje de madurez se calcula **solo sobre las preguntas que aplican**, ponderadas por criticidad como hoy. Una pregunta descartada no resta ni suma.
- El informe muestra el alcance: «Se evaluaron 73 de 80 controles. 7 no aplican por su perfil: sin canales en internet (18, 35), sin publicidad (21, 22, 36) …».
- Las descartadas aparecen en una sección aparte con el motivo, para que un auditor pueda revisarlas.

## 5. Riesgos y cómo se mitigan

| Riesgo | Mitigación |
|---|---|
| Alguien responde «No» a todo para tener menos preguntas | El responsable confirma haber consultado al área correspondiente; el informe lista lo descartado y por qué. Los estructurales no se pueden descartar. |
| Respuesta del perfil contradicha después por evidencia (por ejemplo, se carga un contrato con un proveedor y S4 decía «No») | El sistema reactiva los controles afectados y avisa. |
| Preguntas que dependen de varias respuestas (67) | Regla combinada documentada y probada. |
| Cifras o listas de «datos sensibles» y «gran cantidad» sin respaldo legal | Validar con el texto de la LOPDP, su Reglamento y las resoluciones de la SPDP antes de implementar. |
| Cambiar el perfil a mitad del diagnóstico | Al cambiarlo, se recalcula el conjunto y se conservan las respuestas ya dadas. |

## 6. Trabajo necesario (si se aprueba)

1. **Datos:** guardar las 10 respuestas (Sí, No) junto a la ficha de la organización.
2. **Banco de preguntas** (`tipos.ts`): agregar a cada pregunta qué respuestas la descartan y qué respuestas la exigen. Reemplazar `aplicaATamano` por una función que considere tamaño y perfil.
3. **Pantalla inicial:** bloque de selectores con el formato de la imagen, en lenguaje sencillo y con una explicación breve por pregunta.
4. **Cálculo y reporte:** que el motor de diagnóstico, el resumen de alcance y el informe usen el subconjunto aplicable y muestren los controles «No aplica por perfil».
5. **Textos:** quitar las frases «esta pregunta no aplica» de los ejemplos, que pasan a ser innecesarias.
6. **Pruebas:** casos para cada selector, los paquetes reforzados, la regla de 67 y la precedencia de lo que obliga sobre lo que descarta.

## 7. Decisiones tomadas

1. Dos ejes (tamaño y perfil); solo «Sí» o «No»; sin casilla de confirmación.
2. Definiciones validadas contra la LOPDP, su Reglamento y la Resolución SPDP-SPD-2026-0005-R (sección 8).
3. El tamaño se calcula con empleados directos afiliados al IESS más personas bajo contrato de servicios (cuentas contables de servicios).

## 8. Validación normativa e implementación

| Elemento | Fuente | Cómo se usó |
|---|---|---|
| Datos sensibles | LOPDP Art. 4 (datos sensibles: etnia, identidad de género, cultura, religión, ideología, afiliación política, pasado judicial, condición migratoria, orientación sexual, salud, biométricos, genéticos) y Art. 25 (categorías especiales: sensibles, niñas, niños y adolescentes, salud, discapacidad) | Texto de ayuda del selector S9 |
| EIPD y Delegado para categorías especiales a gran escala | LOPDP Arts. 42 y 48 | Paquetes reforzados: preguntas 3, 4, 65, 66, 67 |
| Tamaño no decide el RAT | Reglamento Arts. 38 y 39 (100 o más trabajadores; menos de 100 si hay riesgo, tratamiento no ocasional o categorías especiales) | Justifica el perfil como eje adicional; las preguntas 9 y 10 nunca se descartan |
| Gran escala | Resolución SPDP-SPD-2026-0005-R: Modelo Técnico de Gran Escala con seis variables; la variable «titulares» puntúa por tramos (hasta 1.000; 1.001-10.000; 10.001-100.000; más de 100.000); umbral de 6 puntos | Umbral de 10.000 titulares en S10 |
| Supuestos de gran escala directa | Misma resolución: salud, biometría, menores, geolocalización, perfilamiento automatizado, transferencias sistemáticas, videovigilancia en espacios públicos | Cubiertos por S9 (salud, biometría, menores), S10 (geolocalización), S8 (perfilamiento), S6 (transferencias) y S3 (cámaras) |
| Tamaño de la organización | IESS (empleados directos) y cuentas contables de servicios (personas bajo contrato) | Dos campos numéricos en la ficha; el tamaño se calcula con su suma |

Las tres últimas fuentes se contrastaron con comentarios jurídicos publicados (Lexis Ecuador, EY, Meythaler Zambrano). **No pude leer el PDF oficial de la resolución:** los tramos de «titulares» y el umbral de 6 puntos provienen de un solo resumen y deben confirmarse en el texto oficial antes de darlos por definitivos.

### Discrepancia detectada en el repositorio

El motor `features/riesgos_mtge/services/mtge_calculator.py` usa tramos de titulares (1.000, 10.000, 50.000) y un umbral de 100 puntos que no coinciden con lo publicado sobre la resolución (tramos hasta 1.000, 10.000 y 100.000, y umbral de 6 puntos). Esto no afecta a esta función, pero conviene revisarlo.

### Lo implementado

- Perfil de operación: `frontend/src/lib/bancoPreguntas/perfil.ts` (selectores, reglas, paquetes).
- Poda por tamaño y perfil: `tipos.ts` y `resumenPoda.ts` (el perfil es un tercer argumento opcional; sin perfil el comportamiento es el anterior).
- Ficha: `ProjectConfig.tsx` (empleados IESS, contratados por servicios y los diez selectores).
- Alcance verificado: base por tamaño 39/59/73/80; con todo «No» 31/47/56/62; con todo «Sí» 58/70/75/80.

### Pendiente

- El componente `ResumenPoda.tsx` (detalle de controles no aplicables y su motivo) ya estaba sin montar en ninguna pantalla; quedó actualizado pero sigue sin mostrarse.
- El snapshot sellado no guarda el perfil de operación; solo respeta el conjunto de preguntas que resultó de él.
- Pruebas automatizadas: solo hay pruebas de extremo a extremo (Playwright); la lógica se verificó con un script y en el navegador.
