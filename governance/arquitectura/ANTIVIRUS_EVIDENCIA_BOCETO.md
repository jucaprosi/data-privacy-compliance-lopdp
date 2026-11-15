# Boceto Arquitectónico: Análisis antivirus de la evidencia (SEC-05)
`¤seguridad` `¤evidencias`

> **Estado:** Boceto (Fase BBAP, paso 1).  
> **Árbitro:** Aprobación del propietario. Sin proveedor real, sin credenciales y sin integrar ningún escáner.  
> **Fecha de verificación de las fuentes:** 2026-10-16. Lo que no se pudo comprobar figura como «no verificado».

---

## 1. Qué protege y qué no (hoy)

La evidencia sube directo del navegador a Cloud Storage (GCS) con una URL firmada V4; el servidor nunca ve los bytes. SEC-05 ya valida en el servidor, **antes** de la subida, el tipo MIME declarado, la extensión y el tamaño declarado (`app_core/storage/limites.py::motivo_de_rechazo`). Esa validación es declarativa: quien sube puede declarar `application/pdf` y enviar otra cosa. Por eso el análisis del contenido solo puede hacerse **después** de la subida.

Superficie que cubre un antivirus: documentos Office con macros o enlaces, PDF con scripts, archivos que otra persona del tenant descargará (validador, DPO, auditor).

## 2. Hechos verificados en documentación oficial

| Hecho | Fuente | Estado |
|---|---|---|
| Cloud Run: memoria configurable (hasta 32 GiB) y duración máxima de petición hasta 3600 s; en despliegue actual, timeout de 300 s. | cloud.google.com/run/docs/configuring/services/memory-limits | Verificado |
| Cloud Storage emite notificaciones `OBJECT_FINALIZE` hacia **Pub/Sub** / **Eventarc**, consumible por servicios HTTP en Cloud Run. | cloud.google.com/storage/docs/pubsub-notifications | Verificado |
| API pública de VirusTotal: 4 peticiones/minuto, 500/día, **prohibida en productos o servicios comerciales**. | docs.virustotal.com/reference/public-vs-premium-api | Verificado |
| Tamaño máximo de archivo de VirusTotal; tamaño y peso de la base de firmas de ClamAV; precios de escáneres de terceros distintos de VirusTotal. | — | **No verificado** |

## 3. Opciones

### A. Escáner externo por API (p. ej. VirusTotal premium u otro proveedor)
- **Cómo:** una notificación `OBJECT_FINALIZE` de GCS llega vía Pub/Sub / Eventarc; un consumidor pide una URL firmada V4 y envía el archivo al proveedor.
- **A favor:** sin infraestructura propia; las firmas las mantiene el proveedor.
- **En contra:** el archivo sale a un tercero (el contenido son evidencias de cumplimiento con posibles datos personales: exige base legal y contrato de encargo conforme a la LOPDP). La API pública de VirusTotal no sirve: su licencia excluye el uso comercial y 500 consultas/día es poco. Costo y límites del plan de pago: no verificado.

### B. ClamAV embebido en el contenedor principal de Cloud Run
- **Cómo:** empaquetar ClamAV y su base de firmas dentro de la imagen del servicio principal.
- **Análisis:** obliga al servicio de API a descargar el archivo desde GCS en cada subida o a cargar la base de firmas en memoria durante arranques en frío.
- **En contra:** acopla el escalado de la API al peso de la base de firmas y exige reconstruir ante cada actualización de firmas.

### C. Servicio dedicado en Cloud Run activado por Eventarc/Pub/Sub
- **Cómo:** `OBJECT_FINALIZE` → Eventarc/Pub/Sub → servicio Cloud Run aislado con ClamAV o escáner externo que descarga desde GCS y registra el resultado.
- **A favor:** desacoplado de la API transaccional y nativo en Google Cloud.
- **En contra:** incorpora un segundo servicio gestionado y su suscripción de eventos en Google Cloud.

## 4. Estado «pendiente de análisis» y cuarentena (independiente de la opción)

Sea cual sea el motor, el modelo debe tener un estado de análisis. Hoy `task_evidence.validation_status` cubre la validación humana (pending/approved/rejected), no el análisis del archivo. Propuesta:

1. Toda evidencia nace `analisis = pendiente` y **no se ofrece su descarga** a otros usuarios hasta pasar a `limpio`. Quien la subió puede ver que está en análisis.
2. `infectado` → cuarentena: el objeto se mueve a un prefijo no descargable, se notifica al encargado y queda en bitácora.
3. `error` o sin respuesta tras un plazo → permanece sin descarga y se reintenta; nunca se libera por defecto.

Esto **no está implementado**: exige una columna y una migración nuevas. SEC-05 no cambia el modelo de datos; si se aprueba, se propone como tarea aparte (sala `pasillo_central`, con su migración).

## 5. Recomendación

Primero la cuarentena (sección 4), porque es independiente del motor y protege desde el primer día. Después el motor por la opción C con un proveedor que cumpla el contrato de encargo; B solo si se acepta el costo de mantenimiento; A solo con plan comercial.

## 6. Decisiones que necesita el propietario

1. ¿Se aprueba un estado de análisis y cuarentena en el modelo de la evidencia (nueva tarea con migración)?
2. ¿Puede el contenido de las evidencias salir a un proveedor externo de análisis? Si sí, con qué base legal y contrato.
3. ¿Se aprueba un servicio dedicado en Cloud Run + Eventarc/Pub/Sub para análisis asíncrono o se prefiere escaneo bajo demanda?
4. ¿Qué plazo máximo de espera antes de marcar un análisis como fallido?
5. Verificar con el proveedor elegido: tamaño máximo de archivo, precio y límites de su plan de pago (hoy no verificados).
