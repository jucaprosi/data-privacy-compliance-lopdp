# BOV-04 · Centro de Mando de las 10 Dimensiones LOPDP y Bóveda Cloud
`¤sdd` `¤boveda-cloud` `¤videovigilancia-cctv` `¤dpo-cockpit` `¤conservacion`

## 1. Datos

Proyección `ResumenOrquestadorDiezDimensiones` (`tenant_id`, `dimensiones: list[EstadoDimensionCloud]`, `uso_boveda_gb`, `uso_egress_gb`, `camaras_activas`, `clips_en_hold_legal`, `actas_destruccion_emitidas`, `escaneos_dlp_completados`).

## 2. API

- `GET /api/v1/boveda-cloud/orquestador-10d` -> `200 OK`

## 3. Reglas

- **R1 · Prohibición de cifra única global (`INV_LOPDP_MULTIDIMENSIONAL_METRICS`).** El orquestador expone cada una de las 10 dimensiones y las métricas de la Bóveda por separado; nunca calcula un porcentaje escalar único.
- **R2 · Trazabilidad de actas criptográficas.** Toda automatización de purga o congelamiento enlaza su certificado `SHA-256` verificable por el DPO.

## 4. Interfaz

Pantalla `frontend/src/components/pantallas/BOV-04.tsx` con la matriz de las 10 Dimensiones + Bóveda Cloud, estado de purgas automáticas y acceso a las actas `SHA-256`.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una organización con paquete de Bóveda activo, cámaras registradas y actas de purga emitidas, **cuando** consulta `GET /api/v1/boveda-cloud/orquestador-10d`, **entonces** recibe el desglose separado de las 10 dimensiones y telemetría de nube sin porcentaje único global. | `test_orquestador_10_dimensiones_sin_cifra_unica` |
| **Dado** un DPO que supervisa la organización, **cuando** consulta el resumen por pasillo `dpo_cockpit.py#BOV-04`, **entonces** visualiza las actas de destrucción `SHA-256` y los clips bajo Hold Legal en modo solo lectura. | `test_dpo_consulta_orquestador_boveda_read_only` |

## 6. Trazabilidad

- PRD §8.1–8.4, Doctrina 4 e invariante `INV_LOPDP_MULTIDIMENSIONAL_METRICS`.
