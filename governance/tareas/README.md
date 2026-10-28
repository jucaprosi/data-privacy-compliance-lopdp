# Especificaciones de tareas

Una especificación por tarea (`<ID>.md`). Es la **fuente de verdad** de la tarea: su cabecera la lee `scripts/generar_indice_tareas.py`, que genera el índice de `governance/artefactos/TASKS.md` y **comprueba** que las tareas son independientes. Un agente de desarrollo que toma una tarea solo necesita leer su especificación, el PRD (Módulo 5) y `governance/arquitectura/HOJA_DE_RUTA_ADPA.md`.

> **Agente de desarrollo:** sesión de Claude, Codex u otra herramienta que implementa una tarea del plan. **No** es el asistente de IA (Copiloto) de la plataforma, que no usa estas ramas ni este protocolo.

## Cabecera (TOML entre dos líneas `+++`)

| Campo | Significado |
| :--- | :--- |
| `id`, `titulo` | Identificador (igual al nombre del archivo) y título. |
| `ola` | `A` a `E`, `indep` (sin ola) o `backlog`. |
| `estado` | `pendiente`, `en_curso`, `hecha` o `bloqueada`. **Solo vive aquí.** |
| `sala` | Sala ADPA o área a la que pertenece. |
| `depende_de` | Ids que deben estar integrados antes. |
| `propiedad` | Archivos o patrones que **solo esta tarea** puede modificar. `archivo#SECCION` posee solo esa sección reservada del archivo. |
| `arbitro` | Comprobación exógena que decide si está terminada. |

## Reglas de independencia

1. **Propiedad exclusiva.** Dos tareas que pueden ejecutarse a la vez (ninguna espera a la otra, ni directa ni indirectamente) no pueden poseer el mismo archivo. Lo comprueba `tests/test_indice_tareas.py`; si se rompe, se corrige la propiedad, no la prueba.
2. **Secciones reservadas.** Una compuerta (`<sala>_service.py`) la crea la tarea de reestructuración con una sección vacía por tarea (`# === RM-07 ===` … `# === fin RM-07 ===`). Cada tarea edita solo la suya.
3. **Routers nuevos sin tocar `main.py`.** Cada router va en su módulo de `api/routers/` con `AUTO_REGISTRO = True` (RM-00).
4. **Errores de negocio** con `ErrorNegocio` y un código del catálogo `app_core/errors.py`; nunca texto suelto.
5. **Pruebas propias.** Cada tarea crea su archivo de pruebas, incluidas las de RLS de sus tablas nuevas. No se amplía un archivo de pruebas ajeno.
6. **Migraciones.** `down_revision` es la cabeza de `main` al crear la rama. `tests/test_alembic_una_cabeza.py` falla si hay dos cabezas. La CI de cada PR prueba su fusión con `main` y la de `main` corre tras cada fusión, así que no hace falta exigir ramas al día; si dos migraciones se integran casi a la vez, se resuelve con `alembic merge heads` en un commit propio (plan de reserva: CI-01).
7. **Base de pruebas por agente de desarrollo.** Cada agente de desarrollo prueba y migra en su **propia rama hija de Neon** (`test-<agente>`), nunca en la rama `test` compartida (OPS-04). El plan gratuito admite 10 ramas por proyecto.
8. **Un agente de desarrollo, una tarea; la rama y el PR son los de su persona (regla 10).** El aislamiento lo da la propiedad exclusiva de archivos (regla 1), no git: aunque dos agentes compartan carpeta, cada uno escribe solo su `propiedad` y no modifica, revierte ni «limpia» un archivo ajeno. Un árbol de trabajo propio (`git worktree add <ruta corta>`) es una comodidad recomendada, no la frontera ni un requisito. Si varias sesiones comparten una carpeta, la propiedad exclusiva evita que se pisen los archivos, pero quedan dos riesgos que ella no cubre: (a) la rama activa es una sola, así que otra sesión puede cambiarla bajo los pies de la tuya; antes de cada commit ejecuta `git branch --show-current` y añade siempre por ruta (`git add <archivo>`), nunca `git add -A` ni `git add .`; (b) la suite completa también ejecuta los archivos a medio escribir de las demás sesiones; si falla por un archivo que no es tuyo, no lo toques, repórtalo o vuelve a ejecutarla cuando ese archivo esté estable. El coordinador comprueba que el diff de cada rama cabe en la propiedad del bloque con `python scripts/verificar_reparto.py --rama <rama> --bloque <BL-xx>`.
9. **PR de código por tarea; PR de gobernanza por tanda** (decisión del propietario, 2026-10-22). Todo cambio llega a `main` por PR, porque `main` está protegida y su CI es el árbitro, pero los PR se agrupan así:
   - **Código:** un PR por persona y por noche, con las tareas del día en commits separados (regla 10). Las correcciones del coordinador a una entrega van **en ese mismo PR, antes de fusionarlo**, nunca en un PR posterior.
   - **Gobernanza** (cierres de tareas, fichas nuevas, briefs, índice y arreglos de documentos de `governance/`): **un solo PR por tanda**, al terminarla: cierra las tareas fusionadas y abre las de la tanda siguiente.
   - **Excepción:** lo urgente para la seguridad o para producción va en su propio PR en el momento, y lo que un PR posterior necesita para pasar sus verificadores (por ejemplo, ampliar una propiedad antes de que el diff de una tarea quepa en ella).
