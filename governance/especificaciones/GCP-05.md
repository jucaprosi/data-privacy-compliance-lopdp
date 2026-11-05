# GCP-05 · Observabilidad nativa: registro JSON sin datos personales en Cloud Logging, Cloud Trace, Error Reporting, comprobaciones de disponibilidad y alertas de SLO y de presupuesto
`¤sdd` `¤observabilidad` `¤grado-productivo` `¤cloud-run-perf` `¤seguridad`

## 1. Datos

Registro estructurado `RegistroJSON` (`severity: str`, `message: str`, `tenant_id: UUID | None`, `request_id: str`, `ruta: str`, `codigo: int`, `latencia_ms: float`, `trace: str | None`). Manifiesto `monitoreo_alertas.yaml` (`uptime_checks[]`, `alert_policies[]`, `budgets[]`, `notification_channels[]`).

## 2. API

- No crea rutas nuevas: instrumenta todas las existentes y reutiliza `GET /health` y `GET /api/v1/health` como objetivo de las comprobaciones de disponibilidad.

## 3. Reglas

- **R1 · Sin datos personales (`INV_OBS_STRUCTURED_LOGS_NO_PERSONAL_DATA`).** Ningún registro contiene cédulas, RUC, correos, teléfonos ni contenido de evidencias: el filtro Módulo 10 y el enmascarado se aplican antes de emitir.
- **R2 · Correlación.** Todo registro de una petición lleva el mismo `request_id` y la traza de Cloud Trace, y el `tenant_id` solo cuando la sesión lo resolvió.
- **R3 · Alertas con destino (`INV_OBS_SLO_UPTIME_AND_BUDGET_ALERTS`).** Ninguna política de alerta ni presupuesto queda sin canal de notificación.

## 4. Interfaz

Sin pantallas nuevas: la telemetría se consulta en la consola de Google Cloud. El consumo frente a los techos del paquete se muestra en el Orquestador (`BOV-04`).

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un registro emitido durante una petición con una cédula válida en el mensaje, **cuando** se formatea, **entonces** sale en JSON con `request_id` y la cédula aparece como `[CEDULA-REDACTADA]`. | `test_registro_json_redacta_datos_personales` |
| **Dado** el manifiesto `monitoreo_alertas.yaml`, **cuando** se inspecciona, **entonces** declara comprobaciones de disponibilidad, alertas de SLO y presupuestos, y cada uno tiene canal de notificación. | `test_manifiesto_alertas_completo` |

## 6. Trazabilidad

- PRD_EVYDENTIA_REVENTA_NUBE §5.4 pilar 10 y criterio 29; invariantes `INV_OBS_STRUCTURED_LOGS_NO_PERSONAL_DATA` e `INV_OBS_SLO_UPTIME_AND_BUDGET_ALERTS`.
