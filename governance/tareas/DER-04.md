+++
id = "DER-04"
titulo = "Contracción de DER-03: retirar la columna tenant_id uuid y el trigger de compatibilidad de las solicitudes ARCO"
ola = "backlog"
estado = "pendiente"
sala = "derechos_arco"
depende_de = ["DER-03"]
propiedad = ["alembic/versions/20261109_derechos_contraccion_tenant.py", "tests/test_der04_contraccion.py"]
crea = ["alembic/versions/20261109_derechos_contraccion_tenant.py", "tests/test_der04_contraccion.py"]
arbitro = "pytest tests/test_der04_contraccion.py + suite completa + verificar_migracion_compatible.py; FUSION_ALEMBIC"
rastros = ["¤arbitro"]
+++

# DER-04 · Contracción de la migración de DER-03

DER-03 aplica la fase de expansión (expand/contract, GCP-07): columna de texto nueva, FK `NOT VALID` más `VALIDATE` y un trigger que mantiene la revisión estable. Esta ficha es la contracción, en una migración marcada con `CONTRACCION = True`, que se despliega solo cuando ninguna revisión en servicio use la columna vieja:
- retira la columna `tenant_id` uuid y el trigger;
- mantiene la guardia de huérfanos: si queda alguno, aborta sin tocar la tabla.

Pendiente del diseño del Arquitecto ADPA y de la confirmación del propietario sobre el momento del despliegue.
