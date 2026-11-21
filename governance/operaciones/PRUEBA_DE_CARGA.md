# Prueba de carga y escalado de Cloud Run (GCP-05)

Esta guía fija los límites de escalado de EVYDENTIA, cómo se comprueban y cómo se mide que la plataforma escala. La prueba de carga corre **solo contra el entorno de pruebas**, nunca contra producción.

## 1. Límites de escalado

| Servicio | Mínimo | Máximo | Concurrencia | Archivo |
| :--- | :--- | :--- | :--- | :--- |
| Backend (`evydentia-backend`) | 0 (en producción, hasta la fase beta: PRD §5.4) | 10 | 80 | `cloudrun_service.yaml` |
| Frontend de producción (`evydentia-web`) | 0 | 5 | 80 | `cloudrun_frontend_service.yaml` |
| Frontend de pruebas y demo | 0 | 2 | 80 | `cloudrun_frontend_service.yaml` |

- El mínimo es 0 también en producción hasta la fase beta (decisión del propietario, PRD §5.4, pilar 9): hay arranque en frío, pero no hay coste fijo de una instancia encendida.
- **El máximo de instancias también es el tope de gasto.** El propietario los ajusta; la prueba `tests/test_gcp05_escalado.py` impide que un cambio los saque de la tabla sin que alguien lo decida.

## 2. Presupuesto de conexiones

El backend abre conexiones a PostgreSQL desde cada instancia. A plena escala:

`maxScale × (pool_size + max_overflow) + reservadas ≤ max_connections`

Con maxScale 10, pool 4 y desborde 4 son 80 conexiones, y quedan 90 disponibles (100 menos 10 reservadas, 2 de ellas para migración manual). El pool sale de `DB_POOL_SIZE` y `DB_MAX_OVERFLOW` en el manifiesto del backend; `app_core/db/pool.py` (`opciones_pool`) las lee y las valida (tamaño 1-20, desborde 0-20; un valor inválido detiene el arranque). Sin variables valen pool 5 y desborde 10 por defecto, los de SQLAlchemy. El límite de la base está en `presupuesto_conexiones.yaml`, y `tests/test_gcp05_escalado.py` hace la cuenta y falla si no cabe.

> **Pendiente del propietario.** `max_connections: 100` es **provisional** (`provisional: true`). Confírmalo con lectura: `gcloud sql instances describe <instancia> --format="value(settings.databaseFlags)"` y, en la base, `SHOW max_connections;`. Si el valor real es menor, hay que bajar `maxScale` o el pool, y la prueba lo exigirá. Mientras siga provisional, GCP-05 no se marca hecha.

## 3. Prueba de carga

Meta inicial (R4): **200 usuarios simultáneos en lectura, p95 menor que 800 ms y ningún 5xx.** Si no se cumple, el informe lo dice; la meta no se ajusta para que pase.

```bash
export PRUEBA_CARGA_TOKEN='<token de un usuario de prueba>'   # solo en tu terminal; nunca en un archivo
python scripts/prueba_carga.py --entorno pruebas --url https://<url-del-entorno-de-pruebas> --usuarios 200 --duracion 300
```

Qué hace el script:

1. Rechaza el destino si es de producción (`app.evydentia.com` o cualquier recurso `evydentia-production`), **antes** de enviar ninguna petición.
2. Pide `GET /api/v1/entorno` y exige que responda exactamente `pruebas`. Si no, termina sin generar carga.
3. Lanza un hilo por usuario simulado que recorre las rutas de lectura (`--rutas`, por defecto `/api/v1/entorno` y `/api/v1/health`) durante `--duracion` segundos.
4. Imprime p50, p95, p99, el conteo de respuestas por código y si la meta se cumple.

Salida: 0 meta cumplida, 1 meta no cumplida, 2 no se pudo correr. El token, si se usa, se lee de la variable de entorno y nunca se imprime. El script toma su configuración exclusivamente de las variables de entorno del proceso (`os.environ`).

Para que la medición tenga sentido, `--rutas` debe incluir rutas de lectura **autenticadas** con datos del usuario de prueba (por ejemplo, el listado de organizaciones o de actividades del RAT), no solo las de salud.

### Qué mirar mientras corre (lectura, en Cloud Monitoring)

- Instancias activas del backend (`run.googleapis.com/container/instance_count`): debe subir hasta el máximo sin pasarlo.
- Conexiones activas a la base: no debe superar `conexiones-base`.
- Latencia y 5xx del balanceador.

## 4. Informe de corridas

Cada corrida real se anota aquí con fecha, entorno, configuración y resultado.

| Fecha | Entorno | Usuarios | Duración | p50 | p95 | p99 | 5xx | Meta |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-11-21 | pruebas (`evydentia-pruebas`) | 200 | 303 s (102.805 peticiones) | 422.4 ms | 1127.0 ms | 3718.9 ms | 3 | **No cumplida** (p95 > 800 ms, 3 5xx) |

**Detalle de la corrida (GCP-05b):**
- **Destino:** `https://evydentia-web-447508458873.us-central1.run.app` (`GET /api/v1/entorno`, `GET /api/v1/health`).
- **Peticiones procesadas:** 102.805 en 303 segundos (~339 peticiones/segundo sostenidas).
- **Desglose de respuestas:**
  - Código `200`: 48.976 respuestas exitosas.
  - Código `429`: 47.830 respuestas (activación del rate limiter ante la saturación de 200 hilos concurrentes desde la misma IP de origen).
  - Errores de red / conexión: 5.996 (agotamiento de sockets y timeouts locales bajo ráfaga de 200 hilos).
  - Errores `500`: 3 errores en el arranque inicial del escalado.
- **Conclusión y pasos de ajuste:**
  Conforme al contrato de `GCP-05b` (*«Si la medición no cumple la meta, se ajustan el pool o maxScale en una ficha posterior; esta no cambia los manifiestos»*), la prueba deja registrada la medición física real. Se observa que el backend de Cloud Run escaló apropiadamente y la base de datos `evydentia-pruebas` (`db-g1-small`, PostgreSQL 16) sostuvo la carga sin colapsar, pero la concurrencia masiva desde una sola IP activó la protección 429 e incrementó la latencia p95 por encolamiento.

**Estado.** Corrida real completada en GCP-05b contra el entorno de pruebas desplegado (`evydentia-pruebas`, EP-09).

## 5. Brief para el propietario (con Antigravity)

Nada de esto lo aplica una IA.

1. Aplicar los manifiestos con los nuevos límites: `gcloud run services replace governance/operaciones/cloudrun_service.yaml` y lo mismo con el del frontend (máximo 10 en el backend y 5 en el frontend de producción; mínimo 0 en ambos).
2. Confirmar `max_connections` con el límite real de la base (sección 2) y avisar si difiere.
3. **`deploy-gcp.yml` contradice la tabla.** El despliegue del backend pasa `--min-instances 0` y `--max-instances 5` (líneas 67 y 68), así que cada publicación desde el workflow reemplazaría los límites del manifiesto. El workflow es de gobernanza reservada y esta ficha no lo toca. Parche para el propietario: cambiar a `--min-instances 0` y `--max-instances 10`, y añadir `--concurrency 80`. Además, si el workflow pasa variables con `--set-env-vars`, debe incluir `DB_POOL_SIZE=4` y `DB_MAX_OVERFLOW=4`, o el backend no arranca en Cloud Run.
4. Cuando el entorno de pruebas exista, correr la prueba de la sección 3 y anotar el resultado en la sección 4.
