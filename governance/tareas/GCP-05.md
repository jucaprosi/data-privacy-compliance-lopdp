+++
id = "GCP-05"
titulo = "Escalado verificable en Cloud Run: límites de instancias, presupuesto de conexiones y prueba de carga"
ola = "C"
estado = "pendiente"
sala = "operaciones"
depende_de = ["GCP-01", "GCP-03", "GCP-04"]
propiedad = ["governance/operaciones/cloudrun_service.yaml", "governance/operaciones/cloudrun_frontend_service.yaml", "governance/operaciones/PRUEBA_DE_CARGA.md", "scripts/prueba_carga.py", "tests/test_gcp05_escalado.py"]
arbitro = "pytest tests/test_gcp05_escalado.py + suite completa + vigilantes; prueba de carga contra el entorno de pruebas con su informe en PRUEBA_DE_CARGA.md"
rastros = ["¤cloud-run-perf", "¤arbitro"]
+++
# GCP-05 · Escalado verificable en Cloud Run: límites de instancias, presupuesto de conexiones y prueba de carga

**Origen.** Revisión de la constitución de la reventa en la nube contra los diez requisitos de una aplicación vendible, 2026-11-04. GCP-01 fija `--concurrency=80`, pero ni el PRD ni las tareas fijan el mínimo y el máximo de instancias ni exigen medir que la plataforma escala.

**Contrato:** `governance/especificaciones/GCP-05.md`.

## Entrega
- Mínimo y máximo de instancias y concurrencia explícitos en `governance/operaciones/cloudrun_service.yaml` (backend, creado por GCP-01) y `governance/operaciones/cloudrun_frontend_service.yaml` (frontend, creado por GCP-03). Va después de ambas, así que no comparte archivo con una tarea simultánea.
- Prueba `tests/test_gcp05_escalado.py` que lee los manifiestos y comprueba el presupuesto de conexiones contra el límite de PgBouncer y Cloud SQL de GCP-04.
- Script `scripts/prueba_carga.py`: usuarios simultáneos simulados contra el **entorno de pruebas** (nunca producción); escribe percentiles de latencia y errores.
- Informe `governance/operaciones/PRUEBA_DE_CARGA.md` con la fecha, el entorno, la configuración y los resultados de la corrida.

## Decisiones asumidas
- Backend: mínimo 0 instancias en pruebas y 1 en producción (evita el arranque en frío del primer usuario; cuesta una instancia permanente); máximo 10. Frontend: mínimo 0, máximo 5. El máximo también es un tope de gasto. El propietario los ajusta.
- Meta inicial de la prueba de carga: 200 usuarios simultáneos en lectura con p95 menor que 800 ms y ningún 5xx.

## Pruebas
- `pytest tests/test_gcp05_escalado.py` comprueba que ambos manifiestos declaran mínimo, máximo y concurrencia, y que `max_instancias × tamaño_del_pool ≤ conexiones_de_PgBouncer`.
- `python scripts/prueba_carga.py --entorno pruebas` y su informe; el script se niega a correr contra el host de producción.
