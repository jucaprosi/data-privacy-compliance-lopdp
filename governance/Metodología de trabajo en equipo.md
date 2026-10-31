# Metodología de trabajo en equipo — EVYDENTIA

> **Estado: borrador vivo (2026-10-30).** Redactado con asistencia de IA a partir de lo que el equipo ha vivido. Cada parte indica qué es regla vigente, qué es práctica recomendada y qué está por confirmar. Nada aquí es asesoría legal.

## Para qué sirve
Documentar **cómo trabaja el equipo** (personas y agentes de IA) en EVYDENTIA y los procesos que han funcionado, de modo que:
1. Cualquier persona nueva entienda el modelo en una tarde.
2. Las decisiones no dependan de la memoria de un chat.
3. Lo aprendido se pueda **reutilizar en otros proyectos** (ver «Qué es reutilizable» abajo).

## Índice

| # | Parte | Contenido |
| :-- | :-- | :-- |
| 1 | [Principios](#parte-1-principios) | Las reglas de fondo, en una página |
| 2 | [Roles y autorización](#parte-2-roles-y-autorización) | Quién decide qué (por confirmar) |
| 3 | [Flujo de trabajo](#parte-3-flujo-de-trabajo) | Fichas, tandas, ramas, PR, rutina diaria y bases de pruebas |
| 4 | [Verificación y evidencia](#parte-4-verificación-y-evidencia) | Cómo saber que algo está hecho |
| 5 | [Seguridad y credenciales](#parte-5-seguridad-y-credenciales) | Qué no se muestra, cómo se rota |
| 6 | [Estado compartido y registro](#parte-6-estado-compartido-y-registro) | Dónde chocan los agentes |
| 7 | [Lecciones aprendidas](#parte-7-lecciones-aprendidas) | Casos reales y qué enseñan |
| 8 | [Plantillas](#parte-8-plantillas) | Briefs, partes, autorizaciones, informes |
| 9 | [Glosario](#parte-9-glosario) | Términos en lenguaje claro |

## Parte 1. Principios

> Estado: práctica recomendada (borrador). Los principios 1 a 4 reflejan reglas que el proyecto ya aplica; el resto son recomendaciones del equipo.

1. **El agente informa, la compuerta decide, la persona autoriza.** Un agente nunca se califica a sí mismo. Decide el CI y otros árbitros automáticos; autoriza una persona.
2. **Sin evidencia contrastable no es «hecho».** Evidencia = PR, commit, checks «X de Y terminados», log. Una frase («probé y va bien») no lo es. Ver Parte 4.
3. **Un archivo o recurso, un dueño.** Lo que dos tareas tocan a la vez se ordena o se le asigna dueño antes de lanzar agentes. Ver Parte 6.
4. **Lo irreversible o compartido se autoriza en el chat del agente que lo ejecuta**, con palabras de la persona, tras preguntar *qué se rompe si sale mal y cómo se deshace*.
5. **Parar y preguntar vale más que improvisar.** Un agente que se detiene ante un dato inesperado está bien controlado.
6. **Separar siempre «comprobado» de «supuesto»** en informes, reuniones y descripciones de PR.
7. **Lanzar solo lo que se pueda revisar.** El límite de agentes simultáneos lo pone la atención de quien revisa, no la máquina.
8. **Una credencial que aparece en una captura o chat se considera filtrada y se rota.** Sin discutir el nivel de riesgo. Ver Parte 5.
9. **Lo aprendido se escribe.** Si una lección solo vive en un chat, se pierde. Ver Parte 7.
10. **Lo legal no lo cierra un agente.** Contenido normativo: fuente oficial cotejada o «POR VERIFICAR».

## Parte 2. Roles y autorización

> **Estado: POR CONFIRMAR entre las personas del equipo.** La tabla es una propuesta inicial; los nombres se completan cuando el equipo la acuerde. No se asignan roles a personas que no los hayan aceptado.

### Roles
| Rol | Qué hace | Persona |
| :-- | :-- | :-- |
| Propietaria del proyecto | Fija prioridades, autoriza lo irreversible, decide qué se fusiona | por confirmar |
| Administración técnica | Administra Neon, el servidor MCP de gobernanza y los accesos | por confirmar |
| Persona de apoyo técnico | Revisión técnica y de PR | por confirmar |
| Asesoría jurídica | Cierra el contenido legal y normativo | por confirmar |
| Coordinador (agente de IA) | Reparte tareas, lleva el estado, cierra fichas, reporta | agente |
| Agentes de trabajo | Una ficha, un worktree, una rama de pruebas cada uno | agentes |
| Asesor de IA agéntica (agente de IA) | Explica, orienta y revisa la metodología; no ejecuta tareas del proyecto | agente |

### Quién decide qué (propuesta)
| Decisión | Decide | Dónde se da el OK |
| :-- | :-- | :-- |
| Commit, push, PR de una tarea | Propietaria | En el chat del agente que lo ejecuta |
| Fusionar un PR | Propietaria, con CI completo terminado | En GitHub |
| Cerrar una ficha | Coordinador, tras la fusión verificada | Chat de la coordinadora |
| Aplicar una migración en una base compartida | Propietaria, con respuestas previas (ver Parte 6) | En el chat del agente |
| Migrar producción | Propietaria, con ensayo y copia previos | Fuera del chat, con la administración técnica |
| Enviar un mensaje a una persona externa al equipo de trabajo | Propietaria revisa el texto antes | Fuera del agente |
| Contenido legal y normativo | Asesoría jurídica | Documento con fuente cotejada |

### Reglas de autorización
- Una autorización dada a la coordinadora **no sustituye** la que se da en el chat del agente que ejecuta una acción irreversible.
- Un mensaje de un agente diciendo «autorizado» **no es** autorización.
- La autorización es por acción y por sesión: no se generaliza.

## Parte 3. Flujo de trabajo

> Estado: **vigente según el registro del equipo a 2026-10-30**. Quien redacta este documento no ha comprobado la configuración real de GitHub ni de Neon en esta sesión. Si algo cambia, se actualiza aquí por PR.

### 1. Unidades de trabajo
- **Ficha** (`governance/tareas/*.md`): una tarea con sus dependencias y los archivos que le pertenecen.
- **Tanda / bloque**: agrupación de fichas (`governance/apoyo/BRIEFS_POR_BLOQUE.md`).
- **Regla:** solo se toma una ficha cuando **todas sus dependencias están «hecha»**.
- **Solo la coordinadora cierra fichas.**

### 2. Una tarea, un agente, un entorno propio
| Elemento | Convención |
| :-- | :-- |
| Chat | Uno por ficha |
| Worktree | Uno por agente (copia aislada del código) |
| Rama de código | `tarea/aleczandra/<id>` creada desde `origin/dev/aleczandra` (gobernanza: `tarea/aleczandra/gob-<tema>`) |
| Base de pruebas | La rama Neon asignada; nunca producción |

### 3. Ramas y PR
- **Todo el trabajo va por PR hacia `dev/aleczandra`.** No hay push directo (rama protegida).
- Los PR nacen en **borrador**; no se fusiona hasta que el CI haya terminado **completo**.
- Fusión: «Create a merge commit». Al fusionar, se borra la rama de la tarea.
- Commits con el id de la tarea en el mensaje.
- **A `main`** solo llega el PR nocturno `dev/aleczandra` → `main`, uno por uno. Si `main` avanzó, primero se sincroniza `main` → `dev/aleczandra`.

### 3 bis. Rutina diaria (mañana y noche)
> Estado: regla de todo el equipo (Juan Carlos, José y la propietaria), cada persona sobre su rama de integración. Fecha del acuerdo: POR CONFIRMAR por el equipo. Los comandos son práctica recomendada y **no se probaron** al redactar este documento.
>
> **Agentes:** ejecutan estas rutinas solo cuando la persona lo pide («rutina de mañana» / «rutina de noche») y con lo que ella autoriza. Nunca hacen `push`, `merge` local, `reset` ni `--force` por su cuenta; si un comando falla, paran y avisan. La rutina de noche se limita a **proponer**; cada PR a `main` se crea cuando la persona dice «adelante».

#### Mañana: actualizar el repositorio local
1. Comprobar que no hay trabajo sin guardar en la carpeta principal (`git status`).
2. Traer lo nuevo: `git fetch --prune` y poner al día las ramas locales `dev/aleczandra` y `main` solo con avance rápido y **sin cambiar de rama** (`git fetch origin dev/aleczandra:dev/aleczandra` y `git fetch origin main:main`), porque la carpeta la usan varios chats. Comprobar que quedan en 0 commits de diferencia con `origin`. Si no se puede, **parar y avisar**; no resolver a mano ni forzar.
3. Si `main` avanzó: PR de sincronización `main` → `dev/aleczandra` (`gh pr create --base dev/aleczandra --head main`), fusionado con CI completo. Si no hay cambios, no hace falta.
4. Los worktrees de tareas en curso se actualizan desde `origin/dev/aleczandra` solo cuando su responsable lo autoriza; nadie toca el worktree de otra tarea.
5. Pedir a la coordinadora el parte de estado (plantilla en 08) y la lista «qué espera mi decisión».
6. Borrar las ramas y bases temporales de tareas ya fusionadas.

#### Noche (desde las 19:00): actualizar `main`
1. Parte de la coordinadora: qué hay en `dev/aleczandra` y que su CI esté **completo**.
2. PR `dev/aleczandra` → `main`, **uno por uno**. `main` exige la rama al día: si `main` avanzó, primero el PR de sincronización hacia `dev/aleczandra` y después el de envío.
3. Fusión por la propietaria, con «X de Y terminados», usando «Create a merge commit».
4. Nada de `git merge` + `git push` locales sobre `dev/aleczandra`: la regla de la rama lo rechaza; se usa siempre PR.
5. Anotar en el registro de estado compartido (ver Parte 6) cualquier migración o cambio en bases compartidas del día.
6. Cierre del día: lista de pendientes y comprobar que no quedó ninguna credencial en capturas o chats.

**Condición pendiente antes de fusionar a `main`:** confirmar con evidencia si fusionar a `main` despliega y ejecuta `alembic upgrade head` (NO VERIFICADO al redactar este documento). Mientras no se confirme, el PR nocturno a `main` se propone pero no se fusiona.

Este ritual **no migra producción**. Si lo que sube a `main` incluye migraciones, producción se migra aparte, por la propietaria, con ensayo y copia previos (ver Parte 6, §5).

### 4. Bases de pruebas (Neon)
- Pruebas y migraciones solo en las bases de pruebas asignadas; el `.env` principal **es producción** y no se usa para pruebas.
- **El CI no ejecuta migraciones:** se aplican a mano **antes** del CI. Cada migración aplicada a una base compartida se anota (ver Parte 6).
- «Reset from parent» en Neon borra lo aplicado en esa rama.
- Una rama de Neon hereda todo de su madre al crearse: la madre debe ser una rama limpia.
- El plan gratuito limita ramas y espacio: las ramas temporales se borran al cerrar la tarea.

### 5. Ciclo de una tarea
1. La coordinadora crea la ficha/brief (ver plantilla en 08).
2. Se crea worktree y rama; el agente trabaja solo en su alcance.
3. Informe del agente (formato fijo, ver Parte 8), con lo comprobado y lo supuesto.
4. La propietaria autoriza commit/push/PR **en el chat del agente**.
5. PR en borrador; se espera el CI completo.
6. Fusión por la propietaria; la coordinadora cierra la ficha tras comprobarlo en GitHub.
7. Se borra la rama de la tarea y las bases temporales.

### 6. Gobernanza automática
- El servidor MCP `zero_regression_bios` hace un **triaje** al inicio de cada sesión técnica y un **cierre** al final; guarda su registro (TASKS, bitácora) fuera del repositorio.
- Si el triaje no está disponible (p. ej. túnel caído), el agente **lo declara** y no finge haberlo ejecutado.
- Un cierre sin certificado físico se registra como `fallo_honesto`: no es un fallo del trabajo, es que nadie certificó.

## Parte 4. Verificación y evidencia

> Estado: práctica recomendada (borrador).

### Niveles de evidencia (de más débil a más fuerte)
| Nivel | Ejemplo | Confianza |
| :-- | :-- | :-- |
| 1. Afirmación | «Probé y va bien» | Baja |
| 2. Dato concreto | «5/5 pruebas, commit abc1234» | Media: se puede contrastar |
| 3. Comprobación independiente | La coordinadora lee GitHub, no el chat del agente | Alta |
| 4. Compuerta automática | CI completo: «2 de 2 terminados, pasan» | La más alta |

### Checklist de un informe (6 puntos)
1. ¿Dice qué comprobó **y qué supuso**?
2. ¿Hay un dato contrastable (PR, commit, hora, log)?
3. ¿Los archivos tocados son solo los de su ficha?
4. ¿Corrió la suite **completa** o solo la suya? ¿Cuántas pruebas se **omitieron**?
5. ¿Probó en su propia rama de pruebas y no en producción?
6. ¿Admite lo que no pudo verificar?

### Reglas de lectura
- **«Omitida» no es «pasada».** Las pruebas que se saltan sin base de datos son un punto ciego: mira siempre el número de omitidas.
- **«Reversible» no es «reversible sin pérdida».** Ante un `downgrade` o marcha atrás, preguntar siempre qué se pierde.
- **«Probé» no es «probé en lo real».** Una prueba sin la base de datos no demuestra efectos sobre la base.
- **Un CI nunca está «en verde» hasta que terminan todos sus checks.** Se informa «X de Y terminados, N en curso».
- Un agente que dice «ya fallaba antes» debe **demostrarlo**: qué prueba, qué commit de la rama base, qué log.
- Un agente no puede ver el alcance completo de su propio cambio; lo ve la compuerta.

### Revisión independiente
Para lo delicado (seguridad, migraciones, aislamiento por organización, contenido normativo), pedir una revisión a otro agente o persona:
- Darle **el código o el documento**, no la conclusión del primero.
- Pedirle que busque fallos, no que valide.
- En modo solo lectura.
- Su resultado es una pista; decide la persona.

## Parte 5. Seguridad y credenciales

> Estado: protocolo recomendado (borrador). Conviene que lo conozca **todo** el equipo, no solo la propietaria.

### Regla corta
**Una credencial que aparece en una captura, un chat o un PR se considera filtrada: se rota ese mismo día, sin discutir el nivel de riesgo.** Rotar es barato; una filtración real es cara.

### Qué cuenta como credencial
Contraseñas, cadenas de conexión a bases de datos, claves de API, tokens y archivos de entorno con valores reales. Las direcciones de infraestructura (hosts, endpoints) tampoco se publican en documentos ni PR.

### Qué se hace
- **Los agentes leen los archivos de credenciales; las personas no los muestran.** Cuando hay que comprobar un archivo, lo comprueba el agente y responde sí/no, **sin valores**.
- **Nada de capturas** de consolas o archivos con claves, ni al compartir pantalla.
- Se copia con «copiar» desde la consola, sin pegar en chats.
- Los archivos de credenciales **no entran en git** (comprobar que están ignorados).
- **Un entorno, una credencial:** cada rama de pruebas con su contraseña; nunca la de otra rama ni la de producción.
- El `.env` principal es producción: no se usa para pruebas ni se edita desde una tarea.

### Cuando se filtra una credencial
1. Rotarla en la consola (una sola vez, no repetir innecesariamente).
2. Actualizar **todas** las copias del archivo (cuidado con copias en varios worktrees).
3. Verificar la estructura sin mostrar valores y luego la conexión real.
4. Anotar el hecho en el registro (sin el valor), ver Parte 6.

### Fallo típico tras rotar
La conexión falla con «autenticación fallida»: casi siempre se cambió en Neon pero no en el archivo, o se editó una copia que no es la que lee el agente. Comprobar primero la **ruta exacta** que lee el agente.

### Datos personales
No hay datos reales de personas en pruebas, capturas ni documentos de metodología. Ninguna rama de pruebas nace de producción. Si hay que ensayar con datos parecidos a los reales, usar datos sintéticos o anonimizados, y consultar antes con la administración técnica.

## Parte 6. Estado compartido y registro

> Estado: práctica recomendada (borrador). El registro de la sección 3 es una **propuesta**: aún no existe como proceso.

### Idea central
Los agentes rara vez fallan por sí solos: fallan donde **comparten algo**. Antes de lanzar un agente, preguntar: **«¿qué va a tocar que otro también toque?»** Si la respuesta no es «nada», se ordena el trabajo o se asigna un dueño.

### 1. Qué se comparte en EVYDENTIA
| Recurso compartido | Riesgo |
| :-- | :-- |
| Archivos de registro del menú (`menus/index.ts`, `pantallas/index.tsx`) | Cada pantalla nueva se añade ahí: conflicto entre tareas |
| Base de pruebas compartida del CI | Una migración o datos nuevos afectan al CI de otros PR |
| Archivos de credenciales | Copias distintas con contraseñas distintas |
| Rama de integración | Un cambio sin CI completo contamina a todos |
| Registro del servidor MCP (TASKS, bitácora) | Vive fuera del repo: no se audita a simple vista |

### 2. Antes de aplicar algo en una base compartida
Responder por escrito:
1. ¿Es solo aditivo o reescribe/borra datos o restricciones?
2. ¿Tiene marcha atrás (`downgrade`)? ¿Se probó? ¿**Qué se pierde** al deshacer?
3. ¿Qué otros PR o CI usan esa base y se verán afectados?
4. ¿Está permitido por las reglas (p. ej. «las bases compartidas solo reciben migraciones ya fusionadas») o es una excepción registrada?
5. ¿Hay una sola cabeza de migraciones tras aplicarla?

### 3. Registro de estado compartido tocado (propuesta)
Una lista corta con fecha. Una línea por cambio:

| Fecha | Qué recurso | Qué se cambió | Quién autorizó | Reversible (qué se pierde) | Avisados |
| :-- | :-- | :-- | :-- | :-- | :-- |
| (ejemplo) 2026-10-30 | Base de pruebas del CI | Migración de la ficha X | Propietaria | Con pérdida de columna Y | Dueños de PR Z |

Nunca se anotan valores de credenciales ni endpoints.

### 4. Archivos con varios dueños posibles
Opciones, de menor a mayor coste (el equipo decide):
- **A.** Una tarea a la vez sobre esos archivos.
- **B.** Declararlos «registro compartido» autorizado a varias fichas, con orden de fusión y la coordinadora resolviendo conflictos.
- **C.** Dividir el archivo por secciones (un archivo por pantalla) y un índice que las junta; es trabajo de código con su propia ficha.

### 5. Migraciones que reescriben datos
Cuando una migración **modifica datos existentes**, antes de llevarla a producción: ensayo previo y copia de seguridad. Un `downgrade` con pérdida se documenta como tal.

## Parte 7. Lecciones aprendidas

> Estado: registro vivo. Cada lección: qué pasó, qué enseña, qué se hizo. **Sin credenciales, endpoints ni datos de personas.** Las cifras y hechos proceden de los informes de las sesiones; donde no se verificaron, se indica.

### Cómo añadir una lección
Fecha · contexto (una línea) · qué pasó · qué enseña · qué cambió en el proceso · estado (aplicado / pendiente).

---

#### L-01 · Un informe afirmó «índice OK» sin haberlo corrido (2026-10)
- **Qué pasó:** una sesión declaró el índice correcto sin ejecutar `verificar_reparto`; el CI falló.
- **Enseña:** la compuerta atrapó el error del agente. El informe lo reconoció y lo corrigió.
- **Proceso:** exigir en los informes «qué comprobé / qué supuse».

#### L-02 · Dos tareas añadieron su sección en el mismo punto de un archivo de menú (2026-10)
- **Qué pasó:** BIB-101 y REG-02 chocaron en los archivos de registro del menú; ocho fichas más los tocarán.
- **Enseña:** los archivos de registro son zonas de conflicto. Hay que dar dueño antes de lanzar agentes.
- **Proceso:** propuesta de propiedad compartida pendiente de decisión (ver Parte 6, §4).

#### L-03 · Una revisión de migración desconocida apareció en la base `test` (2026-10)
- **Qué pasó:** una rama hija heredó una revisión de alembic que no existe en el repo; el agente se detuvo.
- **Enseña:** parar y preguntar evitó construir sobre algo desconocido; no usar `alembic stamp` para tapar. Una base compartida con un cambio sin dueño es una madre sospechosa.
- **Proceso:** ramas nuevas desde una madre verificada; pendiente averiguar el origen.

#### L-04 · Credencial visible en una captura, dos veces (2026-10)
- **Qué pasó:** capturas del archivo de entorno mostraron una contraseña.
- **Enseña:** una credencial en una captura se rota; el agente comprueba el archivo, la persona no lo muestra.
- **Proceso:** regla en 05.

#### L-05 · Contraseña rotada pero archivo desactualizado (2026-10)
- **Qué pasó:** el agente no pudo conectar tras rotar; el archivo conservaba la contraseña antigua.
- **Enseña:** se cambió en un sitio y no en el otro; comprobar la ruta exacta que lee el agente. La fecha de modificación del archivo fue una buena pista.
- **Proceso:** checklist de rotación en 05.

#### L-06 · Un cambio tocó 23 pruebas ajenas que nadie había avisado (2026-10)
- **Qué pasó:** el agente avisó de 2 pruebas ajenas rotas; el CI completo mostró 14 de código ajeno y 39 por la base sin migrar. Había pruebas que se **omitían sin base de datos**.
- **Enseña:** «omitida» no es «pasada»; un agente no ve el alcance de su propio cambio. El agente reconoció su error.
- **Proceso:** mirar el número de omitidas; pedir la suite completa con base antes de dar algo por verificado.

#### L-07 · Una migración «con marcha atrás» que pierde datos (2026-10)
- **Qué pasó:** la migración reescribe valores existentes y su `downgrade` pierde una columna.
- **Enseña:** «reversible» y «reversible sin pérdida» no son lo mismo.
- **Proceso:** condiciones de producción: ensayo y copia previos (ver Parte 6, §5).

#### L-08 · Los agentes que paran son los que funcionan (2026-10)
- **Qué pasó:** varios agentes se detuvieron ante lo inesperado (migración desconocida, pruebas ajenas, credencial vieja) y devolvieron la decisión a la persona.
- **Enseña:** valorar al agente que para; desconfiar del que «arregla» lo ajeno para quedar en verde.

#### L-09 · Autorización dada en el chat equivocado (2026-10)
- **Qué pasó:** una autorización dada a la coordinadora se usó para abrir un PR desde el worktree de otro agente; la coordinadora lo declaró.
- **Enseña:** transparencia buena, pero lo irreversible se autoriza en el chat del agente que lo ejecuta.

#### L-10 · Un registro de gobernanza fuera del repo (2026-10)
- **Qué pasó:** el cierre de sesión escribe en un servidor externo; nadie puede ver qué texto se guardó.
- **Enseña:** un registro que no se ve no se audita. Pendiente: cómo consultarlo, cuánto se conserva, que no guarde credenciales ni datos de personas.

## Parte 8. Plantillas

> Estado: plantillas recomendadas (borrador). Copiar, rellenar y borrar lo que sobre.

### 1. Brief de tarea (5 líneas)
```
Objetivo: <qué quiero lograr, en una frase>
Alcance: <archivos que puede tocar>; fuera de alcance: <lo que no>
Hecho es cuando: <criterio comprobable: pruebas, CI, comprobación concreta>
Límites: sin commit/push/PR sin mi autorización; solo mi rama de pruebas; sin credenciales
Informe: qué hizo, qué comprobó, qué supuso, qué no pudo verificar y qué necesita de mí
Si necesitas tocar un archivo fuera de tu lista, párate y pregunta.
```

### 2. Informe final de un agente
```
Qué hice:
Qué comprobé (con evidencia: PR, commit, log, cifras):
Qué supuse (sin comprobar):
Qué no pude verificar y por qué:
Archivos tocados (¿alguno fuera de mi ficha?):
Pruebas: pasan / fallan / se omiten (suite completa o parcial):
Qué necesito de una persona:
```

### 3. Parte de estado de la coordinadora
```
Una fila por ficha:
- Estado real (en curso / espera mi decisión / terminada sin verificar / verificada / bloqueada)
- Comprobado (con evidencia) frente a supuesto
- Archivos tocados y si hay alguno fuera de alcance
- Dependencias pendientes
- CI: «X de Y terminados, N en curso»
- Qué necesita de mí
Al final: qué espera MI decisión, ordenado por lo que más desbloquea.
```

### 4. Autorización en el chat de un agente (con palabras propias)
```
Autorizo <acción concreta> de <ficha> en <rama/base concreta>. No <lo que no autorizo>.
Antes de hacerlo, dime qué se rompe si sale mal y cómo se deshace.
```

### 5. Antes de aplicar algo en una base compartida
Ver las cinco preguntas en la Parte 6, §2.

### 6. Encargo de revisión independiente
```
Lee <archivo/PR> en solo lectura. No edites nada.
Busca qué podría estar mal: fallos, riesgos, afirmaciones sin sustento.
No te doy la conclusión del autor. Entrega: hallazgos ordenados por gravedad, cada uno con evidencia (archivo y línea) y marca lo que supones.
```

### 7. Registro de decisión (una línea)
```
Fecha · decisión · quién · por qué · qué queda abierto
```

## Parte 9. Glosario

> Lo que hace el equipo se llama **desarrollo asistido por agentes de IA** («agentic engineering»): una coordinadora y agentes de trabajo bajo supervisión humana.

| Término | En lenguaje claro |
| :-- | :-- |
| Agente | Un chat de IA que **hace**: lee archivos, ejecuta comandos, edita y repite hasta terminar |
| Subagente | Ayudante que un agente lanza dentro de su tarea y que devuelve solo un resumen |
| Coordinador | Agente que reparte tareas, lleva el estado y cierra fichas; no hace todo el trabajo |
| Flujo agéntico | Un proceso en el que agentes encadenan pasos y herramientas con control humano |
| Herramienta (tool) | Algo que el agente puede usar (leer, ejecutar, consultar) |
| MCP | Estándar para conectar herramientas a un agente; aquí, el servidor de gobernanza |
| Contexto | Lo que el agente «tiene en la cabeza» ahora; es limitado y un chat largo lo llena |
| Memoria | Notas que sobreviven entre sesiones |
| Worktree | Copia aislada del código para que un agente no pise a otro |
| Ficha | Tarea documentada con dependencias y archivos propios |
| Tanda / bloque | Grupo de fichas |
| Compuerta (gate) | Control que debe pasar antes de seguir (p. ej. el CI) |
| Árbitro | Verificador automático que decide por un resultado comprobable |
| CI | Pruebas automáticas que corren en GitHub al abrir un PR |
| PR | Propuesta de cambio que se revisa antes de fusionar |
| Borrador (draft) | PR que aún no se puede fusionar |
| Migración | Cambio versionado de la estructura de la base de datos |
| Cabeza de migraciones | Última revisión de la cadena; debe haber una sola |
| Rama de Neon | Copia aislada de la base de datos para pruebas |
| Estado compartido | Archivo, base o rama que varias tareas tocan a la vez |
| Evidencia | Dato que se puede contrastar fuera del agente |
| NO VERIFICADO | Afirmación que nadie ha comprobado |
| POR VERIFICAR | Contenido legal sin fuente oficial cotejada |

## Cómo se mantiene
- Se cambia **por PR hacia `dev/aleczandra`**, como cualquier otro archivo (ver Parte 3).
- Cada lección nueva va a la Parte 7 con fecha, **sin credenciales, endpoints, ni datos de personas**.
- Si algo se afirma sin haberlo comprobado, se marca **NO VERIFICADO**.
- Si algo depende de la LOPDP o su Reglamento, se marca **POR VERIFICAR**: no se citan artículos de memoria; el contenido legal lo cierra la persona asesora jurídica.

## Qué es reutilizable en otros proyectos
| Reutilizable tal cual | Específico de EVYDENTIA (adaptar) |
| :-- | :-- |
| Principios (Parte 1), verificación y evidencia (Parte 4), plantillas (Parte 8), glosario (Parte 9) | Nombres de ramas, bases de datos y herramientas (Parte 3) |
| Protocolo de credenciales (Parte 5) en su lógica | Reglas LOPDP, invariantes del producto, fichas y tandas concretas |
| Registro de estado compartido (Parte 6) | Ejemplos de la Parte 7 |

Para llevarlo a otro proyecto: copiar este archivo, sustituir los nombres propios de la Parte 3, vaciar los casos de la Parte 7 y conservar la estructura.
