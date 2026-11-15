# Parte del Tech Lead: fichas de IA y aportes 135 a 156, 2026-11-12 (corte posterior)

Parte de relevo del chat del Tech Lead después de `2026-11-12_CHATS_POR_DOMINIO_Y_REPARTO.md` (ya en `main`, no se toca). Tema principal: fichas de IA (IA-10, IA-11, RM-26 y RM-27) y consolidación de los aportes inéditos de los sub chats. Otros temas del chat: tanda de diez fichas libres (SEC-22), ampliaciones de propiedad (GCP-05, DER-07, DEMO-05c, DEMO-05d, GCP-10), chats por dominio aprobados y archivados, y el Aporte 134. Sin secretos; fichas y PR por identificador. Si este parte y una ficha se contradicen, manda la ficha.

Estado al corte: `main` en `1d306f67` (PR #648). Fichas en `governance/tareas/`: 260 hechas, 63 pendientes y 22 en curso. Cabeza de Alembic: no se midió en este corte; la mide el CTO al fusionar. Abiertos míos: #643 (Aporte 134), #644 (ampliaciones de propiedad) y #649 (Aportes 135 a 156).

## Rol de quien escribe
- **Rol:** Tech Lead de EVYDENTIA, asignado por el propietario. Una sesión nueva empieza esperando «Lanza la tanda: …» del propietario o el aviso del CTO; antes lee este parte y el anterior.
- **Lugar en la cadena:** CTO → Arquitecto → UX/UI (si hay frontend) → **Tech Lead** → sesiones de ingeniería.
- **Función:** escribe fichas y bloques, reparte en tandas, asigna briefs a los chats de dominio y hace la primera revisión de cada PR de código.
- **Límites:** no fusiona PR (lo hace el CTO), no actúa en Google Cloud ni contra producción, no toca `.github/workflows/`, `verificadores/`, `AGENTS.md` ni `.claude/`, no usa el `.env` de la carpeta principal ni escribe código de producto; sus commits son de gobernanza, en una rama por tanda.
- **Entregas y escalado:** fichas y briefs a las sesiones, una línea de estado al CTO por cada PR de gobernanza, dudas de diseño al Arquitecto, lo legal al abogado del propietario (**ESTIMADO** mientras no responda). Todo en español.

## Lo decidido
- **Diez chats por dominio** aprobados por el propietario, con la excepción de abrir un segundo chat del dominio cuando haga falta; renombrados y con siete archivados. Mapa e ids en la memoria `regla-subchats-por-dominio-reutilizables`.
- **Tanda de diez libres** (#646, fusionado): ORG-22a, MARCA-01/02/03/05/06, PRD-01/02 y REP-01 a `en_curso`; ficha nueva SEC-22 (sin clave en el log del motor de inferencia, `depende_de ADPA-03`); IA-05 depende de SEC-22; bloques BL-271 a BL-279 y tandas 24 a 28.
- **Fichas de IA** (#647, fusionado): IA-10 (tabla `trazas_ia` con RLS FORCE y prompts versionados con huella), IA-11 (evaluación fija, la corre el propietario), RM-26 (cifras deterministas de la Hoja de Ruta) y RM-27 (revisión humana con cuatro ojos, pasa por UX/UI). Quedan en «Sin agente», sin bloque ni tanda. IA-05 e IA-06 ampliaron su propiedad y sus dependencias (la sección `# === IA-05 ===` de `ai_copilot_service.py` se sembró antes). IA-10 y RM-27 llevan migración: no van en la misma tanda.
- **Orden entre dueñas de un mismo archivo** (Aporte 134, #643): la dependencia que acepta R4 es la de la dueña con tanda hacia la que no la tiene; MARCA-01 antes de RM-25a.
- **Aportes 135 a 156** (#649): 22 aportes verificados contra el repositorio y diez fuentes nuevas; descartados en la Parte XXX. Los defectos de producto no son aportes: el RUC que no oculta el saneador (`app_core/dlp_sanitizer.py`) va a la ficha dueña del saneador.

## Lo que falta
- **Fusiones del CTO:** #643, #644 y #649 (fusionar #643 primero; #649 lo incluye). Al fusionar #644, avisar a `nube` para que siga con GCP-05.
- **Lanzamiento de la tanda** (el usuario pega «Lanza la tanda: …»): abrir cinco sesiones `marca-y-gobernanza` (MARCA-01, MARCA-06, PRD-01, PRD-02, REP-01) y asignar ORG-22a a `organizacion`, MARCA-02 a `diagnostico`, MARCA-03 a `derechos-y-cumplimiento`, MARCA-05 a `nube` y SEC-22 a `ia`.
- **Bloques por escribir:** IA-10 (espera IA-03), IA-11, RM-26 y RM-27 (una sola migración por tanda); tanda siguiente: CI-20, RM-25a (tras MARCA-01) y DEMO-03f (bloqueada).
- **Fichas por escribir, cada una por el Arquitecto:** ampliación de SEC-21 (contar entradas de `X-Forwarded-For`), GCP de `min-instances` y `timeoutSec`, organización (`dpo_nombre` e `implementador_nombre`), EVI-01c, BIB-110b, generador del manifiesto E2E emitiendo `base_pruebas`, subir el contrato como archivo, DIAG-15, DEMO-04b, y VTX-01 (modelo y versión del prompt). Cola del Arquitecto: cifras LLM sin validar y migración a la compuerta de Vertex.
- **Aportes pendientes:** faltan los informes de `evidencias-roadmap`, `demo` (llegó parcial) y el fork del Tech Lead; irían en un PR desde el Aporte 157. Quedan en espera los candidatos de DIAG-07 (candado de ausencia, cuando exista la prueba de concurrencia), SEC-21 y el presupuesto de conexiones de GCP-05. El Aporte 155 no tiene cita verificada y los 148 y 153 citan fuentes que no se releyeron.
- **Pendientes de la memoria** (`proyecto-pendientes-tech-lead-2026-11-12`): EP-05 (contradicción de OAuth, con el Arquitecto), ocultar «Clientes» en el backlog, refrescar el brief del bucket de evidencias, brief del secreto `INVENTARIO_CLAVE_CIFRADO`, DIAG-06 por dimensión y control, corrección de `cloud_load_balancer.yaml` y BRIEF_BALANCEADOR en el próximo PR de gobernanza.
- **Mensajes sin enviar:** FE-25 (opción (a); `plantillas-cuenta` es deuda de BIB-401; `cambio-organizacion` es de BIB-110), EVI-02 (renombrar su spec a `vigencia-activa.spec.ts`), DEMO-02 (no tocar `jobs/purga_demo`; la purga va por DEMO-05c y DEMO-05d), GCP-02 (pregunta al Arquitecto sobre capas), BIB-110b y avisar a Arquitecto y UX/UI del formato nuevo de partes. La mensajería se pausa tras 20 envíos sin respuesta del usuario.
- **Archivados por re-archivar:** los chats desarchivados para el pedido de aportes que todavía no han respondido; archivar «seguridad · SEC-21» solo si el usuario lo dice.

## Lo que no se toca
- Producción, `.github/workflows/`, `verificadores/`, `AGENTS.md`, `.claude/`, secretos y el `.env` de la carpeta principal (apunta a producción). Google Cloud solo en lectura para la IA; los cambios van por brief.
- `BRIEFS_POR_BLOQUE.md` y `TASKS.md`: solo el Tech Lead. Un PR fusionado no recibe commits; la corrección va en un PR nuevo desde `main`. Un parte ya en `main` no se edita.
- Archivos con dueña viva: la propiedad se amplía por PR de gobernanza. `app_core/db/session.py` fuera de la sección de GCP-05.
- El nombre del proveedor retirado y los identificadores de sus fichas, fuera de `governance/tareas/` (guardia de pruebas).
- Las pruebas no importan `yaml` (usan `tests/_lector_yaml.py`); SQL con parámetros ligados; valores simulados y correos `.invalid`; nunca `AUTH_MODE=headers`.
- Se comprueba la rama antes de cada commit; un PR de gobernanza por tanda; los de gobernanza no se mezclan con código.

## Pendientes del usuario
1. Pegar «Lanza la tanda: …» para abrir las cinco sesiones de `marca-y-gobernanza` y asignar las fichas libres.
2. Decidir si se consolidan los aportes restantes cuando lleguen los informes que faltan, y si se archiva «seguridad · SEC-21».
3. Decidir DEMO-05c (arreglo de la purga contra las tablas append-only): `session_replication_role` o el diseño que fije el CTO; hay que confirmar que Cloud SQL lo permita (Aporte 142, abierto).
4. Lo que ya estaba pendiente y sigue igual: preguntas al abogado (días hábiles frente a corridos, nombre del DPO visible, Vertex en us-central1, retención frente a supresión), los briefs de Google Cloud con Antigravity, los cambios de `.github/workflows/` (CI-23 `--destino` y el flag de ingress), y las lecturas de producción de solo lectura.
5. Su carpeta, tras fusionar el PR de partes: borrar la copia local de este parte y hacer `git pull --ff-only`.
