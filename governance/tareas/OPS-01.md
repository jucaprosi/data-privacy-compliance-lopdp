+++
id = "OPS-01"
titulo = "Inventario de variables de entorno por servicio en Cloud Run"
ola = "E"
estado = "hecha"
sala = "operaciones"
depende_de = []
propiedad = ["governance/tareas/OPS-01.md"]
arbitro = "lista revisada por el usuario; cada variable cargada en su entorno"
rastros = ["¤seguridad"]
+++

# OPS-01 · Variables de entorno en Cloud Run

**Objetivo.** Dejar por escrito qué variable va en qué entorno, sin valores. Los valores los carga el usuario.

## Entrega
- Servicios de Cloud Run (`backend` y `frontend`) y entornos: `DATABASE_URL` (rol `lopdp_app`), `JWT_SECRET`, `CORS_ORIGINS`, configuración de Vertex AI (`GOOGLE_CLOUD_PROJECT`, `VERTEX_LOCATION`), `GCP_STORAGE_BUCKET`, OIDC de Google (`SEC-03`) y secretos en Secret Manager.
- Consistencia de variables obligatorias verificada al arranque por `exigir_arranque_seguro` (`SEC-16`, `SEC-17`).

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
