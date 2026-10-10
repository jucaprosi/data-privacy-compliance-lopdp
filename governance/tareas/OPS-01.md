+++
id = "OPS-01"
titulo = "Variables de entorno en Vercel"
ola = "E"
estado = "pendiente"
sala = "operaciones"
depende_de = []
propiedad = ["governance/operaciones/VARIABLES_VERCEL.md"]
arbitro = "lista revisada por el usuario; cada variable cargada en su entorno"
rastros = ["¤seguridad"]
+++

# OPS-01 · Variables de entorno en Vercel

**Objetivo.** Dejar por escrito qué variable va en qué entorno, sin valores. Los valores los carga el usuario.

## Entrega
- Production y Preview: `DATABASE_URL` (rol `lopdp_app`), `JWT_SECRET`, `CORS_ORIGINS`, `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, las de R2 y las de Redis mientras el estado de los trabajos siga allí, y las de Google (SEC-03) y del correo (NOTIF-01).
- Alinear Preview con Production: hoy le faltan `CORS_ORIGINS` (cae en `*`) y `DEEPSEEK_MODEL`.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
