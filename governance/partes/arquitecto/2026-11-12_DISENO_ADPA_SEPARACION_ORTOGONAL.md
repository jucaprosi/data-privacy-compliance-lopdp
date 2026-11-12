# Parte del Arquitecto ADPA: diseño y separación ortogonal de fichas de EVYDENTIA, 2026-11-12

Parte de relevo del chat del Arquitecto ADPA (2026-11-08 a 2026-11-12).
- **Tema principal:** cómo se diseña una ficha para que sea ortogonal (una sala, archivos concretos y árbitro exógeno) y cómo se valida antes de repartirla.
- **Otros temas del chat:**
  - IA en Vertex y buckets de evidencias y de la demo;
  - DIAG-07 en expandir y contraer;
  - nombre y PRD únicos, e invariantes heredados;
  - doble validación de evidencia (RM-25) y DIAG-12;
  - rol auditor (ORG-22);
  - presupuesto de conexiones (GCP-05);
  - entorno de pruebas (EP-04);
  - guardia de la clave de cifrado (ORG-17b);
  - ficha resumen (FE-25);
  - purga de la demo (DEMO-05c y DEMO-05d).

**Rol de quien escribe**
- **Rol:** Arquitecto de soluciones ADPA de EVYDENTIA, asignado por el propietario. Una sesión nueva empieza leyendo este parte y esperando el mensaje del CTO.
- **Lugar en la cadena:** CTO → **Arquitecto** → UX/UI (si hay frontend) → Tech Lead → sesiones de ingeniería.
- **Función:**
  - medir sobre `origin/main`, leyendo el código, cada decisión o duda de diseño que llega del CTO o del Tech Lead;
  - devolver un diseño ortogonal: sala dueña, archivos concretos, `crea`, `depende_de`, árbitro con su mutación y orden frente a las fichas vivas;
  - validar cada ficha nueva antes de repartirla, con el método de «Lo decidido»;
  - responder las dudas de diseño de las sesiones de ingeniería, a través del Tech Lead o con copia a él;
  - separar las tareas de forma ortogonal, teniendo en cuenta los procesos de todas las fichas.
- **Límites:**
  - solo lee y diseña: no edita fichas, scripts, workflows ni `governance/apoyo/BRIEFS_POR_BLOQUE.md`; no hace commits ni abre o fusiona PR;
  - solo ejecuta en copias o bases desechables, para comprobar una solución;
  - respeta la propiedad de las fichas en curso; ZERAG es de solo lectura;
  - en Google Cloud solo usa `gcloud` de lectura; los cambios van por brief del propietario, con comandos de PowerShell completos.
- **Entregas y escalado:**
  - cada diseño va al Tech Lead, con una línea al CTO;
  - lo que choca con el PRD o con los invariantes, o es una regla de producto, vuelve al CTO;
  - lo legal va al abogado y se marca ESTIMADO mientras no responda;
  - siempre en español.

