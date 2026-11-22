# Tareas libres y cómo lanzarlas
`¤adpa` `¤arbitro` `¤roadmap` `¤demo` `¤gobernanza`

> **Corte de `origin/main`:** `798ca0b1` (merge de #947, 2026-11-22). Hoja del CTO; se rehace desde `origin/main` en cada corte.
> **Regla de esta hoja (CI-31):** el brief de cada ficha vive solo en `governance/apoyo/briefs/<ID>.md`. Aquí no se copian briefs, para que no se desfasen: cada tarea lleva su estado y la orden de lanzamiento que apunta a su brief.

## 1. Estado al corte

Las tandas 88 y 89 están cerradas:
- **CI-35** (#943): el índice de tareas es válido con 0 fichas pendientes.
- **GOB-05** (#944): el generador del índice sigue el molde de ZERAG y conserva lo que trajo CI-35.
- **GCP-03b** (#946): el client id de Google entra al compilar y la imagen web se etiqueta por commit. Cierra el incidente del login del 2026-11-22.

Ninguna ficha tiene brief al corte. Las cuatro pendientes esperan a su brief o a otra ficha:

| ID | Brief | Sala | Depende de (pendiente) | Estado al corte | Qué cierra |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GCP-04b` | Pendiente; lo escribe el Tech Lead | `operaciones` | — | **Sin brief.** Ficha y especificación en #940. | `cloud_load_balancer.yaml` con la exclusión de 942421 y el registro del balanceador, con su árbitro. |
| `CI-36` | Pendiente; lo escribe el Tech Lead | `frontend` | — | **Sin brief.** Ya no espera a GCP-03b. Ficha en #936. | Node 22 LTS en imágenes, CI y `engines`. El cambio de `node-version` del workflow lo aplica el propietario. |
| `CI-37` | Pendiente; lo escribe el Tech Lead | `gobernanza` | — | **Sin brief.** Especificación en #945. | Minutos de GitHub Actions por fusión reducidos a la mitad sin perder árbitros. Toca `.github/workflows/zero-regression-pipeline.yml`: ese archivo lo aplica el propietario. |
| `LEG-06` | Pendiente; lo escribe el Tech Lead | `gobernanza` | **CI-36** | **Espera a CI-36**: los dos tocan `frontend/package.json`. Especificación en #947. | Licencia propietaria y aviso de derechos de autor en todo archivo de código versionado. |

GCP-04b, CI-36 y CI-37 no comparten archivos ni traen migraciones: cuando tengan brief van en paralelo y se fusionan según llega su CI en verde.

## 2. Órdenes de lanzamiento

Cada orden se pega en una sesión nueva de VS Code con superpowers, o la ejecuta el Tech Lead en su sesión. El brief es autosuficiente: rama, «Escribe», «No hagas» y árbitro están en él. Modelo por defecto.

No hay órdenes al corte. Se añaden aquí cuando el Tech Lead publique los briefs de GCP-04b, CI-36 y CI-37, y el de LEG-06 cuando CI-36 esté en `main`.

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
