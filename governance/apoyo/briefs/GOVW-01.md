### BL-179 · satelite-go-vault-worker-eventarc-y-purga  (tanda 47)

**Contexto.** Sala(s): `go_vault_worker`. Depende de: `GCP-01`, `BOV-01`, `CON-01`, `ADPA-09`. Especificaciones: `governance/tareas/GOVW-01.md`, `governance/especificaciones/GOVW-01.md`.

**Objetivo** (en este orden):

1. `GOVW-01` — Microservicio en Go (services_go/vault_worker): receptor Eventarc, hashing SHA-256 en streaming y purga masiva en Cloud Run

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤motor-go-hibrido`: registrado en `VPA_MAP.md`.
- `¤boveda-cloud`: registrado en `VPA_MAP.md`.
- `¤conservacion`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `services_go/vault_worker/go.mod`
  - `services_go/vault_worker/main.go`
  - `services_go/vault_worker/vault_worker_service.go`
  - `services_go/vault_worker/Dockerfile`
  - `app_core/pasillo/go_vault_worker.py#GOVW-01`
  - `app_core/pasillo/conservacion.py#GOVW-01`
  - `tests/test_govw01_vault_worker_contract.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `GOVW-01`: pytest tests/test_govw01_vault_worker_contract.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