**Estado al corte:**
- `main` en `d5490f65` (PR #641), con una sola cabeza de Alembic (`20261123_der06a_tipos_solicitud`).
- Fichas: 260 hechas, 12 en curso y 68 pendientes, de 340 (en `governance/tareas` hay 341 archivos `.md`: las 340 fichas y el `README.md`).
- Abierto: #642 (historial de los partes).
- Los diseños completos se quedaron en archivos de trabajo del chat, fuera del repositorio. Lo que vale está en las fichas o en los mensajes al Tech Lead.

## Lo decidido

**Método de validación ortogonal.** Antes de dar una ficha por «validada» se recorren siete bloques, siempre sobre `origin/main`:
1. **Propiedad contra el árbol:**
   - cada ruta existe o va en `crea`;
   - una sección `#ID` necesita su marca en `HEAD` o una ancestro que la siembre;
   - una ficha no se siembra a sí misma.
2. **Choques con fichas vivas:**
   - un archivo entero frente a una sección ajena es un choque;
   - se quitan las dependencias que no comparten archivos: compartir sala no es compartir archivo.
3. **Referencias:**
   - `git grep` en todo el árbol antes de borrar, mover o renombrar;
   - antes de cambiar un texto visible, buscar los specs que lo esperan.
4. **Migraciones:**
   - una sola cabeza de Alembic;
   - un valor nuevo en un tipo nativo o en un CHECK que la revisión anterior no conoce va en dos fichas: una que expande sin activar y otra que activa después.
5. **Árbitros:**
   - cada criterio lleva su prueba y su mutación;
   - las capturas o la aprobación humana son evidencia, no árbitro, y se declaran como compuerta humana.
6. **Seguridad y entornos:**
   - fallar cerrado;
   - sin respaldos implícitos de variables;
   - funciones de arranque sin E/S.
7. **ADPA y ley:**
   - una ficha, una sala;
   - entre salas solo compuertas `_service.py` y pasillos;
   - no se cita un artículo que no esté en `governance/apoyo/CITAS_LEGALES_VERIFICADAS.md`.

Toda solución de guardia o de SQL se ejecuta antes en una copia o en una base desechable. En DEMO-03, leerla sin correrla hizo fallar tres versiones.

**Diseños entregados, cada uno en su ficha**
- **Nombre y PRD únicos** (MARCA-01 a 06 y PRD-01 a 03, en #605):
  - Se renombran el texto visible y la documentación. Las claves de almacenamiento del navegador y los nombres de los loggers no se renombran sin migrar o sin medir antes Cloud Logging.
  - La historia no se toca.
  - `scripts/generar_indice_tareas.py` lee el catálogo de salas del §5.2 del PRD de EVYDENTIA.
- **Invariantes heredados** (PRD-02): los 32 pasan con el mismo ID, como equivalencia o con texto adaptado. No se retira ninguno. `PMV_DECLARED_EVIDENCE` queda transitorio. El CTO lo aprobó, junto con las contradicciones C1 a C6.
- **Doble validación de evidencia** (RM-25a, RM-25b y RM-25c, en #609):
  - columnas con quién validó y con qué rol, y `nivel_acreditado` de 0 a 4, que fija el DPO;
  - el implementador deja de validar;
  - lo aprobado con una sola validación no sube el nivel y se marca para revalidar;
  - la validación sube el nivel de evidencia, nunca la madurez.
- **DIAG-12:**
  - la consulta vive en la sala roadmap (`features/roadmap/services/tareas_validadas_engine.py`, compuerta y pasillo);
  - toma por control el máximo entre el nivel de evidencia del diagnóstico real y `nivel_acreditado`;
  - entra sumando 0 hasta RM-25b.
- **Rol auditor** (ORG-22a y ORG-22b):
  - se parte en dos fichas, porque la revisión anterior da 500 al leer un rol desconocido en `features/organizacion/services/roles_engine.py:95` y en `features/organizacion/services/invitaciones_personas_engine.py:49`;
  - el auditor no acumula ningún otro rol en el tenant. Lo decidió el CTO; es ESTIMADO frente al PRD, que solo lo dice por tarea.
- **GCP-05:**
  - el tamaño del pool se lee en una sección propia de `app_core/db/session.py`, con rango cerrado y fallo cerrado en la nube;
  - el límite de la base va en un contrato nuevo que crea la ficha, marcado como provisional hasta la lectura del propietario.
- **EP-04:**
  - el worker no llama de vuelta al backend;
  - Eventarc necesita `run.invoker` sobre el worker;
  - la anotación de IAP se confirma con `describe`;
  - no hay secreto OIDC: `GOOGLE_CLIENT_ID` es público.
- **ORG-17b:** la guardia de la clave de cifrado excluye la referencia de Secret Manager con lookahead y sigue detectando cualquier valor de 20 caracteres o más. Lo probé con 8 casos.
- **FE-25:**
  - para quien no es administrador, el DPO se oculta o se muestra «No disponible», nunca «Sin designar»;
  - el RUC, la naturaleza, `dpo_nombre`, `implementador_nombre` y los contadores van en una ficha nueva de organización;
  - que cualquier miembro vea el nombre del DPO es ESTIMADO.
- **DEMO-05c** (paso 5 de `governance/operaciones/BRIEF_PROPIETARIO_DEMO05.md`). El CTO aprobó:
  - políticas solo `TO purga_demo`, solo SELECT y DELETE, con el marcador `demo`, solo sobre tenants demo vencidos y nunca sobre la plantilla;
  - en `demo_sesiones`, SELECT por columnas (`id`, `tenant_id`, `estado`, `terminada_en`) y DELETE solo de las vencidas hace más de 90 días;
  - quitar el UPDATE de `jobs/purga_demo/purga.py:116-117`, porque las FK `ON DELETE SET NULL` bastan;
  - el SQL queda en el repositorio dentro de la ficha, con una guardia en el Job y una prueba de CI con PostgreSQL efímera.

  Lo probé en un PG16 desechable con tablas mínimas.
- **DEMO-05d.** El CTO aprobó:
  - una función `SECURITY DEFINER` que solo existe en la base de la demo; la crea el brief, nunca Alembic;
  - solo la ejecuta `purga_demo`, y exige el marcador `demo` y que el tenant no sea la plantilla;
  - apaga una lista cerrada de triggers de inmutabilidad dentro de la transacción y los rehabilita en ella.

  Quedaron descartados el GUC, el borrado lógico y recrear la base.
- **Diseños anteriores, ya en fichas o briefs:**
  - IA-01 a IA-09 y DEP-01: Vertex, `google-genai`, us-central1 y fallo cerrado;
  - DER-05, DER-06a y DER-06b: expandir y activar un ENUM nativo;
  - DEMO-05: bucket sin retención;
  - evidencias: retención por objeto, rol propio `evidenciasEscrituraUnica` y firma V4;
  - DIAG-07 partida en DIAG-07a, DIAG-07b y DIAG-07 (DIAG-07c fundida), con candado advisory del sello;
  - SEC-21: saltos de `X-Forwarded-For`;
  - CI-23, FE-29 y REP-01.

## Lo que falta
- **DEMO-05d:**
  - medir en la PG efímera si `biblioteca_versiones`, `biblioteca_revisiones` o el trigger AFTER `biblioteca_registrar_evento` también bloquean el borrado;
  - medir si esas tablas tienen FORCE RLS para su dueño.
  - Responsable: la sesión de la ficha. El Arquitecto revisa la lista cerrada resultante.
- **Política de purga sobre `users`:** la diseña el Arquitecto cuando DEMO-05b fije cómo se distinguen las personas ficticias.
- **Ficha nueva de organización** que amplía la fila de cartera para FE-25: la escribe el Tech Lead y la valida el Arquitecto.
- **Fichas que pasan antes por el Arquitecto:**
  - EVI-01c;
  - BIB-110b;
  - el generador del manifiesto E2E, que emite `base_pruebas` sin alias;
  - la subida del contrato de ORG-17 y ORG-18;
  - DIAG-15.
- **Material pendiente:**
  - el auxiliar de subida simulada de EVI-01b, cuando el Tech Lead dé el archivo o el PR;
  - los archivos del assessment (brief v3, zip y hoja), cuando los entregue el CTO.
- **Duda sin responder:** GCP-02, vía Tech Lead. La capa `app_core/cloud` carga `scripts/seleccionar_pruebas.py`. Se desbloquea cuando llegue el mensaje del Tech Lead.

## Lo que no se toca
- **La inmutabilidad de la biblioteca en producción y en pruebas:** ningún trigger de inmutabilidad cambia por la demo.
- **La RLS de los roles de la aplicación:** las políticas nuevas son solo `TO purga_demo`.
- **La función y las políticas de la demo nunca viajan por Alembic.** Si viajaran, llegarían a la cadena de producción.
- **`app_core/db/session.py`** fuera de las secciones de GCP-01 y GCP-05, y `fijar_contexto_rls`. Es el núcleo de la RLS.
- **ADPA:**
  - una sala no lee tablas ajenas: los datos llegan por la compuerta `_service.py` o por el pasillo de la sala dueña;
  - una regla de negocio común va en la compuerta, no en el router.
- **Producción y Google Cloud:** la IA solo lee; los cambios van por brief. ZERAG es de solo lectura.
- **Datos sensibles:** sin secretos, sin URL de conexión y sin citas legales sin verificar.

## Pendientes del usuario
1. **Ejecutar con Antigravity el SQL del paso 5 en la base de la demo** (`evydentia-demo`), después de fusionar DEMO-05c. Esa ficha deja el SQL en el repositorio y quita el UPDATE de `jobs/purga_demo/purga.py`; si se ejecuta antes, el Job falla por permiso. Luego pegar al Tech Lead la salida de las comprobaciones de solo lectura del final del SQL, sin la contraseña. Brief: `governance/operaciones/BRIEF_PROPIETARIO_DEMO05.md`, paso 5.
2. **Crear la función de DEMO-05d en la base de la demo** con el mismo brief, una vez fusionada esa ficha.
3. **Lecturas de solo lectura:**
   - `gcloud sql instances describe` de la instancia de producción, para el `max_connections` real de GCP-05;
   - `gcloud run services describe evydentia-web` en el proyecto de pruebas, para confirmar la anotación de IAP de EP-04;
   - `SELECT count(*) FROM pg_roles WHERE rolname = 'purga_demo'` en producción y en pruebas: debe dar 0;
   - métricas y alertas de Cloud Logging que filtren por los nombres de los loggers de la marca anterior, antes de MARCA-01.
4. **Preguntas al abogado:**
   - si cualquier miembro puede ver el nombre del DPO (FE-25, ESTIMADO);
   - la cita «CSIRT, Ley de Ciberseguridad 2026», retirada de `INCIDENT_TIMELOCK`;
   - los plazos de retención antes de activar el bloqueo WORM de las evidencias.
5. **Su carpeta**, tras fusionar el PR de partes: borrar la copia local de este archivo solo si es idéntica a la de `main`. Lo comprueba `git diff --quiet origin/main -- governance/partes/arquitecto/2026-11-12_DISENO_ADPA_SEPARACION_ORTOGONAL.md`, que debe salir con 0. Si difiere, va al PR siguiente.
