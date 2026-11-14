### BL-183 · agente-edge-go-cctv-recorte-eventos-y-subida-tls  (tanda 47)

**Contexto.** Sala(s): `go_cctv_agent`. Depende de: `CCTV-01`, `BOV-02`. Especificaciones: `governance/tareas/GOCA-01.md`, `governance/especificaciones/GOCA-01.md`.

**Objetivo** (en este orden):

1. `GOCA-01` — Agente Edge en Go (services_go/cctv_agent): conector local de cámaras/NVR con recorte por eventos H.265, supresión de audio y subida directa TLS a GCS

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤motor-go-hibrido`: registrado en `VPA_MAP.md`.
- `¤videovigilancia-cctv`: registrado en `VPA_MAP.md`.
- `¤boveda-cloud`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `services_go/cctv_agent/go.mod`
  - `services_go/cctv_agent/main.go`
  - `services_go/cctv_agent/cctv_agent_service.go`
  - `services_go/cctv_agent/config_schema.json`
  - `app_core/pasillo/go_cctv_agent.py#GOCA-01`
  - `app_core/pasillo/videovigilancia.py#GOCA-01`
  - `features/videovigilancia/services/cctv_provisioning_bundle.py`
  - `tests/test_goca01_cctv_edge_agent_contract.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `GOCA-01`: pytest tests/test_goca01_cctv_edge_agent_contract.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

