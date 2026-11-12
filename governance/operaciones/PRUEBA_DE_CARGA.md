# Prueba de carga y escalado de Cloud Run (GCP-05)

Esta guía fija los límites de escalado de EVYDENTIA, cómo se comprueban y cómo se mide que la plataforma escala. La prueba de carga corre **solo contra el entorno de pruebas**, nunca contra producción.

## 1. Límites de escalado

| Servicio | Mínimo | Máximo | Concurrencia | Archivo |
| :--- | :--- | :--- | :--- | :--- |
| Backend (`evydentia-backend`) | 1 en producción, 0 en pruebas | 10 | 80 | `cloudrun_service.yaml` |
| Frontend de producción (`evydentia-web`) | 0 | 5 | 80 | `cloudrun_frontend_service.yaml` |
| Frontend de pruebas y demo | 0 | 2 | 80 | `cloudrun_frontend_service.yaml` |

- El mínimo de 1 instancia del backend en producción evita el arranque en frío del primer usuario y cuesta una instancia permanente.
- **El máximo de instancias también es el tope de gasto.** El propietario los ajusta; la prueba `tests/test_gcp05_escalado.py` impide que un cambio los saque de la tabla sin que alguien lo decida.

## 2. Presupuesto de conexiones

El backend abre conexiones a PostgreSQL desde cada instancia. A plena escala:

`maxScale × (pool_size + max_overflow) ≤ conexiones que admite la base`

Las tres cifras están en el manifiesto del backend, como anotaciones `evydentia.com/pool-size`, `evydentia.com/max-overflow` y `evydentia.com/conexiones-base`. `tests/test_gcp05_escalado.py` hace la cuenta y falla si no cabe.

> **Pendiente del propietario.** `evydentia.com/conexiones-base` es una cifra provisional (100). El propietario debe confirmarla con el límite real de la instancia: `gcloud sql instances describe evydentia-production --format="value(settings.databaseFlags)"` (lectura) y, si el pooler es el administrado de Cloud SQL, su tamaño de pool. Si el valor real es menor, hay que bajar `maxScale` o el pool, y la prueba lo exigirá.

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

Salida: 0 meta cumplida, 1 meta no cumplida, 2 no se pudo correr. El token, si se usa, se lee de la variable de entorno y nunca se imprime. El script no lee ningún `.env`.

Para que la medición tenga sentido, `--rutas` debe incluir rutas de lectura **autenticadas** con datos del usuario de prueba (por ejemplo, el listado de organizaciones o de actividades del RAT), no solo las de salud.

### Qué mirar mientras corre (lectura, en Cloud Monitoring)

- Instancias activas del backend (`run.googleapis.com/container/instance_count`): debe subir hasta el máximo sin pasarlo.
- Conexiones activas a la base: no debe superar `conexiones-base`.
- Latencia y 5xx del balanceador.

## 4. Informe de corridas

Cada corrida real se anota aquí con fecha, entorno, configuración y resultado.

| Fecha | Entorno | Usuarios | Duración | p50 | p95 | p99 | 5xx | Meta |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| — | — | — | — | — | — | — | — | **Sin corrida real todavía** |

**Estado.** No se ha ejecutado ninguna corrida contra el entorno de pruebas. El entorno de pruebas aún no se pone en marcha (`EP-09`, pendiente) y esta ficha no tiene credenciales ni despliega nada en Google Cloud. Las pruebas automáticas (`tests/test_gcp05_escalado.py`) verifican el script contra un servidor simulado en la máquina local; eso **no** demuestra la meta. La primera corrida real queda para el propietario, con el comando de la sección 3, y su resultado se anota en la tabla anterior.

## 5. Brief para el propietario (con Antigravity)

Nada de esto lo aplica una IA.

1. Aplicar los manifiestos con los nuevos límites: `gcloud run services replace governance/operaciones/cloudrun_service.yaml` y lo mismo con el del frontend (mínimo 1 en el backend de producción; máximo 5 en el frontend de producción).
2. Confirmar `evydentia.com/conexiones-base` con el límite real de la base (sección 2) y avisar si difiere.
3. **`deploy-gcp.yml` contradice la tabla.** El despliegue del backend pasa `--min-instances 0` y `--max-instances 5` (líneas 67 y 68), así que cada publicación desde el workflow reemplazaría los límites del manifiesto. El workflow es de gobernanza reservada y esta ficha no lo toca. Parche para el propietario: cambiar a `--min-instances 1` y `--max-instances 10`, y añadir `--concurrency 80`.
4. Cuando el entorno de pruebas exista, correr la prueba de la sección 3 y anotar el resultado en la sección 4.
