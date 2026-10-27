# BIBLIOTECA de EVYDENTIA — PMV para pequeñas empresas privadas (LOPDP)

> Estado: borrador de especificación, 2026-10-27. Sin código de funcionalidades.
> Las referencias normativas se marcan **POR VERIFICAR** hasta cotejarlas con el texto oficial
> (LOPDP, Quinto Suplemento RO Nº 459, 26-05-2021; Reglamento, DE 904, Tercer Suplemento RO Nº 435,
> 13-11-2023; resoluciones de la SPDP).

## 0. Decisiones de partida

- Menú **BIBLIOTECA** con dos pestañas:
  - **Documentos de la organización** (vista principal). Cada documento lleva su etiqueta de origen: *basado en plantilla*, *propio* o *subido*.
  - **Plantillas**. Catálogo con las plantillas SMARTCIDI (solo lectura) y «Mi plantilla» del DPO. Acción principal: **Usar en esta organización**.
- Botón fijo **Biblioteca** en el lado derecho de la barra superior, en todas las pantallas. Abre un panel lateral derecho con las mismas dos pestañas y el enlace **Abrir en pantalla completa**.
- El backend tiene dos capas: **Plantilla** (versionada; publicar crea una versión nueva y nunca sobrescribe) y **Documento** (una instancia por organización).
- Editar una plantilla SMARTCIDI siempre crea una copia. Un usuario nunca ve documentos de otra organización.
- Se trabaja documento por documento, de punta a punta: contenido → backend → frontend → verificación.

### Códigos de documento y códigos de tarea

Los códigos `BIB-001`…`BIB-012` identifican **documentos del catálogo**. Las fichas de tarea de gobernanza usan `BIB-101`…`BIB-307` (`governance/tareas/`). Los rangos no se solapan, pero en commits y PR hay que escribir siempre «documento BIB-00X» o «tarea BIB-1XX».

## a) Convención de variables

### Sintaxis

- Formato `{{ambito.campo}}`: minúsculas, `snake_case`, un solo punto. Sin espacios dentro de las llaves.
- Ámbitos admitidos: `organizacion`, `representante`, `dpo`, `documento`, `tratamiento` y `contexto`.
- Fechas en ISO (`AAAA-MM-DD`). El frontend las muestra en formato local.
- Una variable sin valor no se borra: el borrador muestra `⟦falta: organizacion.direccion⟧` y el documento no puede pasar a *en revisión* mientras quede alguna.
- Las variables propias de un solo documento (por ejemplo, las finalidades) usan el ámbito `contexto` y se declaran en los metadatos de la plantilla. Hasta que esto se apruebe, ninguna plantilla puede inventar un ámbito nuevo.
- Las plantillas del kit v1 (DOCX/XLSX) usan otra convención, `{{MAYUSCULAS}}` (por ejemplo, EIPD-00). No se tocan: siguen su propio flujo editorial. La convención de este documento rige solo para las plantillas en Markdown del PMV.

### Lista inicial

Columna «Fuente actual»: ✅ el campo ya existe; ➕ hay que crearlo; ✍ lo captura el usuario en el borrador.

| Variable | Significado | Fuente actual |
|---|---|---|
| `{{organizacion.razon_social}}` | Razón social | ✅ `tenants.razon_social` |
| `{{organizacion.nombre_comercial}}` | Nombre comercial | ✅ `tenants.nombre_comercial` |
| `{{organizacion.ruc}}` | RUC | ✅ `tenants.ruc_identificacion` |
| `{{organizacion.sector}}` | Sector | ✅ `tenants.sector` |
| `{{organizacion.tamano}}` | Tamaño de empresa | ✅ `tenants.tamano` |
| `{{organizacion.direccion}}` | Domicilio principal | ➕ `tenants.direccion` |
| `{{organizacion.ciudad}}` | Ciudad | ➕ `tenants.ciudad` |
| `{{organizacion.telefono}}` | Teléfono de contacto | ➕ `tenants.telefono` |
| `{{organizacion.correo_contacto}}` | Correo general de contacto | ➕ `tenants.correo_contacto` |
| `{{organizacion.correo_privacidad}}` | Canal para solicitudes de titulares | ➕ `tenants.correo_privacidad` |
| `{{organizacion.sitio_web}}` | Sitio web | ➕ `tenants.sitio_web` |
| `{{representante.nombre}}` | Representante legal | ➕ `tenants.representante_legal_nombre` |
| `{{representante.identificacion}}` | Cédula del representante legal | ➕ `tenants.representante_legal_identificacion` |
| `{{representante.cargo}}` | Cargo del representante legal | ➕ `tenants.representante_legal_cargo` |
| `{{dpo.nombre}}` | Delegado de protección de datos (DPD) | ✅ `designaciones_formales` (tipo `dpd`, vigente) → `users` |
| `{{dpo.correo}}` | Correo del DPD | ✅ `users.email` del DPD designado |
| `{{dpo.fecha_designacion}}` | Fecha de designación | ✅ `designaciones_formales.fecha_designacion` |
| `{{documento.codigo}}` | Código del documento (BIB-00X) | ✅ plantilla |
| `{{documento.nombre}}` | Nombre del documento | ✅ plantilla |
| `{{documento.version}}` | Versión de la plantilla de origen | ✅ plantilla |
| `{{fecha_emision}}` | Fecha de emisión del documento | ✍ al crear (por defecto, hoy) |
| `{{documento.proxima_revision}}` | Fecha de la próxima revisión | ✍ (por defecto, emisión + 12 meses) |
| `{{documento.aprobado_por}}` | Quien aprobó | ✅ al aprobar |
| `{{documento.fecha_aprobacion}}` | Fecha de aprobación | ✅ al aprobar |
| `{{tratamiento.finalidades}}` | Finalidades del tratamiento | ✍ (en el futuro, desde el RAT) |
| `{{tratamiento.categorias_datos}}` | Categorías de datos tratados | ✍ (en el futuro, desde el RAT) |
| `{{tratamiento.plazo_conservacion}}` | Plazo de conservación | ✍ |
| `{{tratamiento.destinatarios}}` | Destinatarios o encargados | ✍ |

