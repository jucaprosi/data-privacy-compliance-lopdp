# Brief del propietario · DLP-01 · Encender Sensitive Data Protection (Cloud DLP)

Estado: **el adaptador real no existe todavía y la sala falla cerrada** (503 `DLP_ADAPTADOR_DESACTIVADO`). Este brief reúne lo que el propietario decide antes de que una ficha posterior entregue el adaptador. Ninguna IA ejecuta cambios en Google Cloud: los comandos de abajo son de lectura o los ejecuta el propietario (o Antigravity con este brief).

## 1. Qué saldría de la plataforma

Al escanear, las filas de la muestra (hasta 1000 por escaneo, con un tope de 2 MiB por solicitud) se envían a la API `dlp.googleapis.com` para detectar correos, teléfonos y posibles datos de salud. Las cédulas y los RUC se validan dentro de la plataforma (Módulo 10) y no necesitan el servicio. La muestra puede contener **datos sensibles** (salud). La plataforma guarda solo los tipos y los conteos; Google procesa el contenido.

## 2. Decisión 1 · Región del procesamiento

| Opción | Qué implica | Encuadre legal |
| :--- | :--- | :--- |
| **A · `us-central1`**, la misma de Cloud Run, Cloud SQL y Vertex AI | Una sola región para toda la plataforma; los datos de la muestra se procesan en Estados Unidos, como ya ocurre con la base y los documentos. | Transferencia internacional (LOPDP, arts. 55 a 61). **Pendiente de verificar** por el abogado: el mecanismo aplicable (nivel adecuado, art. 56; garantías adecuadas, art. 57; o autorización, art. 59). |
| **B · Otra región** (p. ej. `southamerica-east1`, São Paulo) | La muestra sale hacia otra región distinta de la base; añade una ubicación más que declarar y vigilar. | También es transferencia internacional (Ecuador no tiene región de Google Cloud). **Pendiente de verificar**: que Sensitive Data Protection admita esa región para `content:inspect` y si Brasil tiene resolución de nivel adecuado de la Autoridad. |

Recomendación técnica (no legal): **A**, para no añadir una ubicación nueva; el encuadre legal es el mismo dictamen pendiente de la base y los documentos.

## 3. Decisión 2 · Encargo del tratamiento

Google actúa como encargado del tratamiento al procesar la muestra. **Pendiente de verificar** por el abogado: si los términos de tratamiento de datos de Google Cloud que ya rigen la cuenta cubren Sensitive Data Protection y bastan como contrato de encargo, y cómo se registra la transferencia en el Registro Nacional.

## 4. Citas legales (de `governance/apoyo/CITAS_LEGALES_VERIFICADAS.md`)

- LOPDP, arts. 55 a 61: transferencia o comunicación internacional; art. 56, países con nivel adecuado; art. 57, garantías adecuadas; art. 58, normas corporativas vinculantes; art. 59, autorización; art. 60, casos excepcionales; art. 61, control continuo. Estado en el registro: verificado.
- Reglamento General, art. 71: la Autoridad declara los países con nivel adecuado y esa transferencia no requiere autorización previa. Verificado.
- Reglamento General, art. 74: instrumentos de garantías adecuadas para países sin nivel adecuado. Verificado.
- Reglamento General, art. 77: autorización previa en los casos no contemplados. Verificado.
- Reglamento General, art. 78: registro de las transferencias internacionales (país, categorías de datos, finalidades, destinatario, mecanismo). Verificado.

Lo que no está en el registro queda **pendiente de verificar**: si existe hoy una resolución de nivel adecuado para Estados Unidos o Brasil.

## 5. Costo estimado

**Pendiente de verificar** en la página oficial de precios de Sensitive Data Protection (`https://cloud.google.com/sensitive-data-protection/pricing`): el método `content:inspect` se cobra por volumen de bytes inspeccionados, con un tramo mensual gratuito. Con el tope de la sala (2 MiB por escaneo), el costo por escaneo es muy bajo; el número exacto por GB y el tramo gratuito se copian de esa página al decidir.

## 6. Comandos de lectura (PowerShell, pegables)

```powershell
$PROYECTO = "evydentia"
gcloud services list --enabled --project=$PROYECTO --filter="name:dlp.googleapis.com"
gcloud sql instances list --project=$PROYECTO --format="table(name,region,state)"
```

## 7. Lo que hará la ficha siguiente, tras las dos decisiones

1. El propietario activa la API y concede a la cuenta de servicio de Cloud Run el rol mínimo de uso de Sensitive Data Protection, en la región elegida.
2. Una ficha nueva entrega el adaptador real detrás del puerto `ClienteDlp`, fijado a esa región y sin registrar el contenido. Hasta entonces la pantalla responde con el aviso de servicio no habilitado.
