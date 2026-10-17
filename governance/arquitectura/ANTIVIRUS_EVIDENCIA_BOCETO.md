# Boceto Arquitectónico: Análisis antivirus de la evidencia (SEC-05)
`¤seguridad` `¤evidencias`

> **Estado:** Boceto (Fase BBAP, paso 1).  
> **Árbitro:** Aprobación del propietario. Sin proveedor real, sin credenciales y sin integrar ningún escáner.  
> **Fecha de verificación de las fuentes:** 2026-10-16. Lo que no se pudo comprobar figura como «no verificado».

---

## 1. Qué protege y qué no (hoy)

La evidencia sube directo del navegador a Cloudflare R2 con una URL prefirmada; el servidor nunca ve los bytes. SEC-05 ya valida en el servidor, **antes** de la subida, el tipo MIME declarado, la extensión y el tamaño declarado (`app_core/storage/r2.py::motivo_de_rechazo`). Esa validación es declarativa: quien sube puede declarar `application/pdf` y enviar otra cosa. Por eso el análisis del contenido solo puede hacerse **después** de la subida.

Superficie que cubre un antivirus: documentos Office con macros o enlaces, PDF con scripts, archivos que otra persona del tenant descargará (validador, DPO, auditor).

## 2. Hechos verificados en documentación oficial

| Hecho | Fuente | Estado |
|---|---|---|
| Funciones de Vercel: tamaño máximo sin comprimir 250 MB; **500 MB para Python**; hasta 5 GB en «large functions» (beta). | vercel.com/docs/functions/limitations (actualizada 2026-08-24) | Verificado |
| Memoria máxima: Hobby 2 GB / Pro 4 GB. Duración máxima: Hobby 300 s; Pro 800 s. | idem | Verificado |
| Cuerpo de petición o respuesta de una función: máximo **4,5 MB** (error 413). | idem | Verificado |
| R2 emite notificaciones `object-create` y `object-delete` hacia una **Cloudflare Queue**, consumible por un Worker o por HTTP; admite filtro por prefijo y sufijo; hasta 100 reglas por bucket. | developers.cloudflare.com/r2/buckets/event-notifications | Verificado. La página no dice si es GA o beta ni da precio. |
| Queues está en el plan Workers Free: 10 000 operaciones/día y retención de 24 h. En el plan de pago: 1 000 000 operaciones/mes y luego 0,40 USD por millón. Un mensaje consume unas 3 operaciones. | developers.cloudflare.com/queues/platform/pricing | Verificado |
| API pública de VirusTotal: 4 peticiones/minuto, 500/día, **prohibida en productos o servicios comerciales**. | docs.virustotal.com/reference/public-vs-premium-api | Verificado |
| Tamaño máximo de archivo de VirusTotal; tamaño y peso de la base de firmas de ClamAV; precios de escáneres de terceros distintos de VirusTotal. | — | **No verificado** |

## 3. Opciones

### A. Escáner externo por API (p. ej. VirusTotal premium u otro proveedor)
- **Cómo:** una notificación de R2 llega a una cola; un consumidor pide la descarga prefirmada y envía el archivo al proveedor.
- **A favor:** sin infraestructura propia; las firmas las mantiene el proveedor.
- **En contra:** el archivo sale a un tercero (el contenido son evidencias de cumplimiento con posibles datos personales: exige base legal y contrato de encargo conforme a la LOPDP). La API pública de VirusTotal no sirve: su licencia excluye el uso comercial y 500 consultas/día es poco. Costo y límites del plan de pago: no verificado.

### B. ClamAV propio dentro de una función de Vercel
- **Cómo:** empaquetar ClamAV y su base de firmas en una función Python.
- **Lo verificado:** el límite de 500 MB sin comprimir para Python y los 4,5 MB de cuerpo hacen viable el paquete solo si la base de firmas cabe (peso de la base: no verificado) y obligan a que la función descargue el archivo desde R2, no a recibirlo por petición. Las funciones no son procesos de larga vida: cada arranque en frío cargaría la base de firmas.
- **En contra:** mantener las firmas al día exige reconstruir y desplegar. No lo recomiendo en el plan actual.

### C. Worker/consumidor de Cloudflare + escáner (propio o de tercero)
- **Cómo:** `object-create` → Queue → consumidor que descarga y llama al motor de análisis, y marca el resultado.
- **A favor:** el evento nace donde está el archivo; no pasa por Vercel.
- **En contra:** nueva pieza operativa fuera del repositorio; el límite de 10 000 operaciones/día del plan gratuito de Queues (unos 3 000 archivos/día a 3 operaciones por mensaje) es holgado para el uso previsto pero hay que vigilarlo.

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
3. ¿Se acepta nueva infraestructura en Cloudflare (cola y consumidor) o se prefiere mantener todo en Vercel?
4. ¿Qué plazo máximo de espera antes de marcar un análisis como fallido?
5. Verificar con el proveedor elegido: tamaño máximo de archivo, precio y límites de su plan de pago (hoy no verificados).
