+++
id = "GCP-08b"
titulo = "Presupuesto de tamaño de la imagen web"
ola = "D"
estado = "pendiente"
sala = "frontend, operaciones"
depende_de = ["CI-36", "GCP-08", "QA-12"]
propiedad = ["tests/test_gcp08_proxy_e_imagen.py"]
crea = []
arbitro = "pytest tests/test_gcp08_proxy_e_imagen.py con docker; la imagen de main cabe en el presupuesto y test_06 sigue rojo con una imagen que lo supere (mutación m1); índice y especificaciones con código 0."
rastros = ["¤arbitro"]
agente = "ninguno"
+++

# GCP-08b · Presupuesto de tamaño de la imagen web

**Contrato:** `governance/especificaciones/GCP-08b.md` (manda sobre esta ficha).

**Origen.** Pedido del CTO (2026-11-23). La imagen de main estaba a 16 KB del límite de 120 MB, y FE-29 (#972) lo supera por 512 bytes.

## Entrega
- El límite de `test_05` pasa a ser un presupuesto con margen explícito: la medida de main más un 15 %, redondeado a MB.
- Sin recorte de la imagen: §1 explica por qué.

## Límites
- `frontend/Dockerfile.cloudrun` no cambia.
- Es ortogonal a FE-29, que se reintegra después.
