+++
id = "GCP-04b"
titulo = "Exclusión de la firma 942421 en Cloud Armor y registro permanente del balanceador"
ola = "backlog"
estado = "pendiente"
sala = "operaciones"
depende_de = ["GCP-04", "GCP-09"]
propiedad = ["governance/operaciones/cloud_load_balancer.yaml", "tests/test_gcp04b_waf_y_registro.py"]
crea = ["tests/test_gcp04b_waf_y_registro.py"]
arbitro = "pytest tests/test_gcp04b_waf_y_registro.py tests/test_gcp04_cloudsql_migration_cutover.py tests/test_gcp09_dominio_e_ingress.py; mutaciones m1 a m4."
rastros = ["¤seguridad", "¤arbitro"]
+++

# GCP-04b · Exclusión de la firma 942421 en Cloud Armor y registro permanente del balanceador

**Contrato:** `governance/especificaciones/GCP-04b.md` (manda sobre esta ficha).

**Origen.** Incidente del login del 2026-11-22, brief `BRIEF_PROPIETARIO_WAF_403_LOGIN.md` (#939). El propietario aplica la corrección en Cloud Armor. Esta ficha deja el repositorio igual que la nube y fija el registro del balanceador.

## Entrega
- Regla 1000 de `evydentia-waf` con la expresión final que aplicó el propietario.
- Registro activado, con muestreo 1, en los dos servicios de backend.
- Un árbitro de texto que compruebe las dos cosas.

## Límites
- Cambiar Cloud Armor o los servicios de backend en la nube lo hace el propietario.
