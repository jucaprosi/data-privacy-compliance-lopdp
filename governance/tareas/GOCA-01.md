+++
id = "GOCA-01"
titulo = "Agente Edge en Go (services_go/cctv_agent): conector local de cámaras/NVR con recorte por eventos H.265, supresión de audio y subida directa TLS a GCS"
ola = "D"
estado = "pendiente"
sala = "go_cctv_agent"
depende_de = ["CCTV-01", "BOV-02"]
propiedad = ["services_go/cctv_agent/go.mod", "services_go/cctv_agent/main.go", "services_go/cctv_agent/cctv_agent_service.go", "services_go/cctv_agent/config_schema.json", "app_core/pasillo/go_cctv_agent.py#GOCA-01", "app_core/pasillo/videovigilancia.py#GOCA-01", "features/videovigilancia/services/cctv_provisioning_bundle.py", "tests/test_goca01_cctv_edge_agent_contract.py"]
arbitro = "pytest tests/test_goca01_cctv_edge_agent_contract.py + suite completa + vigilantes"
rastros = ["¤motor-go-hibrido", "¤videovigilancia-cctv", "¤boveda-cloud"]
+++
# GOCA-01 · Agente Edge en Go (services_go/cctv_agent): conector local de cámaras/NVR con recorte por eventos H.265, supresión de audio y subida directa TLS a GCS

## Entrega
- Agente local multiplataforma en Go (`services_go/cctv_agent/`) compilable a binario único de ~10 MB sin dependencias externas, que toma los segmentos de movimiento del NVR local, verifica ausencia de pista de audio (`-an`), calcula el `SHA-256` en origen y sube el clip `.mp4` (H.265) directamente a Google Cloud Storage usando la `Signed URL V4` emitida para el `tenant_id`.
- Generador de paquete de aprovisionamiento `features/videovigilancia/services/cctv_provisioning_bundle.py` y pasillo `app_core/pasillo/go_cctv_agent.py#GOCA-01`.

## Pruebas
- `pytest tests/test_goca01_cctv_edge_agent_contract.py` valida el esquema de aprovisionamiento del agente en Go, la firma del manifiesto de cámara y el rechazo de subida si el agente reporta pista de audio activa o hash discrepante.
