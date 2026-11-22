# Tareas libres y cómo lanzarlas
`¤adpa` `¤arbitro` `¤roadmap` `¤demo` `¤gobernanza`

> **Corte de `origin/main`:** `d323aedf` (merge de #940, 2026-11-22). Hoja del CTO; se rehace desde `origin/main` en cada corte.
> **Regla de esta hoja (CI-31):** el brief de cada ficha vive solo en `governance/apoyo/briefs/<ID>.md`. Aquí no se copian briefs, para que no se desfasen: cada tarea lleva su estado y la orden de lanzamiento que apunta a su brief.

## 1. Estado al corte

El 2026-11-22 hubo dos incidentes en el login de producción.
- **Imagen web sin client id de Google.** La imagen `web:188d207c` se construyó sin él, y el propietario volvió a `web:v2`. La corrección es GCP-03b.
- **Bloqueo de Cloud Armor.** La firma `owasp-crs-v030301-id942421-sqli` bloqueaba el login. El propietario la excluyó en la nube, y GCP-04b la lleva al repositorio.

| ID | Brief | Sala | Tanda | Depende de (pendiente) | Estado al corte | Qué cierra |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GCP-03b` | `briefs/GCP-03b.md` (#938) | `frontend` | 89 | — | **Lista para lanzar. Prioridad.** | Client id de Google incrustado al compilar la imagen web y etiqueta por commit (`_ETIQUETA`). Desbloquea el despliegue del frontend nuevo. |
| `CI-35` | `briefs/CI-35.md` (#930) | `gobernanza` | 88 | — | **Lista para lanzar.** | Índice de tareas y sus pruebas válidos con 0 fichas pendientes. |
| `GCP-04b` | Pendiente; lo escribe el Tech Lead | `operaciones` | — | — | **Sin brief.** Ficha y especificación en #940. | `cloud_load_balancer.yaml` con la exclusión de 942421 y el registro del balanceador, con su árbitro. |
| `CI-36` | Pendiente; lo escribe el Tech Lead | `frontend` | — | **GCP-03b** | **Espera a GCP-03b**: los dos tocan `frontend/Dockerfile.cloudrun`. Ficha en #936. | Node 22 LTS en imágenes, CI y `engines`. El cambio de `node-version` del workflow lo aplica el propietario. |

GCP-03b, CI-35 y GCP-04b no comparten archivos ni traen migraciones: van en paralelo y se fusionan según llega su CI en verde.

## 2. Órdenes de lanzamiento

Cada orden se pega en una sesión nueva de VS Code con superpowers. El brief es autosuficiente: rama, «Escribe», «No hagas» y árbitro están en él. Modelo por defecto.

### GCP-03b (lanzar ya, prioridad)

```text
Ejecuta la tarea GCP-03b siguiendo al pie de la letra su brief governance/apoyo/briefs/GCP-03b.md de origin/main (haz git fetch origin antes de leerlo). El contrato es governance/especificaciones/GCP-03b.md. Trabaja en un worktree propio en C:/Users/Juan Carlos/worktrees-evydentia/gcp-03b con la rama tarea/juan-carlos/gcp-03b creada desde origin/main. Abre un PR hacia main y no lo fusiones: lo simula y lo fusiona el CTO. Escribe en español.
```

### CI-35 (lanzar ya, en paralelo)

```text
Ejecuta la tarea CI-35 siguiendo al pie de la letra su brief governance/apoyo/briefs/CI-35.md de origin/main (haz git fetch origin antes de leerlo). El contrato es governance/especificaciones/CI-35.md. Trabaja en un worktree propio en C:/Users/Juan Carlos/worktrees-evydentia/ci-35 con la rama tarea/juan-carlos/ci-35 creada desde origin/main. Abre un PR hacia main y no lo fusiones: lo simula y lo fusiona el CTO. Escribe en español.
```

### GCP-04b y CI-36 (todavía no)

Sus órdenes se añaden aquí cuando el Tech Lead publique sus briefs. CI-36, además, cuando GCP-03b esté en `main`.

## 3. Despliegue a producción

Lo hace el propietario con `governance/operaciones/BRIEF_PROPIETARIO_DESPLIEGUE_MAIN.md`.

- Producción hoy: backend `evydentia-backend-00013-d4t` (`188d207c`) y web `evydentia-web-00003-m7w` (`web:v2`).
- El frontend nuevo se publica cuando GCP-03b esté en `main`. Con él llegan la pestaña «Impacto» (NORM-03b) y el menú de Vigilancia Normativa.
- El incidente del WAF está cerrado: `BRIEF_PROPIETARIO_WAF_403_LOGIN.md`, sección «Resultado».

## 4. Pendientes del propietario

- **Cuenta sin «s»** (`juancarlosproanio@gmail.com`): si al entrar recibe «Usuario no registrado» o «no perteneces a ninguna organización», se da de alta con el §5 del brief de despliegue.
- **Carpeta vacía `C:\Users\Juan Carlos\worktrees-evydentia\demo-05d`:** algún proceso la tiene abierta. Se borra con `Remove-Item` después de cerrar VS Code o de reiniciar.
