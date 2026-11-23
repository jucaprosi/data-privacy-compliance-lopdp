# Tareas libres y cómo lanzarlas
`¤adpa` `¤arbitro` `¤roadmap` `¤demo` `¤gobernanza`

> **Corte de `origin/main`:** merge de #955 (briefs de LEG-06 y FE-29), 2026-11-23. Hoja del CTO; se rehace desde `origin/main` en cada corte.
> **Regla de esta hoja (CI-31):** el brief de cada ficha vive solo en `governance/apoyo/briefs/<ID>.md`. Aquí no se copian briefs, para que no se desfasen: cada tarea lleva su estado y la orden de lanzamiento que apunta a su brief.

## 1. Estado al corte

Las tandas 88 a 91 están cerradas:
- **CI-35** (#943), **GOB-05** (#944) y **GCP-03b** (#946).
- **GCP-04b** (#950).
- **CI-37** (#951): el pipeline tiene dos jobs y el push a `main` no repite el arnés si el PR ya verificó ese mismo árbol. La medición de después queda pendiente (§4).
- **CI-36** (#953): Node 22 en las imágenes, en `engines` y en el CI.

| ID | Brief | Sala | Tanda | Depende de (pendiente) | Estado al corte | Qué cierra |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `LEG-06` | `briefs/LEG-06.md` (#955) | `gobernanza` | 92 | — | **Lista para lanzar.** Por su R6 no puede haber otra ficha en `en_curso`: se lanza sola y nada más hasta que se fusione. | Licencia propietaria y aviso de derechos de autor en todo archivo de código versionado. |
| `FE-29` | `briefs/FE-29.md` (#955) | `frontend`, `pasillo_central`, `plataforma` | 93 | **LEG-06** | **Espera a LEG-06.** Ficha en #954. | Login que explica por qué una cuenta de Google no entra, con códigos estables en el backend y el botón «Usar otra cuenta de Google». |

## 2. Órdenes de lanzamiento

Cada orden se pega en una sesión nueva de VS Code con superpowers, o la ejecuta el Tech Lead en su sesión. El brief es autosuficiente: rama, «Escribe», «No hagas» y árbitro están en él. Modelo por defecto.

### LEG-06 (lanzar ya, sola)

```text
Ejecuta la tarea LEG-06 siguiendo al pie de la letra su brief governance/apoyo/briefs/LEG-06.md de origin/main (haz git fetch origin antes de leerlo). El contrato es governance/especificaciones/LEG-06.md. Trabaja en un worktree propio en C:/Users/Juan Carlos/worktrees-evydentia/leg-06 con la rama tarea/juan-carlos/leg-06 creada desde origin/main. Comprueba antes que ninguna ficha está en «en_curso» (R6). Abre un PR hacia main y no lo fusiones: lo simula y lo fusiona el CTO. Escribe en español.
```

### FE-29 (cuando LEG-06 esté en `main`)

```text
Ejecuta la tarea FE-29 siguiendo al pie de la letra su brief governance/apoyo/briefs/FE-29.md de origin/main (haz git fetch origin antes de leerlo). El contrato es governance/especificaciones/FE-29.md. Trabaja en un worktree propio en C:/Users/Juan Carlos/worktrees-evydentia/fe-29 con la rama tarea/juan-carlos/fe-29 creada desde origin/main, que ya trae LEG-06: todo archivo nuevo lleva el aviso de autor. Abre un PR hacia main y no lo fusiones: lo simula y lo fusiona el CTO. Escribe en español.
```

## 3. Despliegue a producción

Lo hace el propietario con `governance/operaciones/BRIEF_PROPIETARIO_DESPLIEGUE_MAIN.md`.

- Producción hoy: backend `evydentia-backend-00013-d4t` (`188d207c`) y web `evydentia-web-00006-xgz` (`web:e6dcb778`, Node 22), con el 100 % del tráfico en la revisión más reciente.
- FE-29 toca el backend y el frontend: tras su fusión se despliegan los dos.

## 4. Pendientes del propietario

- **Alta de cuentas** con el §5 del brief de despliegue: `evydentia@gmail.com` y, si se quiere, `juancarlosproanios@gmail.com` y `juancarlosproanio@gmail.com`. El 2026-11-23 ninguna estaba dada de alta: el backend respondió «Usuario no registrado en la plataforma».
- **Medición de después de CI-37:** la corre el Tech Lead tras 20 fusiones con el workflow nuevo (R6 de su especificación). El objetivo es una media de 12,21 min o menos.
- **YAML de entornos (aviso de GCP-03b):** en demo hay un client id en tiempo de ejecución que no tiene efecto, y en pruebas una variable `NEXT_PUBLIC_APP_ENV` que nadie lee. Si se limpian, va en una ficha.
- **`ZERAG_ARBITRO=1` en el CI (aviso de GOB-05):** activarlo es un cambio de workflow y lo decide el propietario.
- **Carpeta vacía `C:\Users\Juan Carlos\worktrees-evydentia\demo-05d`:** se borra con `Remove-Item` después de cerrar VS Code o de reiniciar.