10. **Una rama por persona; a `main` solo en la ventana nocturna** (decisión del propietario, 2026-10-28). Manda sobre las reglas 8 y 9 en lo que digan de ramas y PR.
   - **Tres ramas de trabajo:** `dev/juan-carlos`, `dev/aleczandra` y `dev/jose`. Cada persona hace todo su trabajo del día en la suya, y nadie hace commits ni push en la de otro. Las sesiones de IA de una persona trabajan en la rama de esa persona.
   - **Cada tarea en sus propios commits,** con su id en el mensaje (`feat(diag-03): …`). Para comprobar que una tarea cabe en su propiedad: `python scripts/verificar_reparto.py --rama <commit final de la tarea> --base <commit anterior a la tarea> --bloque <BL-xx>`.
   - **Trabajo en paralelo:** quien lleve varias tareas a la vez puede usar ramas o worktrees **locales y temporales**, pero solo integra y empuja en su rama `dev/…`.
   - **Carpetas propias:** nadie cambia la rama de una carpeta o worktree que usa otra persona u otra sesión. Lo que necesite `main` (por ejemplo, migrar) se corre en un worktree aparte.
   - **Durante el día no se fusiona nada en `main`.** Desde las 19:00 (hora de Ecuador) cada persona abre o actualiza su PR `dev/<persona>` → `main`, y se fusionan **de uno en uno**. Antes de fusionar cada PR:
     - se pone al día con `main`;
     - si trae migración, se vuelve a encadenar a la cabeza actual (`alembic heads` debe mostrar una sola) y se migra la rama Neon `test` antes de que corra su CI.
   - **Producción se migra una sola vez,** al terminar la ventana, desde `main`, por quien hizo las fusiones.
   - **A la mañana siguiente,** cada persona pone su rama al día con `main` (`git fetch origin` y `git merge origin/main`) antes de seguir.
   - **Excepción:** lo urgente para la seguridad o para producción (regla 9) se fusiona en el momento, avisando a los otros dos.
   - **Motivo:** el 27 y 28 de octubre de 2026, tres PR con migración (BIB-108, INC-01 y ORG-14) chocaron por la cabeza de Alembic al fusionarse durante el día. Además, una sesión quiso cambiar la rama de una carpeta que usaba otro chat.

## Flujo de una tarea

1. Crear la rama desde `main` actualizado y su árbol de trabajo; crear su rama de Neon.
2. Poner `estado = "en_curso"` en la especificación.
3. Implementar solo lo que declara la entrega, dentro de su propiedad.
4. Ejecutar su árbitro y la suite completa; `python scripts/generar_indice_tareas.py --verificar` debe dar 0.
5. Abrir el PR y esperar a que el check `Arnés Físico Determinista` esté en verde. El agente no marca la tarea como hecha: lo hace el coordinador en el PR de gobernanza de la tanda (regla 9), una vez fusionado el código.

Cambiar el estado **no** obliga a regenerar el índice de `TASKS.md`, que solo contiene lo estable. Ver el estado: `python scripts/generar_indice_tareas.py --estado`.
