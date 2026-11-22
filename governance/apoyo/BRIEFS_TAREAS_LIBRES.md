# Tareas libres y cómo lanzarlas
`¤adpa` `¤arbitro` `¤roadmap` `¤demo` `¤gobernanza`

> **Corte de `origin/main`:** `41aec2ef` (merge de #950, 2026-11-22). Hoja del CTO; se rehace desde `origin/main` en cada corte.
> **Regla de esta hoja (CI-31):** el brief de cada ficha vive solo en `governance/apoyo/briefs/<ID>.md`. Aquí no se copian briefs, para que no se desfasen: cada tarea lleva su estado y la orden de lanzamiento que apunta a su brief.

## 1. Estado al corte

Las tandas 88 y 89 están cerradas:
- **CI-35** (#943): el índice de tareas es válido con 0 fichas pendientes.
- **GOB-05** (#944): el generador del índice sigue el molde de ZERAG y conserva lo que trajo CI-35.
- **GCP-03b** (#946): el client id de Google entra al compilar y la imagen web se etiqueta por commit. Cierra el incidente del login del 2026-11-22.

**GCP-04b** (#950) también está cerrada: el YAML del balanceador quedó igual que la nube, comprobado por el CTO con gcloud de solo lectura.

| ID | Brief | Sala | Tanda | Depende de (pendiente) | Estado al corte | Qué cierra |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `CI-37` | `briefs/CI-37.md` | `gobernanza` | 90 | — | **En curso, PR #951 en borrador.** Falta el commit del propietario con el workflow nuevo, que ya revisó el CTO. | Minutos de GitHub Actions por fusión reducidos al menos a la mitad, sin perder árbitros. |
| `CI-36` | `briefs/CI-36.md` | `frontend` | 91 | **CI-37** | **Espera a CI-37**, que reescribe el workflow. La ficha incluye ya `tests/test_gcp03_frontend_cloudrun.py`, que exigía `alpine:3.20`. | Node 22 LTS en imágenes, CI y `engines`; sin `EBADENGINE`. |
| `LEG-06` | Pendiente | `gobernanza` | — | **CI-36** | **Espera a CI-36**: las dos tocan `frontend/package.json`. Especificación en #947. | Licencia propietaria y aviso de derechos de autor en todo archivo de código versionado. |

Las tres van en cadena por lo que comparten: CI-37 y CI-36 el workflow, CI-36 y LEG-06 `frontend/package.json`.

## 2. Órdenes de lanzamiento

Cada orden se pega en una sesión nueva de VS Code con superpowers, o la ejecuta el Tech Lead en su sesión. El brief es autosuficiente: rama, «Escribe», «No hagas» y árbitro están en él. Modelo por defecto.

### CI-36 (cuando CI-37 esté en `main`)

```text
Ejecuta la tarea CI-36 siguiendo al pie de la letra su brief governance/apoyo/briefs/CI-36.md de origin/main (haz git fetch origin antes de leerlo). El contrato es governance/especificaciones/CI-36.md. Trabaja en un worktree propio en C:/Users/Juan Carlos/worktrees-evydentia/ci-36 con la rama tarea/juan-carlos/ci-36 creada desde origin/main. Abre el PR hacia main como borrador, con el comando del commit del propietario para las node-version, y no lo fusiones: lo simula y lo fusiona el CTO. Escribe en español.
```

### CI-37 (en curso, PR #951)

```text
Ejecuta la tarea CI-37 siguiendo al pie de la letra su brief governance/apoyo/briefs/CI-37.md de origin/main (haz git fetch origin antes de leerlo). El contrato es governance/especificaciones/CI-37.md. Trabaja en un worktree propio en C:/Users/Juan Carlos/worktrees-evydentia/ci-37 con la rama tarea/juan-carlos/ci-37 creada desde origin/main. No escribas en .github/workflows: deja el workflow nuevo en C:/Users/Juan Carlos/worktrees-evydentia/ci-37-workflow.yml y en el PR el comando con que lo aplica el propietario. Abre el PR hacia main como borrador y no lo fusiones: lo simula y lo fusiona el CTO. Escribe en español.
```

### LEG-06 (todavía no)

Su orden se añade aquí cuando CI-36 esté en `main` y el Tech Lead publique su brief.

## 3. Despliegue a producción

Lo hace el propietario con `governance/operaciones/BRIEF_PROPIETARIO_DESPLIEGUE_MAIN.md`.

- Producción hoy: backend `evydentia-backend-00013-d4t` (`188d207c`) y web `evydentia-web-00005-w7s` (`web:798ca0b1`), con el 100 % del tráfico en la revisión más reciente.
- El frontend nuevo trae la pestaña «Impacto» (NORM-03b) y el menú de Vigilancia Normativa.
- El incidente del WAF está cerrado: `BRIEF_PROPIETARIO_WAF_403_LOGIN.md`, sección «Resultado».

## 4. Pendientes del propietario

- **Cuenta sin «s»** (`juancarlosproanio@gmail.com`): si al entrar recibe «Usuario no registrado» o «no perteneces a ninguna organización», se da de alta con el §5 del brief de despliegue.
- **YAML de entornos (aviso de GCP-03b):** en demo hay un client id en tiempo de ejecución que no tiene efecto, y en pruebas una variable `NEXT_PUBLIC_APP_ENV` que nadie lee. Si se limpian, va en una ficha.
- **`ZERAG_ARBITRO=1` en el CI (aviso de GOB-05):** activarlo es un cambio de workflow y lo decide el propietario.
- **Carpeta vacía `C:\Users\Juan Carlos\worktrees-evydentia\demo-05d`:** algún proceso la tiene abierta. Se borra con `Remove-Item` después de cerrar VS Code o de reiniciar.
