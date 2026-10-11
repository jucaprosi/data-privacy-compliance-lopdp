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
8. **Un agente de desarrollo, una tarea, una rama, un PR.** El aislamiento lo da la propiedad exclusiva de archivos (regla 1), no git: aunque dos agentes compartan carpeta, cada uno escribe solo su `propiedad` y no modifica, revierte ni «limpia» un archivo ajeno. Un árbol de trabajo propio (`git worktree add <ruta corta>`) es una comodidad recomendada, porque dos sesiones sobre una carpeta cambian de rama bajo los pies de la otra, pero no es la frontera. El coordinador comprueba que el diff de cada rama cabe en la propiedad del bloque con `python scripts/verificar_reparto.py --rama <rama> --bloque <BL-xx>`.

## Flujo de una tarea

1. Crear la rama desde `main` actualizado y su árbol de trabajo; crear su rama de Neon.
2. Poner `estado = "en_curso"` en la especificación.
3. Implementar solo lo que declara la entrega, dentro de su propiedad.
4. Ejecutar su árbitro y la suite completa; `python scripts/generar_indice_tareas.py --verificar` debe dar 0.
5. Poner `estado = "hecha"`, abrir el PR y esperar a que el check `Arnés Físico Determinista` esté en verde.

Cambiar el estado **no** obliga a regenerar el índice de `TASKS.md`, que solo contiene lo estable. Ver el estado: `python scripts/generar_indice_tareas.py --estado`.
