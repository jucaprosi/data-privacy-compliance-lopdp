# Parte del CTO: PRD de EVYDENTIA como única fuente, 2026-11-12

Parte de relevo del chat del CTO (2026-11-08 a 2026-11-12). Tema principal: EVYDENTIA queda como único nombre y su PRD como única fuente de verdad. Otros temas del chat: fusiones de las tandas 27 y de fichas libres, brief de Google Cloud para Antigravity, secreto `INVENTARIO_CLAVE_CIFRADO`, consolidación del PMV y carpeta de partes por rol.

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
- Partes: una carpeta por rol en `governance/partes/`, escritos primero en la máquina del propietario y empujados juntos en un PR diario.
- Propuestas por convertir en fichas: derivar `SOLO_DESARROLLO` de una marca en el spec; reducir conflictos en índices; árbitro de fusión simulada con PR abiertos que traen migración.

## Lo que falta
- Tech Lead: tanda para RM-25a (tras MARCA-01) y próxima tanda de fichas libres.
- Fichas por lanzar: MARCA-01 a 06, PRD-01 a 03, DEMO-05c/05d, ORG-22a/22b, RM-25b/25c, DIAG-07b, ficha de `dpo_nombre` e `implementador_nombre`, contracción de EVI-01, REP-01 y el generador del manifiesto E2E.
- En curso sin PR de código: EVI-02, DEMO-01, FE-25, SEC-21 y DIAG-07a.
- Partes del Tech Lead, el Arquitecto y UX/UI en sus carpetas.

## Lo que no se toca
- Producción: ninguna sesión de IA actúa en Google Cloud ni contra la base de producción; todo va por brief que ejecuta el propietario.
- `.github/workflows/`, `verificadores/`, `AGENTS.md` y `.claude/`: del propietario.
- `main` solo recibe EVYDENTIA. `AUTH_MODE=headers` nunca.
- Sin secretos, claves ni URL de conexión en archivos ni en el chat.
- `BRIEFS_POR_BLOQUE.md` y `TASKS.md`: solo el Tech Lead.
- La inmutabilidad de la biblioteca y la RLS no se relajan.
- No dejar partes sueltos fuera de la carpeta de su rol.

## Pendientes del usuario
**Decidir o aportar**
- Preguntas al abogado: Vertex en us-central1, retención frente a supresión, días hábiles frente a corridos, el «Art. 62, diez días» de DER-07, nombre del DPO e implementador visible a los miembros (ESTIMADO), plazos antes del bloqueo WORM.
- Normativa oficial en `data/normativa_oficial/` (LEG-05 necesita el Reglamento General).
- Archivos pendientes del assessment.
- Rotar las credenciales de la base remota del PMV.

**Ejecutar solo él**
1. Google Cloud con Antigravity, un bloque por vez (brief `governance/operaciones/BRIEF_PROPIETARIO_GOOGLE_CLOUD_2026-11-11.md`): secreto `INVENTARIO_CLAVE_CIFRADO` antes de cualquier despliegue, bucket de evidencias, bucket de la demo con Job y Scheduler, SQL de purga, API de Vertex, balanceador al final, presupuesto de Cloud SQL en lectura.
2. `.github/workflows/`: workflow de EP-07 y opciones `--destino` y `--estricto-sin-ficha` de CI-23.
3. Administración de GitHub: reglas de `main` y `pmv/**`.
4. Lecturas de producción: solicitudes ARCO huérfanas, estructura de `terceros_encargados` y alertas de Cloud Logging con nombres de la marca anterior.
5. Su carpeta: `git checkout -- governance/partes/cto/2026-11-12_cto.md; git pull --ff-only`.
