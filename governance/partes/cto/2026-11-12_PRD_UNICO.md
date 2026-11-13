# Parte del CTO: PRD de EVYDENTIA como única fuente, 2026-11-12

Parte de relevo del chat del CTO (2026-11-08 a 2026-11-12). Tema principal: EVYDENTIA queda como único nombre y su PRD como única fuente de verdad. Otros temas del chat: fusiones de las tandas 27 y de fichas libres, brief de Google Cloud para Antigravity, secreto `INVENTARIO_CLAVE_CIFRADO`, consolidación del PMV y carpeta de partes por rol.

**Rol de quien escribe**
- Rol: CTO de EVYDENTIA, asignado por el propietario; una sesión nueva empieza leyendo este parte y esperando su mensaje.
- Lugar en la cadena: **CTO** → Arquitecto → UX/UI (si hay frontend) → Tech Lead → sesiones de ingeniería.
- Función:
  - decide producto y técnica (código, archivos, detalles de implementación);
  - envía cada ficha nueva al Arquitecto y, si toca frontend, a UX/UI;
  - simula, revisa y fusiona los PR, y abre el PR diario de partes;
  - escribe los briefs que ejecuta el propietario.
- Límites:
  - no actúa en Google Cloud ni contra producción: desde aquí solo `gcloud` de lectura;
  - no edita `.github/workflows/`, `verificadores/`, `AGENTS.md` ni `.claude/`, ni `BRIEFS_POR_BLOQUE.md` ni `TASKS.md`;
  - no pasa a listo un PR en borrador sin preguntar.
- Entregas y escalado:
  - las decisiones van al Tech Lead, y al Arquitecto si son de diseño;
  - lo de negocio, lo legal y lo que solo ejecuta el propietario va a «Pendientes del usuario»;
  - lo legal va al abogado y se marca ESTIMADO mientras no responda;
  - siempre en español.

