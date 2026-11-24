+++
id = "DEMO-09"
titulo = "La web de demo se publica desde main con la imagen web de producción del mismo commit"
ola = "D"
estado = "pendiente"
tanda = 97
sala = "operaciones"
depende_de = ["DEMO-07", "GCP-03", "GCP-03b", "GCP-08", "GCP-08c"]
propiedad = ["governance/operaciones/DEMO_COMERCIAL.md", "governance/operaciones/entornos/demo/cloudrun_frontend.yaml", "tests/test_demo09_web_demo.py"]
crea = ["tests/test_demo09_web_demo.py"]
arbitro = "pytest tests/test_demo09_web_demo.py; mutaciones m1 a m4; el propietario sigue el procedimiento de DEMO_COMERCIAL.md §5 y la revisión nueva de evydentia-web-demo sirve /login con el digest del commit."
rastros = ["¤demo", "¤arbitro"]
+++

# DEMO-09 · La web de demo se publica desde main con la imagen web de producción del mismo commit

**Contrato:** `governance/especificaciones/DEMO-09.md` (manda sobre esta ficha).

**Origen.** Pedido del CTO (2026-11-23, `origin/main` 572b1127). El backend de la demo ya corre main, pero la web de la demo sigue con `web:v1`, del 2026-11-16, y no hay un procedimiento para reconstruirla.

## Entrega
- El procedimiento en `DEMO_COMERCIAL.md` §5: localizar o construir la imagen del commit, publicar la revisión sin tráfico, verificarla, pasarle el tráfico y saber volver atrás.
- `cloudrun_frontend.yaml` de la demo declara la imagen real: el repositorio web de producción.
- Una prueba exógena que compara el manifiesto, el procedimiento y `frontend/cloudbuild.yaml`.

## Límites
- No toca la nube. Los cambios en GCP los hace el propietario con Antigravity (R4). La ficha deja el procedimiento y el brief para el propietario en `C:\Users\Juan Carlos\compartido\evydentia\briefs\DEMO-09-propietario.md`, fuera del repositorio.
- No cambian `frontend/cloudbuild.yaml`, `frontend/Dockerfile.cloudrun` ni `.github/workflows/`. La interfaz no cambia, así que no pasa por UX/UI.