`{{fecha_emision}}` se mantiene sin ámbito porque así se acordó. Es la única excepción a la regla del punto.

Si el DPD no está designado, `dpo.*` aparece como «falta» y el aviso remite a **Cockpit DPD / DPO**.

## b) Formato estándar de una plantilla

### Ubicación en el repositorio

```
data/biblioteca/pmv/
  BIB-001.md        # una plantilla por archivo: metadatos + cuerpo
  BIB-002.md
  ...
```

- `data/biblioteca/pmv/` es la fuente editorial versionada en Git. Que un archivo esté en el repo no lo publica: entra en el catálogo por el flujo editorial existente (versión *en revisión* → revisión técnica y jurídica → publicar).
- Ninguna plantilla se publica sin la aprobación individual de la propietaria.
- No se mezcla con `data/biblioteca/kit_v1/`: los originales del kit no se editan.

### Estructura del archivo

Cada archivo tiene metadatos en YAML entre `---` y, después, el cuerpo en Markdown.

```markdown
---
codigo: BIB-001
nombre: Política de protección de datos personales
tipo: politica            # politica | aviso | formulario | acuerdo | contrato | registro | procedimiento | protocolo | modelo
ola: 1
sector: general           # general | <sector concreto>
naturaleza: privada       # publica | privada | ambas
tamano_empresa: [micro, pequena]
version: 0.1.0            # semver; cada publicación crea una versión nueva
base_lopdp: POR VERIFICAR # artículos y normas, solo con fuente oficial cotejada
validacion_legal: pendiente   # pendiente | en_revision | validada | con_observaciones
fecha_corte_normativo: 2026-10-27
variables_contexto:       # variables `contexto.*` propias de este documento
  - clave: contexto.canal_solicitudes
    etiqueta: Canal para recibir solicitudes
    obligatoria: true
revision_meses: 12
---

# Política de protección de datos personales de {{organizacion.razon_social}}

RUC: {{organizacion.ruc}} · Emitida el {{fecha_emision}}
...
```

Reglas del archivo:

- Cada variable del cuerpo debe ser de la lista de variables comunes o estar declarada en `variables_contexto`. El validador rechaza las desconocidas.
- `validacion_legal` solo pasa a `validada` con el dictamen jurídico registrado en la revisión `juridica` del flujo editorial.
- No se incluyen datos reales de personas, credenciales ni URL internas.

## c) Contrato de API mínimo

Prefijo `/api/v1/biblioteca`. El servidor toma la organización **siempre de la sesión** (`tenant_id`) y nunca del cuerpo ni de la URL. Pedir el id de un documento de otra organización devuelve `404`. Los errores siguen el formato de `api/errores.py` (`ErrorNegocio`).

| # | Método y ruta | Uso | Respuesta |
|---|---|---|---|
| 1 | `GET /plantillas?fuente=smartcidi\|organizacion&tipo=&ola=` | Pestaña Plantillas | `[{id, codigo, nombre, tipo, fuente, version, validacion_legal, ola}]`; solo versiones **publicadas** y las «Mi plantilla» de la organización |
| 2 | `GET /plantillas/{id}` | Ficha y vista previa | `{…metadatos, cuerpo_markdown, variables:[{clave, etiqueta, disponible}]}`; `disponible` dice si la organización ya tiene ese dato |
| 3 | `POST /plantillas/{id}/copias` | Editar una SMARTCIDI → «Mi plantilla» | `201 {id, fuente:"organizacion", origen_plantilla_id, origen_version}` |
| 4 | `POST /documentos` `{plantilla_id, fecha_emision?, contexto?:{…}}` | **Usar en esta organización** | `201 Documento` en `borrador` con las variables rellenadas |
| 5 | `GET /documentos?estado=&origen=` | Pestaña Documentos | `[DocumentoResumen]` |
| 6 | `GET /documentos/{id}` | Ver | `Documento` |
| 7 | `PATCH /documentos/{id}` `{contenido_markdown, revision}` | Editar (solo en `borrador`) | `200 Documento`; `editado=true`; `409` si `revision` está desfasada |
| 8 | `POST /documentos/{id}/estado` `{estado, motivo?}` | Cambiar estado | `200 Documento`; `422` si la transición no está permitida |
| 9 | `GET /documentos/pendientes` | Contador del botón | `{borrador, en_revision, por_vencer, vencidos, total}` |

