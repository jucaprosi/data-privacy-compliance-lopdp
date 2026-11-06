# Informe para el desarrollador: módulo Firma Electrónica

> **Estado a 2026-10-26.** Este informe se escribió con el módulo aún en boceto. Desde entonces se hicieron `FIRMA-03`, `FIRMA-04` y `FIRMA-05`, `FIRMA-06` está en curso y existen los routers `api/routers/firma_electronica.py` y `api/routers/firma_anf.py`: lo que dice abajo de que algo «no existe» ya no es cierto. Lee las secciones 2 y 3 junto con las fichas `governance/tareas/FIRMA-*.md`. El botón «Firma Electrónica» del encabezado sigue sin acción: `dashboard/page.tsx` no pasa todavía la prop `onFirmaElectronica`.

Fecha: 2026-10-26. Estado: el botón existe y no hace nada; el módulo no tiene código real.

## 1. Qué se pide

Un módulo cuyo único fin es **firmar cualquier PDF con firma electrónica**, enviando a terceros un enlace de firma, con multifirma y con los dos proveedores (sección 7). El acceso es el botón **Firma Electrónica** del encabezado del dashboard.

## 2. Dónde está tu punto de anclaje (ya hecho)

| Pieza | Archivo | Estado |
| :--- | :--- | :--- |
| Botón «Firma Electrónica» | `frontend/src/components/layout/DashboardHeader.tsx` (`data-testid="firma-electronica"`) | Listo, sin acción |
| Prop del botón | `onFirmaElectronica?: () => void` en `DashboardHeaderProps` | Opcional, nadie la pasa aún |
| Uso del encabezado | `frontend/src/app/dashboard/page.tsx` (render de `<DashboardHeader …/>`, hacia la línea 224) | Falta pasar la prop |

Este cambio sustituyó las etiquetas «Sin guardar» y «Workspace». No las repongas.

## 3. Qué ya existe en el repositorio

- **Sala backend (solo boceto):** `features/firma_electronica/`
  - `firma_electronica_service.py`: única compuerta pública. Define `FormatoFirma`, `EstadoFirma`, `ProveedorFirma`, `CertificadoInfo`, `DocumentoParaFirma`, `SesionFirmaPasarela`, `ResultadoFirma` y cuatro funciones `boceto_*` (firmar con ANF, abrir sesión de pasarela, verificar webhook HMAC, verificar firma). **Son simulaciones deterministas: no hacen llamadas de red.**
  - `domain/models.py`: solo `TransaccionFirmaBoceto`.
- **Diseño aprobado:** `governance/arquitectura/FIRMA_ELECTRONICA_BOCETO.md` (decisión D-4 y Aporte 111). Léelo entero antes de empezar: trae marco legal, flujos, custodia y riesgos.
- **Tarea cerrada:** `governance/tareas/FIRMA-01.md` (el boceto, estado `hecha`).
- **Lo que NO existe:** router en `api/routers/`, tablas y migración Alembic, cliente HTTP a los proveedores, vista en el frontend, pruebas.

## 4. Proveedores y modalidades

Radical (GRD Corporation) es la empresa; **UniverseID** es su producto «One-Shot Biometric» (modalidad pasarela). Los dos proveedores entran en la primera entrega.

| | Radical / UniverseID (pasarela one-shot) | ANF AC (STB directo) |
| :--- | :--- | :--- |
| Para quién | Firmante sin firma previa; prueba de vida, Registro Civil y certificado de un solo uso | Firmante con documento enviado por API, con coordenadas de estampado |
| Flujo | `POST /sessions` → `verification_url` → webhook `documents.signed` → descarga del PDF | WS1 STB v2: petición con el documento (Base64) y las coordenadas → PDF firmado con sello de tiempo TSA |
| Secretos | API key `dk_test_…` / `dk_live_…` y secreto de webhook `whsec_…` | Token STB de ANF |
| Especificación | `data/Guia_Integracion_OneShot_SMARTCIDI.pdf` (12-oct-2026) | Informe ANF «V1. Informe de entrega de STBS - SMARTCIDI» (15-oct-2026) |

### 4.1 Parámetros de Radical / UniverseID (según su guía)

