# Arquitectura del módulo Hoja de Ruta Inteligente
`¤roadmap` `¤rbac-tenant` `¤adpa`

> Detalle de módulo del SAD (`governance/ARQUITECTURA_SOFTWARE.md`). Fija **dónde** vive cada pieza y **cómo** se relacionan; el **qué** exige está en `PRD.md` (Módulo 5) y el **quién y cuándo**, en `governance/tareas/`. Aquí no hay estados de avance: estos caducan y se leen en las tareas.

## 1. Salas y núcleo compartido

| Componente | Ubicación | Responsabilidad | Compuerta |
| :--- | :--- | :--- | :--- |
| Sala **Organización** (`¤rbac-tenant`) | `features/organizacion/` | Usuarios, áreas, asignación de roles, SoD del DPO, cuatro ojos, alcance por área, configuración de la organización, alta de responsables. | `organizacion_service.py` |
| Sala **Hoja de Ruta** (`¤roadmap`) | `features/roadmap/` | Generación con IA, olas y tareas, evidencia, KPIs, consulta de auditoría. | `roadmap_service.py` |
| Núcleo compartido (no es sala) | `app_core/` | Infraestructura sin reglas de negocio: `db/session.py` (única fuente de sesión), `audit.py`, `errors.py`, `queue/`, `storage/`, `ai/deepseek_client.py`, `security.py`, `config.py`. | — |
| Capa REST | `api/routers/`, `api/rbac.py`, `api/errores.py` | Importa **solo** la compuerta y los tipos de `domain/` de la sala. | — |
| Frontend | `frontend/src/components/modules/roadmap/` | Pestaña «Hoja de Ruta»; store propio `useRoadmapStore`. | Contrato OpenAPI congelado |

Cada sala sigue la forma ya usada por las demás: `domain/` (tipos), `services/` (un motor por responsabilidad) y la compuerta `<sala>_service.py`. La sala Hoja de Ruta consume el SoD y los cuatro ojos **únicamente** a través de `organizacion_service`.

## 2. Convenciones que hacen independientes a las tareas

1. **Secciones reservadas en las compuertas.** La compuerta nace con una sección vacía por tarea que la ampliará (`# === RM-07 ===` … `# === fin RM-07 ===`); cada tarea edita solo la suya. Así varias tareas comparten un archivo sin conflictos.
2. **Autoregistro de routers.** Un módulo de `api/routers/` con `AUTO_REGISTRO = True` se incluye solo bajo `/api/v1`; los routers existentes siguen en `ROUTERS_MAP`. `main.py` no se vuelve a editar.
3. **Errores de negocio con catálogo.** `ErrorNegocio` lleva un código de `app_core/errors.py`; el manejador responde `detail` (texto, como hoy) más `code` y `action_required`, de modo que los clientes actuales no cambian.
4. **Una sola cabeza de migraciones.** `tests/test_alembic_una_cabeza.py` falla si hay dos cabezas; `main` exige la rama al día, así que quien fusiona después ajusta su `down_revision`.
5. **Pruebas propias y base por agente.** Cada tarea crea su archivo de pruebas y prueba en su propia rama hija de Neon, nunca en la rama `test` compartida.

La independencia se **comprueba**, no se afirma: `tests/test_indice_tareas.py` falla si dos tareas que pueden ejecutarse a la vez poseen el mismo archivo.

## 3. Modelo de datos

**Con RLS y `FORCE ROW LEVEL SECURITY` (7):** `areas`, `roadmaps`, `roadmap_waves`, `roadmap_tasks`, `task_evidence`, `task_audit_log`, `user_tenant_roles`.

**Tablas y columnas nuevas** (cada tabla nueva necesita `GRANT` explícito a `lopdp_app`; no hereda permisos):

| Elemento | Propósito |
| :--- | :--- |
| `audit_events` (`id`, `tenant_id`, `entity_type`, `entity_id`, `action`, `user_id`, `timestamp`, `payload`) | Registro inmutable de eventos que **no** son de una tarea: solicitudes de responsables, asignación y revocación de roles, configuración. Append-only (`lopdp_app` solo `SELECT` e `INSERT`), con RLS e índice por (`tenant_id`, `entity_type`, `entity_id`, `timestamp`). |
| `area_responsable_requests` | Solicitudes de alta de responsables y sus estados. |
| `user_tenant_roles.request_id` | Vincula el rol asignado con la solicitud que lo originó. |
| `users.google_sub` | Identificador estable de Google, único y opcional. |
| `tenants.tamano` + `CHECK` | Claves válidas: `micro`, `pequena`, `mediana`, `corporativo`; sin valor por defecto. |
| Trigger en `user_tenant_roles` | Valida la regla del encargado con rol de responsable en **ambas direcciones**, sin depender de `also_responsable`. |