Estado al corte: `main` en `063a1c30` (PR #640), una sola cabeza de Alembic (`20261123_der06a_tipos_solicitud`), sin PR abiertos conocidos. Fichas: 260 hechas, 12 en curso y 68 pendientes, de 340.

## Lo decidido
- Cadena de trabajo: el CTO decide producto, el Arquitecto diseña, UX/UI redacta, el Tech Lead escribe fichas y reparte, las sesiones implementan, y el CTO simula, revisa y fusiona. El propietario pega «Lanza la tanda: …» en el chat del Tech Lead.
- Las fusiones las hace el CTO. Un PR en borrador no se pasa a listo sin preguntar.
- Las decisiones técnicas son del CTO; al propietario le tocan las de negocio, las legales, los datos y lo que solo él ejecuta.
- Un PR fusionado no recibe commits; la corrección va en un PR nuevo desde `main`.
- Toda fusión exige una sola cabeza de Alembic en la simulación sobre `main` (error de #611, arreglado en #616).
- EVYDENTIA es el único nombre; su PRD y sus artefactos son la única fuente (#603). El PRD anterior queda inhabilitado y se retira con MARCA-01 a 06 y PRD-01 a 03.
- Dimensiones = las 10 (D01 a D10); los 4 agrupadores son ejes.
- Evidencia con doble validación (coordinador y luego DPO o auditor, personas distintas); el implementador no valida.
- `INVENTARIO_CLAVE_CIFRADO`: la cédula opcional va cifrada con Fernet y falla cerrada (503) sin la clave (ORG-17). El workflow ya referencia el secreto (#619) y la guardia de claves distingue la referencia `:latest` de un valor (#621, Aporte 132).
- PMV consolidado en `pmv/consolidacion`; no entra a `main`. #624 cerrado sin fusionar.
- Reglas de GitHub: `main` con PR y comprobaciones, sin aprobación humana obligatoria; `pmv/**` con una aprobación.
- Partes: una carpeta por rol en `governance/partes/`, nombre por el tema más relevante, escritos primero en la máquina del propietario y empujados juntos en un PR diario.
- Propuestas por convertir en fichas: derivar `SOLO_DESARROLLO` de una marca en el spec; reducir conflictos en índices; árbitro de fusión simulada con PR abiertos que traen migración.

## Lo que falta
**Cómo fusiona el CTO (el script de simulación vivía en una carpeta temporal y se pierde)**
1. En un worktree limpio desde `origin/main`, fusionar la rama del PR sin commit.
2. Correr `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_reparto.py`: los dos con salida 0.
3. Contar las cabezas de Alembic: debe haber una sola.
4. Con el CI en verde: `gh pr merge N --merge --match-head-commit <sha>`. Si `main` se movió, cerrar y reabrir el PR para repetir el CI sobre la base nueva.
5. Un PR de gobernanza a la vez cuando tocan `BRIEFS_POR_BLOQUE.md` o `TASKS.md`; chocan casi siempre en las filas de tandas.

**Tech Lead**
- Tanda para RM-25a **después** de MARCA-01: las dos poseen `main.py`.
- Próxima tanda de fichas libres (máximo 4 bloques por tanda).
- Toda ficha nueva pasa antes por el Arquitecto; si toca frontend, también por UX/UI.

**Fichas por lanzar, con lo que hay que recordar**
- MARCA-01 a 06 y PRD-01 a 03 (retiro del PRD anterior): no romper los árbitros que leen el PRD; el criterio 3 del §7 del PRD de EVYDENTIA se prueba en `tests/test_matriz_permisos.py`. No renombrar claves de almacenamiento del navegador ni nombres de registro de la marca anterior sin medir antes, y sin la lectura de Cloud Logging del propietario.
- DEMO-05c y DEMO-05d (purga de la demo): la función `SECURITY DEFINER` vive solo en la base de la demo, la crea el brief del propietario y **nunca** Alembic; una prueba debe garantizar que ninguna migración la define. Políticas estrechas por rol, operación y condición, y `SELECT` por columnas en `demo_sesiones`. El Arquitecto detectó que los triggers de inmutabilidad bloqueaban la purga: el diseño debe resolverlo sin relajarlos.
- ORG-22a y ORG-22b (rol `auditor`): el auditor no acumula ningún otro rol en el tenant (ESTIMADO frente al PRD, que solo lo dice por tarea).
- RM-25b y RM-25c (doble validación): primera del coordinador, final del DPO o del auditor, personas distintas. Una tarea validada sube el nivel de evidencia (0 a 4), nunca la madurez.
- DIAG-07b (DIAG-07a sigue en curso): el PR final necesita el candado advisory del sello y su prueba de concurrencia.
- Ficha de organización con `dpo_nombre` e `implementador_nombre`: cualquier miembro ve solo el nombre (ESTIMADO, pregunta al abogado); va con FE-25.
- Contracción de EVI-01: su criterio de «hecho» se prueba contra la base de pruebas de EVYDENTIA (local PG16 del arnés o `evydentia-pruebas`), no contra el proveedor retirado.
- REP-01: el criterio de «hecho» se copiaba a mano en 28 bloques; debe derivarse y compararse con una prueba.
- Generador del manifiesto E2E: debe vivir en el repositorio bajo su ficha y emitir `base_pruebas`, sin alias transitorio ni entrada en la lista de permitidos (el árbitro del Arquitecto rechazó esa salida).

**Reglas para cualquier ficha**
- Con migración: aplicar `governance/operaciones/FUSION_ALEMBIC.md`; las migraciones entran de una en una.
- Si un spec de Playwright usa `fijarAjustes`, la ficha debe poseer `frontend/playwright.config.ts` y añadir el spec a `SOLO_DESARROLLO`; falló cuatro veces (ORG-17, ORG-18, ORG-15 y BIB-110).
- Las pruebas no importan `yaml`: usan `tests/_lector_yaml.py`.
- Un archivo nuevo de gobernanza con el nombre del proveedor retirado pone en rojo su guardia.
- Propiedad con archivos concretos, sin comodines sobre carpetas ajenas.

**En curso sin PR de código:** EVI-02, DEMO-01, FE-25, SEC-21 y DIAG-07a. SEC-21: `PROXIES_CONFIABLES` es obligatoria en la nube; vale 1 hoy y probablemente 2 detrás del balanceador, pendiente de la evidencia de `X-Forwarded-For`.

**Partes de los otros roles:** el Tech Lead, el Arquitecto y UX/UI escriben el suyo en su carpeta.

## Lo que no se toca
- Producción: ninguna sesión de IA actúa en Google Cloud ni contra la base de producción; todo va por brief que ejecuta el propietario. Desde aquí solo `gcloud` de lectura.
- `.github/workflows/`, `verificadores/`, `AGENTS.md` y `.claude/`: del propietario.
- `main` solo recibe EVYDENTIA. `AUTH_MODE=headers` nunca. No usar el `.env` de la carpeta principal: apunta a producción.
- Sin secretos, claves ni URL de conexión en archivos ni en el chat.
- `BRIEFS_POR_BLOQUE.md` y `TASKS.md`: solo el Tech Lead.
- La inmutabilidad de la biblioteca y la RLS no se relajan.
- No dejar partes sueltos fuera de la carpeta de su rol.

## Pendientes del usuario
**Decidir o aportar**
- Preguntas al abogado: Vertex en us-central1, retención frente a supresión, días hábiles frente a corridos, el «Art. 62, diez días» de DER-07, nombre del DPO e implementador visible a los miembros (ESTIMADO), plazos antes del bloqueo WORM.
- Normativa oficial en `data/normativa_oficial/` (LEG-05 necesita el Reglamento General).
- Archivos pendientes del assessment.
- Rotar las credenciales de la base remota del PMV, que la persona que lo trabaja tiene en texto plano.

**Ejecutar solo él**
1. Google Cloud con Antigravity, un bloque por vez (brief `governance/operaciones/BRIEF_PROPIETARIO_GOOGLE_CLOUD_2026-11-11.md`), pegando al CTO una línea por bloque:
   - secreto `INVENTARIO_CLAVE_CIFRADO` (Bloque 2, `BRIEF_PROPIETARIO_SECRETO_INVENTARIO.md`) **antes de cualquier despliegue**, porque el workflow ya lo referencia; guardar la clave en lugar seguro;
   - bucket de evidencias (Bloque 3): comprobar si fijar la retención exige `storage.objects.update`; sin bloqueo WORM hasta que el abogado confirme plazos;
   - bucket de la demo, Job de purga y Scheduler (Bloque 4); el SQL de la purga cuando llegue DEMO-05c;
   - API de Vertex y su rol mínimo (Bloque 5), condición de la «Evidencia de humo» de IA-03;
   - balanceador (Bloque 6, `BRIEF_PROPIETARIO_BALANCEADOR.md`) al final; cerrar el ingress del backend solo cuando `https://app.evydentia.com/api/v1/entorno` responda por él, y pasar al CTO cuántas direcciones trae `X-Forwarded-For`;
   - presupuesto de conexiones de Cloud SQL en solo lectura (Bloque 0), para GCP-05.
2. `.github/workflows/`: workflow de EP-07 (`governance/apoyo/BRIEF_PROPIETARIO_EP07_WORKFLOW.md`) y, en CI-23, `--destino "${{ github.base_ref }}"` (sin él la exención de `pmv/**` nunca se aplica) y `--estricto-sin-ficha`.
3. Administración de GitHub: reglas de `main` y `pmv/**` como en «Lo decidido».
4. Lecturas de producción: solicitudes ARCO huérfanas y estructura de `terceros_encargados` (antes de migrar DER-03 y ADPA-08), y alertas de Cloud Logging que dependan de nombres de registro de la marca anterior (antes de MARCA-01).
5. Su carpeta, tras fusionar el PR de este parte: borrar la copia local del parte y `git checkout -- governance/partes/cto/2026-11-12_cto.md; git pull --ff-only`.