| Parámetro | Valor del proveedor |
| :--- | :--- |
| Duración de la sesión (`verification_url`) | **10 minutos** desde que se crea. Después pasa a `expired` y hay que crear una sesión nueva |
| Certificado | De un solo uso, **24 horas**. Nunca llega a SMARTCIDI: se usa en sus servidores y se descarta |
| Descarga del PDF firmado | `signed_url` de descarga directa en el webhook. La guía no fija plazo: **descargar en cuanto llega el aviso** y guardarlo en nuestros sistemas |
| Documentos | **Plantillas** (PDF + posición del sello) cargadas en el panel de la organización; cada una tiene un `document_id`. `POST /sessions` recibe `document_ids` y responde 400 si alguno no existe |
| Firmante | Una persona por sesión: `cedula` (10 dígitos), `codigo_dactilar` (6+), `nombres`, `apellidos`, `email`. `return_url` obligatoria y `cancel_url` opcional |
| Webhook | Cuerpo con `signature` y cabeceras `X-Webhook-Signature`, `X-Webhook-Event`. La firma es SHA-256 hexadecimal del JSON **sin** el campo `signature` seguido del secreto `whsec_…`. Responder 2xx en pocos segundos; reintentan **hasta 3 veces**; el mismo aviso puede llegar repetido (deduplicar por `session_id`) |
| Documento fallido | Si un documento llega `failed`, el certificado ya se emitió: **no** crear sesión nueva; se reintenta desde el panel sin costo |
| Consulta de estado | `GET /sessions/{id}` (cada 3 s si hace falta); cancelar con `DELETE /sessions/{id}` |
| Errores | 410: sesión expirada. 5xx: reintentar con espera creciente (2, 4, 8 s) |
| Red | El webhook debe ser `https://` público; en desarrollo, túnel (ngrok o Cloudflare Tunnel) |
| Llamadas | Siempre desde el servidor; nunca desde el navegador |
| Aviso al titular | Informarle, antes de enviarlo al enlace, que se tratarán sus datos biométricos |
| Sandbox | Prueba de vida y Registro Civil simulados; el PDF sale firmado pero sin validez legal |

### 4.2 Parámetros de ANF (según `data/ANF.pdf`, «V1. Informe entrega de STBS - SMARTCIDI», 15-oct-2026)

| Parámetro | Valor del proveedor |
| :--- | :--- |
| Servicio | WS 1 v2: emisión de firma temporal, firmado de PDF, sello de tiempo y estampado múltiple en distintas hojas |
| Certificado | Firma electrónica **temporal de 24 horas** para persona natural; el firmante **no necesita firma previa** |
| Documento | PDF enviado en la petición, con o sin sello de tiempo |
| Firmantes | **Una firma por llamada.** Varios firmantes: una llamada independiente por cada uno |
| Estampado | Varias firmas visibles en un mismo PDF: coordenadas y página por cada estampado, más los datos del firmante, en el JSON |
| Validación del titular | **Validación biométrica obligatoria** (art. 17, Resolución ARCOTEL-2024-0176). La cédula es opcional (art. 24, Ley para la Optimización y Eficiencia de Trámites Administrativos); si no se envía copia o foto, la petición debe llevar un **documento de evidencia** que respalde la emisión |
| Configuración del titular | La petición que emite firma para el titular debe incluir su configuración; si falta, se rechaza |
| Testigos | Si se habilita el esquema de testigos (OTP o biometría), se exige al menos un testigo válido |
| Parámetro `CLIENTE` | Identifica al cliente de SMARTCIDI que pide la firma; por defecto `SMART-CIDI`. Sirve para el control comercial |
| Tiempo de respuesta | Máximo 90 s. Consultar 3 veces (a los 30, 60 y 90 s); después se considera error |
| Rechazo | Cualquier condición incumplida produce rechazo automático en la validación |
| Firma longeva | Debe estar cargada en el aplicativo TOC HEM |
| Ambientes | TEST y producción separados. En TEST no se emite firma: hay firmas precargadas que simulan el firmado |
| Credenciales | TEST entregadas por WhatsApp el 15-oct-2026. Producción: solo tras la aprobación de las pruebas por SMARTCIDI |

**Ficha técnica (endpoints, JSON, errores).** El PDF la enlaza en `http://documentacion-longeva.smartcidi.firmas-electronicas-293414.uc.r.appspot.com/`. Al consultarla, el certificado HTTPS de esa dirección no corresponde al dominio (subdominio de varios niveles bajo `*.uc.r.appspot.com`), así que no se pudo leer. Hay que pedirle a ANF la ficha en PDF o una URL con certificado válido. Mientras no esté, no se conocen endpoints, autenticación, formato de respuesta, códigos de error ni tamaño máximo del PDF.