**`task_audit_log` y `audit_events` son distintas a propósito.** El primero es de tareas: su `task_id` es obligatorio y sus registros se eliminan en cascada con la tarea (latente: ningún código de la aplicación borra tareas hoy). Hacer ese campo opcional debilitaría una tabla que ya funciona; una tabla genérica evita crear una por cada flujo.

## 4. Aislamiento (mecanismo)

* Cada transacción fija el tenant con `set_config('app.current_tenant_id', :tid, true)`; nunca `SET LOCAL` con un valor interpolado. `get_session` lee `X-Tenant-ID` y `X-User-ID` de las cabeceras hasta que SEC-03 sustituya la identidad.
* La aplicación se conecta con `lopdp_app` (sin `BYPASSRLS` ni propiedad de tablas); las migraciones usan el rol dueño. Sin tenant fijado, las políticas devuelven 0 filas.
* La regla del encargado se aplica en tres capas: trigger, servicio (error guiado) y respuesta de la API.

## 5. Contrato objetivo de la API (`/api/v1`)

Rol y tarea responsable de cada endpoint. El estado de avance **no** se guarda aquí.

| Endpoint | Método | Rol requerido | Tarea |
| :--- | :--- | :--- | :--- |
| `/roadmaps/generate` | POST | `implementador` | existente; RM-12 y RM-13 |
| `/roadmaps/jobs/{job_id}` | GET | cualquier rol activo | existente |
| `/roadmaps/{id}`, `/roadmaps/{id}/kpis` | GET | cualquier rol activo | existente |
| `/roadmaps/tasks/{id}` | PATCH (estado) | `implementador` | existente |
| `/roadmaps/tasks/{id}` | PATCH (campos de la tarea) | `implementador` | RM-07 |
| `/roadmaps/tasks/{id}/assign` | POST | `encargado` | RM-08 |
| `/roadmaps/{id}/audit-log` | GET | `encargado`, `dpo`, `implementador`, `admin_organizacion` | RM-09 |
| `/roadmaps/tasks/{id}/evidence/upload-url` | POST | `responsable_area`, `encargado` | existente |
| `/roadmaps/tasks/{id}/evidence` | POST / GET | `responsable_area`, `encargado` / cualquier rol activo | existente |
| `/roadmaps/tasks/{id}/evidence/{eid}` | PATCH | `encargado`, `dpo`, `implementador` | existente |
| `/organizacion/me/roles` | GET | cualquier rol activo | existente |
| `/organizacion/usuarios`, `/areas`, `/roles` | GET / POST / PATCH / DELETE | `admin_organizacion` | existente |
| `/organizacion/configuracion` | GET / PATCH | cualquier rol activo (GET); `admin_organizacion` (PATCH) | RM-15 |
| `/areas/responsable-requests` | POST | `encargado` | RM-10 |
| `/areas/responsable-requests`, `/areas/responsable-requests/{id}` | GET | `encargado`, `implementador` | RM-10 |
| `/areas/responsable-requests/{id}` | PATCH (cancelar si `pendiente`) | `encargado` | RM-10 |
| `/areas/responsable-requests/{id}/approve`, `/reject` | POST | `implementador` | RM-10 |
| `/areas/responsable-requests/{id}/execute` | POST | `implementador` | RM-10 |

## 6. Generación con IA y despliegue

* **Generación en línea.** `POST /roadmaps/generate` ejecuta la generación dentro de la solicitud y responde con `{job_id, status, roadmap_id}` ya terminado; los endpoints de estado siguen existiendo. La llamada al modelo va en un hilo aparte. `vercel.json` fija `maxDuration` en 300 s para `api/index.py`, el máximo del plan gratuito. Una llamada mide de 13 a 19 s (Anexo A del plan).
* **Documento válido.** El prompt incluye el esquema de `RoadmapDocument`; la salida cortada o inválida no se persiste y se reintenta con el error de validación.
* **Salud del despliegue.** `GET /api/v1/health` responde 200 y `OPERATIONAL` si todos los routers cargaron, y 503 y `DEGRADED` si alguno falló; el modo de emergencia responde 503 sin publicar el traceback.
* **Variables y procedimiento:** `governance/operaciones/PROCEDIMIENTO_VERCEL.md`.
