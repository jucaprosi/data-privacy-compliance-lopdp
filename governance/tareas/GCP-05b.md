+++
id = "GCP-05b"
titulo = "Prueba de carga real contra el entorno de pruebas y confirmación del presupuesto de conexiones"
ola = "C"
estado = "pendiente"
sala = "operaciones"
depende_de = ["GCP-05", "EP-09"]
propiedad = ["governance/operaciones/PRUEBA_DE_CARGA.md", "governance/operaciones/presupuesto_conexiones.yaml"]
crea = []
arbitro = "python scripts/prueba_carga.py --entorno pruebas con su informe en PRUEBA_DE_CARGA.md + pytest tests/test_gcp05_escalado.py"
rastros = ["¤cloud-run-perf", "¤arbitro"]
+++

# GCP-05b · Prueba de carga real contra el entorno de pruebas y confirmación del presupuesto de conexiones

**Origen.** Partición de GCP-05 autorizada por el propietario (2026-11-13) para desbloquear GCP-06. GCP-05 entrega los límites, el pool, el presupuesto y el script; esta ficha recoge lo que el #689 dejó pendiente.

## Entrega
- Corrida real de `scripts/prueba_carga.py --entorno pruebas` contra el entorno de pruebas puesto en marcha (EP-09): 200 usuarios simultáneos en lectura, p95 < 800 ms y ningún 5xx. Informe en `governance/operaciones/PRUEBA_DE_CARGA.md` con fecha, entorno, configuración y resultados. Nunca contra producción.
- `max_connections` de Cloud SQL confirmado por el propietario con solo lectura (`gcloud sql instances describe` y `SHOW max_connections;`). `presupuesto_conexiones.yaml` deja de ser `provisional` con la fuente y la fecha de esa lectura.
- Si la medición no cumple la meta, se ajustan el pool o `maxScale` en una ficha posterior; esta no cambia los manifiestos.

## Límites
- Producción sigue con `minScale` 0 hasta la fase beta (PRD §5.4, pilar 9). Ese cambio lo hace el propietario en `deploy-gcp.yml`.
