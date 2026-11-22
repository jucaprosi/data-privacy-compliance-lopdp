+++
id = "GCP-03b"
titulo = "Client id de Google incrustado al compilar la imagen web y etiqueta por commit"
ola = "backlog"
estado = "pendiente"
sala = "frontend"
depende_de = ["EP-02", "GCP-01", "GCP-03", "GCP-08", "GCP-09", "GCP-10", "QA-12", "RET-05"]
propiedad = ["frontend/Dockerfile.cloudrun", "frontend/cloudbuild.yaml", "tests/test_gcp03_frontend_cloudrun.py"]
crea = []
arbitro = "pytest tests/test_gcp03_frontend_cloudrun.py; mutaciones m1 a m4; tras la fusión, el propietario construye con _ETIQUETA=<commit> y el login muestra «Continuar con Google»."
rastros = ["¤arbitro", "¤seguridad"]
+++

# GCP-03b · Client id de Google incrustado al compilar la imagen web y etiqueta por commit

**Contrato:** `governance/especificaciones/GCP-03b.md` (manda sobre esta ficha).

**Origen.** Incidente en producción del 2026-11-21, pedido del CTO con prioridad. La revisión evydentia-web-00004-xkg (web:188d207c) muestra en el login «Falta configurar NEXT_PUBLIC_GOOGLE_CLIENT_ID en el servidor». El propietario volvió a evydentia-web-00003-m7w.

## Entrega
- La etapa `builder` vuelve a declarar el client id, y un árbitro impide que se pierda otra vez.
- La imagen web se etiqueta con el commit, no con `v2`.

## Límites
- Reconstruir y publicar la imagen lo hace el propietario, después de la fusión.
- Los YAML de `governance/operaciones/entornos/` no cambian (§1).
