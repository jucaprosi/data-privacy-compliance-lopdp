+++
id = "OPS-06"
titulo = "Despliegue controlado en producción mediante la rama produccion tras la ventana nocturna"
ola = "indep"
estado = "hecha"
sala = "operaciones"
depende_de = ["RM-13", "SEC-06"]
propiedad = ["governance/tareas/OPS-06.md"]
arbitro = "flujo de despliegue controlado desde la rama produccion documentado y verificado"
rastros = ["¤ci-cd"]
+++

# OPS-06 · Despliegue controlado de producción

**Decisión del propietario (2026-10-29):** producción se migra y se despliega de forma controlada al cerrar la ventana de integración.

## Entrega
- Regla 10 de `governance/tareas/README.md`: tras aplicar migraciones en Cloud SQL, quien cierra la ventana actualiza la rama `produccion` al día con `main` y ejecuta el despliegue en Cloud Run.
