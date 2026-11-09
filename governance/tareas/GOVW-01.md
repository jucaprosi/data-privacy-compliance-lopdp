+++
id = "GOVW-01"
titulo = "Microservicio en Go (services_go/vault_worker): receptor Eventarc, hashing SHA-256 en streaming y purga masiva en Cloud Run"
ola = "D"
estado = "pendiente"
sala = "go_vault_worker"
depende_de = ["GCP-01", "BOV-01", "CON-01", "ADPA-09"]
propiedad = ["services_go/vault_worker/go.mod", "services_go/vault_worker/main.go", "services_go/vault_worker/vault_worker_service.go", "services_go/vault_worker/Dockerfile", "app_core/pasillo/go_vault_worker.py#GOVW-01", "app_core/pasillo/conservacion.py#GOVW-01", "tests/test_govw01_vault_worker_contract.py"]
arbitro = "pytest tests/test_govw01_vault_worker_contract.py + suite completa + vigilantes"
rastros = ["¤motor-go-hibrido", "¤boveda-cloud", "¤conservacion"]
+++
# GOVW-01 · Microservicio en Go (services_go/vault_worker): receptor Eventarc, hashing SHA-256 en streaming y purga masiva en Cloud Run

## Entrega
- Microservicio compilado en Go (`services_go/vault_worker/`) con `Dockerfile` multi-stage `distroless` (< 25 MB, Cold Start < 50 ms, `min-instances=0`) que recibe webhooks CloudEvents de *Eventarc* al finalizar subidas en Google Cloud Storage, calcula el hash `SHA-256` en streaming de memoria constante O(1) y ejecuta lotes de purga física.
- Contrato de pasillo en `app_core/pasillo/go_vault_worker.py#GOVW-01` y `app_core/pasillo/conservacion.py#GOVW-01` con verificación de firma HMAC entre el satélite Go y el Core Python.

## Pruebas
- `pytest tests/test_govw01_vault_worker_contract.py` verifica el contrato de eventos CloudEvents/Eventarc, la validación HMAC del resultado de hashing/purga emitido por el worker en Go y la estructura compilable del módulo `services_go/vault_worker`.
