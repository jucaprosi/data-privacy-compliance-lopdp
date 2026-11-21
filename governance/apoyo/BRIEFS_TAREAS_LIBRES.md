# Tareas libres y cómo lanzarlas
`¤adpa` `¤arbitro` `¤roadmap` `¤demo` `¤gobernanza`

> **Corte de `origin/main`:** `297bce7c` (merge de #916, 2026-11-21). Hoja del CTO; se rehace desde `origin/main` en cada corte.
> **Regla de esta hoja (CI-31):** el brief de cada ficha vive solo en `governance/apoyo/briefs/<ID>.md`. Aquí no se copian briefs, para que no se desfasen: cada tarea lleva su estado y la orden de lanzamiento que apunta a su brief.

## 1. Estado al corte

**No hay tareas de ingeniería libres.** La carpeta `governance/apoyo/briefs/` está vacía desde #916, y CI-34 (#920) dejó las pruebas del reparto en verde con la carpeta vacía. Todas las fichas de `governance/tareas/` están `hecha`, salvo las dos del propietario:

| ID | Sala | Agente | Estado al corte | Lo que falta |
| :--- | :--- | :--- | :--- | :--- |
| `DEMO-07` | `operaciones` | Ninguno (personas) | **Pendiente.** El bucket `lopdp360-demo-evidencias` ya está creado y verificado en `evydentia-demo`. | Paso 5 del brief: poner `PURGA_BUCKETS=lopdp360-demo-evidencias` en el Job de la purga, y el recorrido de aceptación en `DEMO_COMERCIAL.md`. |
| `GCP-05b` | `operaciones` | Ninguno (personas) | **Pendiente.** | Corrida real de `scripts/prueba_carga.py --entorno pruebas` y lectura de `max_connections` de Cloud SQL para el presupuesto de conexiones. |

Ninguna de las dos se lanza en una sesión de IA (PRD §5.5).

## 2. Avisos para la próxima tanda

Dos fichas cerradas dejaron trabajo fuera de su propiedad. No se reabren: si se quiere completar, va en fichas nuevas, que pasan por el Arquitecto y, si hay frontend, por el UX/UI.

- **NORM-03:** quedan tres puntos abiertos: el montaje de la pestaña «Impacto» en la pantalla de NORM-02 y dos compuertas más. Al corte, el router `api/routers/inteligencia_normativa_impacto.py` no está montado en la API, y los componentes de `frontend/src/components/normativa_impacto/**` no se usan fuera de su carpeta.
- **BOV-02:** el router de objetos (`features/boveda_cloud/routes/boveda_objetos_routes.py`) no está montado en la API, y la migración `bov02_boveda_objetos_custodia.py` sigue sin aplicarse en Cloud SQL. Montarlo exige tocar `main.py`, que está fuera de su propiedad.

## 3. Órdenes de lanzamiento

No hay ninguna al corte. Cuando el Tech Lead publique un brief nuevo en `governance/apoyo/briefs/`, el CTO añade aquí su orden con este molde, para pegarlo en una sesión nueva de VS Code con superpowers:

```text
Ejecuta la tarea <ID> siguiendo al pie de la letra su brief governance/apoyo/briefs/<ID>.md de origin/main (haz git fetch origin antes de leerlo). El contrato es governance/especificaciones/<ID>.md. Trabaja en un worktree propio en C:/Users/Juan Carlos/worktrees-evydentia/<id> con la rama tarea/juan-carlos/<id> creada desde origin/main. Abre un PR hacia main y no lo fusiones: lo simula y lo fusiona el CTO. Escribe en español.
```

## 4. Pendientes del propietario

- **Producción:** las migraciones de las fichas fusionadas (entre ellas RM-25b, RM-27 y BOV-02) se aplican en Cloud SQL con el brief `BRIEF_PROPIETARIO_MIGRACION_COMPLETA.md`, pasos 2 a 8, desde `main`.
- **Secreto `WEBHOOKS_CLAVE_CIFRADO`** en Secret Manager.
- **Carpeta vacía `C:\Users\Juan Carlos\worktrees-evydentia\demo-05d`:** algún proceso la tiene abierta. Se borra con `Remove-Item` después de cerrar VS Code o de reiniciar.
