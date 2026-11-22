# Tareas libres y cómo lanzarlas
`¤adpa` `¤arbitro` `¤roadmap` `¤demo` `¤gobernanza`

> **Corte de `origin/main`:** `e61da907` (merge de #934, 2026-11-21). Hoja del CTO; se rehace desde `origin/main` en cada corte.
> **Regla de esta hoja (CI-31):** el brief de cada ficha vive solo en `governance/apoyo/briefs/<ID>.md`. Aquí no se copian briefs, para que no se desfasen: cada tarea lleva su estado y la orden de lanzamiento que apunta a su brief.

## 1. Estado al corte

Las fichas del propietario DEMO-07 y GCP-05b se cerraron en #922 y #923. El Arquitecto abrió la tanda de montaje de routers y compuertas normativas (#925), y el Tech Lead escribió sus briefs (#927) y el de CI-35 (#930). La tanda 86 y la 87 están fusionadas y cerradas: IA-12 (#929), REG-03 (#933), NORM-03b (#932) y BOV-02b (#934). Queda CI-35.

| ID | Brief | Sala | Tanda | Estado al corte | Qué cierra |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CI-35` | `briefs/CI-35.md` (#930) | `gobernanza` | 88 | **Lista para lanzar.** Ficha y especificación en #926. Independiente de las tandas cerradas. | Índice de tareas y sus pruebas válidos con 0 fichas pendientes: lo que dejó `main` en rojo tras #922 y #923. |

## 2. Órdenes de lanzamiento

Cada orden se pega en una sesión nueva de VS Code con superpowers. El brief es autosuficiente: rama, «Escribe», «No hagas» y árbitro están en él. Modelo por defecto.

### Tanda 88 (lanzar ya)

```text
Ejecuta la tarea CI-35 siguiendo al pie de la letra su brief governance/apoyo/briefs/CI-35.md de origin/main (haz git fetch origin antes de leerlo). El contrato es governance/especificaciones/CI-35.md. Trabaja en un worktree propio en C:/Users/Juan Carlos/worktrees-evydentia/ci-35 con la rama tarea/juan-carlos/ci-35 creada desde origin/main. Abre un PR hacia main y no lo fusiones: lo simula y lo fusiona el CTO. Escribe en español.
```

## 3. Avisos

- **Tandas 86 y 87:** ninguna trae migración. La migración `bov02_boveda_objetos_custodia` ya está aplicada en Cloud SQL (fila del 2026-11-15 de `REGISTRO_MIGRACIONES_MANUALES.md`).
- **Seguimientos del Arquitecto** que esperan la aprobación del propietario: (a) el origen «normativa»; (b) el pasillo de tareas y plantillas.

## 4. Pendientes del propietario

- **Desplegar `main`** con `deploy-gcp.yml` para que producción monte los routers de la bóveda (BOV-02b) y la pestaña «Impacto» (NORM-03b). Sin migraciones nuevas.
- **Carpeta vacía `C:\Users\Juan Carlos\worktrees-evydentia\demo-05d`:** algún proceso la tiene abierta. Se borra con `Remove-Item` después de cerrar VS Code o de reiniciar.