**Por confirmar con ANF:** quién ejecuta la validación biométrica (ANF con su propia pantalla, o el integrador entregando la evidencia) y en qué formato se entrega.

## 5. Reglas que no se pueden saltar

1. **ADPA.** Todo el backend vive en `features/firma_electronica/`. Quien llame desde fuera (routers, otras salas) lo hace **solo** por `firma_electronica_service.py`. Prohibido importar `domain/*` desde fuera.
2. **Multi-tenant.** Toda estructura y toda llamada lleva `tenant_id`, con RLS en la base de datos.
3. **Webhook.** Verificar la firma del aviso según la sección 4.1 (no es un HMAC estándar) y comparar con `hmac.compare_digest`. Si no coincide, responder 401 sin guardar nada. Si el aviso ya se procesó, responder 2xx sin repetir el trabajo.
4. **Custodia.** Calcular `sha256_original` y `sha256_firmado`. Guardar el PDF en Cloudflare R2 (`tenants/{tenant_id}/firmas/{año}/{mes}/{firma_id}_{sha256}.pdf`) y registrar el evento `FIRMA_ELECTRONICA_COMPLETADA` en `audit_events`.
5. **Credenciales.** Nada de llaves en el repositorio. Solo variables de entorno, y el sistema debe arrancar sin ellas.
6. **Producción.** La firma real queda sujeta a la aprobación jurídica del propietario y a credenciales productivas de ANF y Radical. Trabaja contra el ambiente de pruebas.
7. **Interfaz.** Los tokens internos (`¤`, `¦`) no deben aparecer en ninguna pantalla ni texto de cara al usuario.
8. **Gobernanza.** Una tarea nueva por entrega, en `governance/tareas/FIRMA-NN.md` (mismo formato TOML que `FIRMA-01.md`: `propiedad`, `arbitro`, `rastros`), una rama por tarea, y registrada en `governance/artefactos/TASKS.md`. No toques archivos fuera de la `propiedad` de tu tarea.

## 6. Cableado del frontend (dónde enganchar)

1. Añadir `"firma_electronica"` a `VistaActiva` en `frontend/src/components/layout/dashboardNavigation.ts` **y** a `ActiveView` en `frontend/src/store/useAuditStore.ts` (hoy la conversión en `page.tsx` es un `as unknown as`).
2. Crear el componente en `frontend/src/components/firma_electronica/` y su cliente en `frontend/src/lib/firma_electronica/`.
3. Añadir la rama `vistaActiva === "firma_electronica"` en la cadena de render de `page.tsx` (hacia la línea 386–440).
4. Pasar `onFirmaElectronica={() => setVistaActiva("firma_electronica")}` al `DashboardHeader`.
5. Título del módulo: el encabezado ya muestra `workspaceTitle` (hacia la línea 227 de `page.tsx`); añade el caso para esta vista.

Si el módulo debe abrirse en un modal en lugar de una vista, el punto de anclaje es el mismo (la prop `onFirmaElectronica`).

## 7. Decisiones del propietario (2026-10-26)

Estas decisiones prevalecen sobre el boceto donde difieran.

| Tema | Decisión |
| :--- | :--- |
| Tiempos y descargas | **Los del proveedor** (sección 4.1): sesión de 10 minutos, certificado de 24 horas, descarga del PDF en cuanto llega el aviso. La plataforma no inventa plazos propios para el proveedor |
| Proveedores | **Ambos en la primera entrega:** Radical/UniverseID y ANF STB directo |
| Alcance | Se firma **cualquier PDF** que suba el usuario. Se construye |
| Firmantes | **Terceros por enlace.** Se construye |
| Multifirma | **Sí.** Se construye |
| Dispositivos | **Solo el recorrido del firmante es mobile-first** (celular y tablet). El dashboard sigue siendo de escritorio |

### 7.1 Cómo se construye cada punto con los parámetros del proveedor

**Terceros por enlace con una sesión de 10 minutos.** No envíes al tercero la `verification_url`: caduca en 10 minutos y casi nunca llegará a tiempo por correo. La plataforma envía su **propia invitación** (enlace de un solo uso, ligado al firmante y al documento). Al abrirla, el servidor crea en ese momento la sesión en Radical y redirige al tercero a la `verification_url`. Si la sesión expira (410 o `expired`), la invitación permite crear otra. Antes de redirigir, la invitación muestra el aviso de tratamiento de datos biométricos. El firmante no necesita cuenta en la plataforma. La vigencia de la invitación es una decisión de negocio que no fija el proveedor: el propietario debe definirla.

