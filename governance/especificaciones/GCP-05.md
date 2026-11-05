# GCP-05 · Escalado verificable en Cloud Run
`¤sdd` `¤cloud-run-perf` `¤arbitro`

## 1. Datos

Parámetros de los manifiestos de Cloud Run:

| Servicio | Mínimo (pruebas / producción) | Máximo | Concurrencia |
| :--- | :--- | :--- | :--- |
| Backend (`cloudrun_service.yaml`) | 0 / 1 | 10 | 80 |
| Frontend (`cloudrun_frontend_service.yaml`) | 0 / 0 | 5 | 80 |

Presupuesto de conexiones: `max_instancias_backend × (pool_size + max_overflow) ≤ conexiones_de_PgBouncer`, donde las conexiones de PgBouncer salen del manifiesto de GCP-04.

## 2. API

Sin API nueva. `python scripts/prueba_carga.py --entorno pruebas --usuarios 200 --duracion 300` recorre rutas de lectura autenticadas con usuarios de prueba y escribe p50, p95, p99 y el conteo de respuestas por código.

## 3. Reglas

- **R1 · Límites explícitos.** Ningún servicio de Cloud Run queda sin mínimo, máximo y concurrencia declarados.
- **R2 · Presupuesto de conexiones.** El máximo de instancias del backend no puede abrir más conexiones que las que admite PgBouncer.
- **R3 · Nunca contra producción.** El script rechaza un host que coincida con el de producción y no lee el `.env` de la carpeta principal.
- **R4 · Meta medible.** 200 usuarios simultáneos en lectura: p95 menor que 800 ms y cero respuestas 5xx. Si no se cumple, el informe lo dice; no se ajusta la meta para que pase.

## 4. Interfaz

Sin interfaz de usuario. El informe vive en `governance/operaciones/PRUEBA_DE_CARGA.md`.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** los dos manifiestos, **cuando** se leen, **entonces** cada uno declara mínimo, máximo y concurrencia. | `test_manifiestos_con_limites_explicitos` |
| **Dado** un máximo de 10 instancias y un pool de 5 más 5, **cuando** PgBouncer admite 80 conexiones, **entonces** la prueba falla porque 100 supera 80. | `test_presupuesto_de_conexiones` |
| **Dado** el host de producción como destino, **cuando** se lanza el script, **entonces** termina con código distinto de 0 sin enviar ninguna petición. | `test_prueba_carga_rechaza_produccion` |

## 6. Trazabilidad

- `PRD_EVYDENTIA_REVENTA_NUBE.md` §5.3 (Cloud Run, PgBouncer) e invariante `INV_CLOUD_RUN_SINGLE_RTT_RLS`; requisito 9 de la revisión del 2026-11-04.
