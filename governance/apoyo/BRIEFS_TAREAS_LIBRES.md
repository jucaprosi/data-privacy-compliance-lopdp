# Tareas libres y cómo lanzarlas
`¤adpa` `¤arbitro` `¤roadmap` `¤demo` `¤gobernanza`

> **Corte de `origin/main`:** `222ab590` (merge de #927, 2026-11-21). Hoja del CTO; se rehace desde `origin/main` en cada corte.
> **Regla de esta hoja (CI-31):** el brief de cada ficha vive solo en `governance/apoyo/briefs/<ID>.md`. Aquí no se copian briefs, para que no se desfasen: cada tarea lleva su estado y la orden de lanzamiento que apunta a su brief.

## 1. Estado al corte

Las fichas del propietario DEMO-07 y GCP-05b se cerraron en #922 y #923. El Arquitecto abrió la tanda de montaje de routers y compuertas normativas (#925), y el Tech Lead escribió sus briefs (#927).

| ID | Brief | Sala | Tanda | Estado al corte | Qué cierra |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `BOV-02b` | `briefs/BOV-02b.md` | `boveda_cloud` | 86 | **Lista para lanzar.** | Monta los routers de objetos y del orquestador desde la compuerta de la sala, sin tocar `main.py`. |
| `IA-12` | `briefs/IA-12.md` | `inferencia` | 86 | **Lista para lanzar.** | Vectores y caché de contexto de Vertex AI por la compuerta de `inferencia`. Desbloquea REG-03. |
| `NORM-03b` | `briefs/NORM-03b.md` | `frontend` | 86 | **Lista para lanzar.** Interfaz cerrada por UX/UI (especificación §4 y §5). | Pestaña «Impacto» en el panel de una resolución de NORM-02. |
| `REG-03` | `briefs/REG-03.md` | `regulacion_rag` | 87 | **Espera a IA-12 en `main`.** | Compuertas de vectores, caché y corpus citable: las dos que dejó abiertas NORM-03, y `obtener_o_crear_cache_normativo` y `corpus_citable`, que el pasillo ya llama. |
| `CI-35` | Pendiente, la escribe el Tech Lead | `gobernanza` | Sin asignar | **Sin brief** (`agente = "ninguno"` hasta que exista). Ficha y especificación en #926. | Índice de tareas y sus pruebas válidos con 0 fichas pendientes: lo que dejó `main` en rojo tras #922 y #923. |

Corrección del corte anterior: el router de impacto de NORM-03 sí está montado (por `AUTO_REGISTRO`). Lo que faltaba era la pestaña, que ahora va en NORM-03b.

## 2. Órdenes de lanzamiento

Cada orden se pega en una sesión nueva de VS Code con superpowers. El brief es autosuficiente: rama, «Escribe», «No hagas» y árbitro están en él. Modelo por defecto para las cuatro.

### Tanda 86 (lanzar ya, las tres en paralelo)

```text
Ejecuta la tarea BOV-02b siguiendo al pie de la letra su brief governance/apoyo/briefs/BOV-02b.md de origin/main (haz git fetch origin antes de leerlo). El contrato es governance/especificaciones/BOV-02b.md. Trabaja en un worktree propio en C:/Users/Juan Carlos/worktrees-evydentia/bov-02b con la rama tarea/juan-carlos/bov-02b creada desde origin/main. Abre un PR hacia main y no lo fusiones: lo simula y lo fusiona el CTO. Escribe en español.
```

```text
Ejecuta la tarea IA-12 siguiendo al pie de la letra su brief governance/apoyo/briefs/IA-12.md de origin/main (haz git fetch origin antes de leerlo). El contrato es governance/especificaciones/IA-12.md. Trabaja en un worktree propio en C:/Users/Juan Carlos/worktrees-evydentia/ia-12 con la rama tarea/juan-carlos/ia-12 creada desde origin/main. Abre un PR hacia main y no lo fusiones: lo simula y lo fusiona el CTO. Escribe en español.
```

```text
Ejecuta la tarea NORM-03b siguiendo al pie de la letra su brief governance/apoyo/briefs/NORM-03b.md de origin/main (haz git fetch origin antes de leerlo). El contrato es governance/especificaciones/NORM-03b.md; sus §4 y §5 son el contrato de la interfaz cerrado por UX/UI. Trabaja en un worktree propio en C:/Users/Juan Carlos/worktrees-evydentia/norm-03b con la rama tarea/juan-carlos/norm-03b creada desde origin/main. Abre un PR hacia main y no lo fusiones: lo simula y lo fusiona el CTO. Escribe en español.
```

### Tanda 87 (cuando IA-12 esté fusionado)

```text
Ejecuta la tarea REG-03 siguiendo al pie de la letra su brief governance/apoyo/briefs/REG-03.md de origin/main (haz git fetch origin antes de leerlo y comprueba que IA-12 ya está en main; si no, no empieces). El contrato es governance/especificaciones/REG-03.md. Trabaja en un worktree propio en C:/Users/Juan Carlos/worktrees-evydentia/reg-03 con la rama tarea/juan-carlos/reg-03 creada desde origin/main. Abre un PR hacia main y no lo fusiones: lo simula y lo fusiona el CTO. Escribe en español.
```

### CI-35 (todavía no)

Su orden se añade aquí cuando el Tech Lead publique `briefs/CI-35.md` y quite `agente = "ninguno"` de la ficha en el mismo PR.

## 3. Avisos

- **BOV-02:** la migración `bov02_boveda_objetos_custodia` ya está aplicada en Cloud SQL (fila del 2026-11-15 de `REGISTRO_MIGRACIONES_MANUALES.md`). BOV-02b no trae migración.
- **Seguimientos del Arquitecto** que esperan la aprobación del propietario: (a) el origen «normativa»; (b) el pasillo de tareas y plantillas.

## 4. Pendientes del propietario

- **#924** (registro de la migración de 12 cabezas y `WEBHOOKS_CLAVE_CIFRADO` en `deploy-gcp.yml`): toca un workflow, así que lo fusiona el propietario.
- **Carpeta vacía `C:\Users\Juan Carlos\worktrees-evydentia\demo-05d`:** algún proceso la tiene abierta. Se borra con `Remove-Item` después de cerrar VS Code o de reiniciar.
