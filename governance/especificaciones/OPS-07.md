# OPS-07 · Observabilidad sin datos personales
`¤sdd` `¤observabilidad` `¤seguridad-tenant` `¤cloud-run-perf`

## 1. Datos

Sin tablas. Cada entrada de registro es un objeto JSON en una línea:

`{"severity", "time", "request_id", "tenant_id", "user_id", "method", "path", "status", "duration_ms", "message"}`

`user_id` es el identificador interno; `path` va sin parámetros de consulta. Políticas de `governance/operaciones/monitoreo/alertas.yaml`:

| Política | Condición inicial |
| :--- | :--- |
| `disponibilidad` | `/health` falla 2 comprobaciones seguidas (cada 60 s) |
| `errores_5xx` | más del 2 % de respuestas 5xx en 5 minutos |
| `latencia_p95` | p95 mayor que 1500 ms durante 10 minutos |
| `presupuesto` | gasto mensual al 50, 90 y 100 % del presupuesto |
| `gasto_ia` | gasto diario de Vertex AI mayor que el tope fijado por el propietario |

## 2. API

- Toda respuesta lleva `X-Request-ID`; si la petición ya trae uno válido (UUID), se conserva.
- Sin rutas nuevas.

## 3. Reglas

- **R1 · Sin datos personales en el registro.** Todo `message` y toda traza pasan por `app_core/dlp_sanitizer.py` antes de escribirse (LOPDP, principio de minimización).
- **R2 · Correlación.** Todas las entradas de una petición comparten su `request_id`.
- **R3 · Sin consulta ni cuerpo.** No se registran parámetros de consulta, cuerpos de petición ni cabeceras de autorización.
- **R4 · Alertas como código.** Las cinco políticas viven en `alertas.yaml`; ninguna se crea solo a mano en la consola.

## 4. Interfaz

Sin pantalla de usuario. La guía `OBSERVABILIDAD.md` es para quien opera la plataforma.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un mensaje de error que contiene una cédula válida y un correo, **cuando** se registra, **entonces** la línea escrita no contiene ninguno de los dos. | `test_registro_sin_datos_personales` |
| **Dado** una excepción cuya traza incluye un teléfono, **cuando** se captura, **entonces** la traza registrada está saneada y conserva el tipo de error. | `test_traza_saneada` |
| **Dado** una petición sin `X-Request-ID`, **cuando** se responde, **entonces** la respuesta trae uno y todas las líneas de esa petición lo repiten. | `test_request_id_propagado` |
| **Dado** una petición con `?correo=x@y.ec`, **cuando** se registra, **entonces** `path` no lleva la consulta. | `test_path_sin_consulta` |
| **Dado** `alertas.yaml`, **cuando** se lee, **entonces** declara las cinco políticas con su condición. | `test_alertas_declaradas` |

## 6. Trazabilidad

- `PRD.md` §1 ley 8 (minimización) y §5.3 (Cloud Run); requisito 10 de la revisión del 2026-11-04.
