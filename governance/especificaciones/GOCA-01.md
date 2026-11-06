# GOCA-01 · Agente Local Edge en Go para NVR/Cámaras con Subida Directa TLS a GCS
`¤sdd` `¤motor-go-hibrido` `¤videovigilancia-cctv` `¤boveda-cloud`

## 1. Datos

Manifiesto de aprovisionamiento `CCTVEdgeAgentConfig` (`tenant_id`, `camara_id`, `codec_required='H265'`, `strip_audio=True`, `max_segment_seconds=120`, `upload_signed_url_endpoint`).

## 2. API

- `POST /api/v1/videovigilancia/camaras/{camara_id}/aprovisionar-agente-go` -> `200 OK` (devuelve configuración firmada compatible con `services_go/cctv_agent/config_schema.json`).

## 3. Reglas

- **R1 · Supresión forzada de audio en el borde.** El agente en Go descarta cualquier stream de audio antes de sellar el `SHA-256` local y subir el clip a la Bóveda.
- **R2 · Subida directa a GCS.** El binario en Go transmite los bytes del clip directamente a la URL firmada de Google Cloud Storage y envía únicamente el metadato (~1 KB JSON) al backend.

## 4. Interfaz

Descarga de archivo de configuración firmado desde la ficha de cámara en `CCTV-01`.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una cámara conforme en `CCTV-01`, **cuando** se genera su paquete de aprovisionamiento para el agente en Go, **entonces** el JSON cumple `services_go/cctv_agent/config_schema.json` con `strip_audio = True` y credenciales acotadas al `tenant_id`. | `test_aprovisionamiento_agente_edge_go_valido` |
| **Dado** un reporte de telemetría del agente Go que indica pista de audio presente, **cuando** el pasillo `go_cctv_agent.py#GOCA-01` lo evalúa, **entonces** bloquea la ingesta. | `test_agente_go_rechaza_stream_con_audio` |

## 6. Trazabilidad

- PRD §8.3, §7.1 (`go_cctv_agent`) e invariante `INV_LOPDP_DIRECT_TO_GCS_ZERO_RAM_STREAM`.
