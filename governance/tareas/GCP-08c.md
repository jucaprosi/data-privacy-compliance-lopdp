+++
id = "GCP-08c"
titulo = "Datos de ICU completos en la imagen web para formatear en es-EC"
ola = "D"
estado = "pendiente"
tanda = 95
sala = "frontend, operaciones"
depende_de = ["CI-36", "GCP-03", "GCP-03b", "GCP-08", "GCP-08b", "QA-12", "RET-05"]
propiedad = ["frontend/Dockerfile.cloudrun", "tests/test_gcp08_proxy_e_imagen.py", "tests/test_ci36_version_node.py", "tests/test_gcp03_frontend_cloudrun.py"]
crea = []
arbitro = "pytest tests/test_gcp08_proxy_e_imagen.py con docker; test_08 da «lunes, 23 de noviembre de 2026» y «$1.234.567,89» dentro de la imagen; test_05 cabe en el presupuesto nuevo de §1; mutación m1 (quitar los datos de ICU) da rojo; pytest tests/test_ci36_version_node.py tests/test_gcp03_frontend_cloudrun.py; índice y especificaciones con código 0."
rastros = ["¤arbitro"]
+++

# GCP-08c · Datos de ICU completos en la imagen web para formatear en es-EC

**Contrato:** `governance/especificaciones/GCP-08c.md` (manda sobre esta ficha).

**Origen.** Hallazgo del Arquitecto al medir GCP-08b, aceptado por el CTO el 2026-11-23. Prioridad normal, sin bloquear nada.

## Entrega
- La imagen web formatea fechas y números en `es-EC` también en el servidor.
- Una prueba dentro de la imagen.
- El presupuesto de GCP-08b se actualiza con su propia regla (GCP-08b R2).

## Límites
- Solo el runner del Dockerfile y las tres pruebas que lo describen.
- Va después de GCP-08b, en una tanda posterior: las dos son dueñas de `tests/test_gcp08_proxy_e_imagen.py`.
- Si la comprobación en físico de R1 no reproduce el defecto, la ficha se cierra sin cambios.