`Documento`:

```json
{
  "id": "uuid", "codigo": "BIB-001", "nombre": "…",
  "origen": "plantilla | propio | subido",
  "plantilla_id": "uuid|null", "plantilla_version": "0.1.0|null",
  "contenido_markdown": "…", "variables_faltantes": ["organizacion.direccion"],
  "editado": false,
  "estado": "borrador | en_revision | aprobado | vencido",
  "aprobado_por": "user_id|null", "aprobado_en": "fecha|null",
  "sha256": "hex del contenido", "proxima_revision": "AAAA-MM-DD",
  "tarea_hoja_ruta_id": "uuid|null", "revision": 3,
  "creado_en": "…", "actualizado_en": "…"
}
```

Transiciones de estado:

| De → a | Quién | Condición |
|---|---|---|
| `borrador` → `en_revision` | editor de la organización | sin variables faltantes |
| `en_revision` → `borrador` | revisor o aprobador | `motivo` obligatorio |
| `en_revision` → `aprobado` | DPD o administrador de la organización | quien aprueba no es quien editó por última vez; fija `aprobado_por`, `aprobado_en` y `sha256` |
| `aprobado` → `borrador` | editor | crea una revisión nueva; la aprobada queda en el historial |
| `aprobado` → `vencido` | sistema | `proxima_revision` < hoy (se calcula al leer; nunca lo pide un usuario) |

Los documentos *propio* (redactado en la plataforma) y *subido* (archivo) comparten el modelo, pero sus rutas de alta (`POST /documentos/propios` y `POST /documentos/subidos`) quedan **fuera del PMV mínimo**. Se diseñan con BIB-106.

## d) Seguimiento de los 12 documentos

Leyenda: ⬜ pendiente · 🟨 en curso · ✅ hecho. «Validación legal» solo pasa a ✅ con el dictamen jurídico registrado.

| Ola | Documento | Contenido | Backend | Frontend | Verificado | Validación legal |
|---|---|---|---|---|---|---|
| 1 | BIB-001 Política de protección de datos personales | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 1 | BIB-002 Aviso de privacidad para clientes | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 1 | BIB-003 Formulario de consentimiento | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 1 | BIB-004 Acuerdo de confidencialidad para empleados | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 1 | BIB-005 Contrato de encargo de tratamiento | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 1 | BIB-006 Registro de actividades de tratamiento simple | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 2 | BIB-007 Procedimiento y formulario de solicitudes de titulares | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 2 | BIB-008 Modelos de respuesta a solicitudes | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 2 | BIB-009 Protocolo de vulneraciones de seguridad y formato de registro | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 2 | BIB-010 Aviso de privacidad para empleados y candidatos | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 3 | BIB-011 Aviso de videovigilancia | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 3 | BIB-012 Aviso de privacidad web y cláusula de formularios | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

Las columnas Backend y Frontend se marcan por documento aunque la infraestructura común (tablas, endpoints, panel) se construya una sola vez con BIB-001.

## e) Definición de terminado por documento

Un documento BIB-00X está **terminado** cuando, en una organización de prueba:

1. **Aparece en la pestaña Plantillas** como plantilla SMARTCIDI publicada, con su versión y su estado de validación legal visibles.
2. **Se puede usar en la organización de prueba** con «Usar en esta organización», y el documento queda en *Documentos de la organización* con la etiqueta *basado en plantilla*.
3. **El borrador muestra las variables rellenadas** con los datos de la organización. Las que falten aparecen marcadas y bloquean el paso a revisión.
4. **Se puede aprobar**: borrador → en revisión → aprobado. Quedan registrados quién aprobó, la fecha, el hash y la próxima revisión.
5. **Se ve también desde el panel del botón «Biblioteca»**, en ambas pestañas, y el contador refleja el cambio de estado.

Además, en todos los casos:

6. Un usuario de otra organización de prueba **no** ve el documento: la lista no lo incluye y abrirlo por su id devuelve `404`.
7. Las pruebas automáticas de backend y la prueba Playwright del recorrido 1–5 pasan en el CI, con **todos** los checks terminados.
8. Backend y frontend dejaron su nota en `docs/biblioteca-entregas.md`, y la fila del documento está actualizada en la tabla del apartado d).

«Validación legal ✅» **no** forma parte de «terminado»: un documento puede estar terminado técnicamente con la validación pendiente. En ese caso la plantilla lo muestra con la etiqueta *Pendiente de validación legal*.
