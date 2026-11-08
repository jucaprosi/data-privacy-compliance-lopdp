# Observabilidad de la plataforma (OPS-07)
`¤observabilidad` `¤seguridad-tenant` `¤cloud-run-perf`

Guía para quien opera la plataforma. Contrato: `governance/especificaciones/OPS-07.md`.

## 1. Registro

Cada línea que escribe la API es un objeto JSON que Cloud Logging lee tal cual:
`severity`, `time`, `request_id`, `tenant_id`, `user_id` (identificador interno, nunca el correo), `method`, `path` (sin consulta), `status`, `duration_ms` y `message`.

- Antes de escribirse, todo mensaje y toda traza pasan por el saneador DLP (`app_core/dlp_sanitizer.py`), y además se ocultan los RUC. En el registro no aparecen cédulas, RUC, correos ni teléfonos.
- No se registran parámetros de consulta, cuerpos de petición ni cabeceras de autorización.
- Los errores no controlados se escriben con `@type` de Error Reporting y la traza saneada. El cliente recibe un 500 genérico con su `request_id`.
- Toda respuesta lleva `X-Request-ID`. Si la petición trae un UUID válido, se conserva.

## 2. Alertas

Las políticas están en `governance/operaciones/monitoreo/alertas.yaml`. Las crea el propietario, y ninguna se crea solo a mano.

| Política | Cuándo avisa | A quién |
| :--- | :--- | :--- |
| `disponibilidad` | `/health` falla 2 comprobaciones seguidas (cada 60 s) | Propietario (correo) |
| `errores_5xx` | Más del 2 % de respuestas 5xx en 5 minutos | Propietario |
| `latencia_p95` | p95 mayor que 1500 ms durante 10 minutos | Propietario |
| `presupuesto` | Gasto mensual al 50, 90 y 100 % | Propietario |
| `gasto_ia` | Gasto diario de Vertex AI mayor que el tope | Propietario |

## 3. Cómo leer un incidente

1. Abre la alerta y anota la hora.
2. En Error Reporting, busca el grupo del error y copia un `request_id`.
3. En el Explorador de registros, filtra `jsonPayload.request_id="<id>"`: verás todas las líneas de esa petición.
4. Con `tenant_id` sabrás si afecta a una organización o a todas.
5. Si la alerta es de `disponibilidad`, el cuerpo de `/health` lista los routers fallidos.

## 4. Conservación

Los registros se conservan 30 días, el período por defecto de Cloud Logging. No son evidencia probatoria: la evidencia va a la Bóveda.
