+++
id = "OPS-06"
titulo = "Producción se despliega una vez por noche desde la rama produccion, no en cada fusión a main"
ola = "indep"
estado = "hecha"
sala = "operaciones"
depende_de = ["RM-13", "SEC-06"]
propiedad = ["vercel.json", "frontend/vercel.json", "tests/test_vercel_despliegue.py", "governance/operaciones/PROCEDIMIENTO_VERCEL.md"]
arbitro = "pytest tests/test_vercel_despliegue.py; tras fusionar, cero despliegues nuevos en Vercel al fusionar en main y dos al empujar produccion (lista de despliegues de GitHub)"
rastros = ["¤ci-cd"]
+++

# OPS-06 · Despliegue nocturno de producción

**Hallazgo (2026-10-29).** El plan gratuito de Vercel admite 100 despliegues al día. Las ramas de trabajo ya no despliegan desde el 2026-10-26, pero cada fusión a `main` crea dos despliegues de producción, uno por proyecto: hubo 28 el 2026-10-29 con 14 fusiones. Con tres personas fusionando de uno en uno cada noche (regla 10), el cupo se agota.

**Decisión del propietario (2026-10-29):** bloquear los despliegues como en el resto del proceso: producción se migra y se despliega **una sola vez** al cerrar la ventana nocturna.

## Entrega
- `vercel.json` y `frontend/vercel.json`: `git.deploymentEnabled` = `{"produccion": true, "preview/**": true, "**": false}`; `main` deja de desplegar.
- `tests/test_vercel_despliegue.py` exige esas reglas en los dos archivos.
- Regla 10 de `governance/tareas/README.md`: tras migrar, quien cerró la ventana pone `produccion` al día con `main`.
- `governance/operaciones/PROCEDIMIENTO_VERCEL.md`, apartado 6: configuración y comando.

## Para el propietario (una vez, en el panel de Vercel)
En los dos proyectos, *Settings* → *Environments* → *Production* → *Branch Tracking*: `produccion`. Hasta hacerlo y empujar `produccion` por primera vez, producción se queda en el último despliegue de `main`.
