+++
id = "GCP-10"
titulo = "Contexto de la imagen del frontend sin dependencias locales, compilados ni secretos: frontend/.dockerignore y su prueba"
ola = "backlog"
estado = "pendiente"
sala = "frontend"
depende_de = ["GCP-03", "GCP-08"]
propiedad = ["frontend/.dockerignore", "tests/test_gcp10_dockerignore.py"]
crea = ["frontend/.dockerignore", "tests/test_gcp10_dockerignore.py"]
arbitro = "pytest tests/test_gcp10_dockerignore.py: frontend/.dockerignore existe y excluye node_modules, .next, .env*, tests, playwright-report, test-results y *.log; la prueba falla si Dockerfile.cloudrun copia . (COPY . .) y el .dockerignore no existe, o si deja de excluir node_modules o .next; mutaciones documentadas: borrar .dockerignore y quitar node_modules o .next de la lista, cada una hace fallar su caso"
rastros = ["¤navegacion-menus"]
+++

# GCP-10 · Contexto de la imagen del frontend sin dependencias locales ni secretos

**Origen.** Hallazgo del despliegue del balanceador, trasladado por el CTO (2026-11-12): `docker build -f frontend/Dockerfile.cloudrun ... frontend/` falla en una carpeta con `frontend/node_modules` local: `COPY . .` copia 1,29 GB y el enlace `@ai-sdk/google` choca con `COPY --from=deps /app/node_modules`. No existe `frontend/.dockerignore`. No urge para hoy (Antigravity compila desde un worktree limpio), pero evita que el próximo despliegue se rompa igual. Debe pasar por el Arquitecto como las demás fichas.

## Medido en `origin/main`
- `frontend/Dockerfile.cloudrun` (GCP-03, GCP-08) copia el contexto entero con `COPY . .` en la etapa `builder` y después reemplaza `node_modules` con el de la etapa `deps` (el comentario del propio Dockerfile lo supone: «otro sistema»).
- El `.gitignore` del repositorio ya ignora `.env`, `.env.*`, `.next/` y `node_modules/`; lo que Git ignora **no** lo ignora Docker, así que un contexto de un worktree con esos archivos locales los envía a la imagen de la etapa de compilación (los secretos locales no llegan a la etapa final, que solo copia `public`, `.next/standalone` y `.next/static`, pero sí pasan por el contexto y por la caché de capas).
- `frontend/tsconfig.json` incluye `**/*.ts` y `**/*.tsx`: al excluir `tests/` y las configuraciones de Playwright del contexto, `next build` ya no los ve; no hay importaciones de `src/` hacia `tests/` (el ingeniero lo comprueba con `git grep` antes de excluirlos).

## Entrega
1. `frontend/.dockerignore` (nuevo), con al menos: `node_modules`, `.next`, `.env*` (con excepción `!.env.example` si existe), `tests/`, `playwright-report/`, `test-results/`, `*.log`, `coverage/`, `.vercel/`, `*.tsbuildinfo` y los archivos del propio Docker que no deben entrar (`Dockerfile*` no es necesario en el contexto de la etapa de compilación, pero `docker build -f` los lee fuera del contexto: el ingeniero lo comprueba). Antes de fijar la lista, el ingeniero mide qué otras cosas del contexto no deben ir a la imagen (secretos, `.env`, archivos de editor y de sistema) y qué necesita la compilación (`public/`, `src/`, `package*.json`, `next.config*.ts`, `tsconfig.json`, `postcss.config.mjs`).
2. `tests/test_gcp10_dockerignore.py` (nuevo): lee `frontend/.dockerignore` y `frontend/Dockerfile.cloudrun` (sin `import yaml`; es texto plano) y falla si el Dockerfile usa `COPY . .` sin `.dockerignore`, o si `.dockerignore` deja de excluir `node_modules` o `.next`, o los patrones de secretos (`.env*`).

## Pruebas (cada una con su mutación)
- Existe `frontend/.dockerignore` y excluye `node_modules`, `.next`, `.env*`, `tests/`, `playwright-report/` y `*.log`.
- Borrar el archivo, o quitar `node_modules` o `.next` de la lista, hace fallar su caso.
- No se ejecuta Docker en el CI de esta ficha: la prueba es estática. El propietario puede comprobarlo con `docker build -f frontend/Dockerfile.cloudrun -t evydentia-web frontend/` en una carpeta con `node_modules` local (opcional, brief del Arquitecto).