**Cualquier PDF.** En la plataforma: validar tipo MIME y cabecera `%PDF`, fijar un tamaño máximo y calcular `sha256_original` al subir.
- **ANF:** recibe el documento en la petición, así que cualquier PDF encaja de forma natural.
- **Radical/UniverseID:** **según su guía solo firma plantillas cargadas a mano en su panel.** La guía no documenta una API para subir un PDF por sesión. Antes de codificar, hay que preguntarle a Radical si existe esa API (o una para crear plantillas). Mientras no la haya, el PDF arbitrario se firma por ANF y Radical queda para las plantillas registradas.

**Multifirma.** El orden de los firmantes es secuencial y cada firma parte del PDF ya firmado por el anterior. Cada paso registra `sha256_original` y `sha256_firmado`.
- **ANF:** admite varios firmantes procesados uno a uno, conservando las firmas previas (boceto, sección 4.2).
- **Radical/UniverseID:** una sesión firma a **una** persona sobre una plantilla fija. La guía no explica cómo firmar encima de un PDF que ya trae una firma. Pregúntalo a Radical junto con lo anterior. Hasta tener respuesta, la multifirma va por ANF o por una cadena en la que Radical solo firma primero.

**Descarga.** Al llegar `documents.signed` se descarga cada `signed_url`, se calcula `sha256_firmado`, se guarda en R2 y se registra en `audit_events`. Los usuarios descargan siempre desde la plataforma, nunca desde la `signed_url` del proveedor.

**Celular o tablet con cámara (prueba de vida).** La prueba de vida necesita un dispositivo con cámara frontal. Según la guía de Radical, la pantalla de cámara **no es nuestra**: está alojada en `app.universe-id.com` (página `verification_url`), y el tercero llega a ella por redirección, enlace por correo o WhatsApp, o código QR. No hay que construir cámara, SDK ni motor de prueba de vida. Lo que sí hay que adaptar a celular y tablet es el **recorrido del firmante** en nuestra plataforma, no el dashboard entero:
- Página de invitación (la abre el tercero desde el correo o WhatsApp), con el aviso de tratamiento de datos biométricos y el botón para empezar. Diseño mobile-first: ancho de 360 px en adelante, botones táctiles, sin desplazamiento horizontal.
- Páginas de retorno (`return_url` y `cancel_url`) con el resultado: firmado, fallido o cancelado, y la opción de reintentar si la sesión expiró.
- Si la invitación se abre en un computador sin cámara, mostrar un **código QR** para continuar en el celular, con el mismo enlace de un solo uso.
- Esas páginas son públicas (sin sesión de la plataforma) y no deben cargar el layout del dashboard.
- Prueba obligatoria en Playwright con los perfiles de celular y tablet.

El dashboard (donde el usuario sube el PDF y define los firmantes) sigue siendo de escritorio, por decisión del propietario (2026-10-26). Queda fuera de este módulo.

### 7.2 Preguntas para Radical (antes de codificar su parte)

1. ¿Hay API para subir un PDF por sesión o para crear plantillas sin usar el panel?
2. ¿Puede una sesión firmar un PDF que ya trae firmas, conservándolas?
3. ¿Cuánto dura la `signed_url` de descarga?

## 8. Entregable y verificación

Cada tarea termina con su árbitro en verde: `pytest` de la sala, `npm run typecheck` y `npm run build` en el frontend, la suite completa y el arnés (`ejecutar_arnes_verificacion.bat`). Antes de sellar, cubre con pruebas el rechazo de un webhook con firma inválida y el aislamiento entre tenants.

## 9. Referencias

- `data/Guia_Integracion_OneShot_SMARTCIDI.pdf` (guía de integración One-Shot Biometric de UniverseID, 12-oct-2026)
- `governance/arquitectura/FIRMA_ELECTRONICA_BOCETO.md`
- `governance/tareas/FIRMA-01.md`
- `governance/artefactos/PRD.md` (sala `firma_electronica`, líneas 146, 226 y 297)
- Ley de Comercio Electrónico, Firmas Electrónicas y Mensajes de Datos (arts. 13 a 15, 17, 18 y 29 a 35) y su Reglamento, como cita el boceto. Contrasta cada artículo con el texto vigente antes de apoyarte en él.
