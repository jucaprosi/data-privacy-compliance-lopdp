+++
id = "BOV-01"
titulo = "Sala Bóveda Cloud: paquetes de reventa de almacenamiento, cuotas de GB/Egress y aprovisionamiento Multi-Tenant"
ola = "D"
estado = "en_curso"
sala = "boveda_cloud"
depende_de = ["ADPA-06", "ADPA-07", "GCP-01", "MARCA-01"]
propiedad = ["alembic/versions/bov01_boveda_paquetes_cuotas.py", "features/boveda_cloud/__init__.py", "features/boveda_cloud/models.py", "features/boveda_cloud/schemas.py", "features/boveda_cloud/boveda_cloud_service.py#BOV-01", "features/boveda_cloud/domain/__init__.py", "features/boveda_cloud/domain/errores.py#BOV-01", "features/boveda_cloud/routes/__init__.py", "features/boveda_cloud/routes/boveda_paquetes_routes.py", "app_core/pasillo/boveda_cloud.py#BOV-01", "app_core/pasillo/plataforma.py#BOV-01", "main.py#BOV-01", "frontend/src/components/layout/menus/index.ts#BOV-01", "frontend/src/components/layout/pantallas/index.tsx#BOV-01", "frontend/src/components/layout/menus/BOV-01.ts", "frontend/src/components/layout/pantallas/BOV-01.tsx", "tests/test_bov01_paquetes_cuotas.py", "tests/matriz/roles/auditor.py#BOV-01", "frontend/tests/boveda/bov01.spec.ts", "governance/operaciones/BRIEF_PROPIETARIO_BOV-01.md"]
arbitro = "pytest tests/test_bov01_paquetes_cuotas.py + suite completa + vigilantes + Playwright de frontend/tests/boveda/bov01.spec.ts"
rastros = ["¤boveda-cloud", "¤seguridad-tenant", "¤adpa"]
+++
# BOV-01 · Sala Bóveda Cloud: paquetes de reventa de almacenamiento, cuotas de GB/Egress y aprovisionamiento Multi-Tenant

## Entrega
- Tabla `boveda_suscripciones_tenant` con RLS forzado por `tenant_id` (`paquete_codigo`, `cuota_almacenamiento_bytes`, `uso_almacenamiento_bytes`, `cuota_egress_mensual_bytes`, `uso_egress_mensual_bytes`, `certificaciones_heredadas` JSONB con ISO 27001/27701/SOC 2, `estado` en `{ACTIVA, CUOTA_EXCEDIDA, SUSPENDIDA}`).
- Compuerta `features/boveda_cloud/boveda_cloud_service.py#BOV-01`, errores `features/boveda_cloud/domain/errores.py#BOV-01` (`BOVEDA_CUOTA_ALMACENAMIENTO_EXCEDIDA`, `BOVEDA_CUOTA_EGRESS_EXCEDIDA`, `BOVEDA_SUSCRIPCION_NO_ENCONTRADA`) y pasillo `app_core/pasillo/boveda_cloud.py#BOV-01`.
- Router `/api/v1/boveda-cloud/suscripcion` y pantalla `frontend/src/components/layout/pantallas/BOV-01.tsx` con medidores de consumo de almacenamiento y transferencia mensual.

## Pruebas
- `pytest tests/test_bov01_paquetes_cuotas.py` verifica el alta de paquete de nube por organización, el bloqueo con 409 `BOVEDA_CUOTA_EGRESS_EXCEDIDA` al superar el límite mensual de descarga y el aislamiento RLS entre inquilinos.

## Textos cerrados por UX/UI (2026-11-13)
Diseñado contra la ficha y los campos de la tabla; UX/UI no vio backend ni corrió pantalla. Decisiones del CTO (2026-11-13): roles y umbrales confirmados; el auditor se decide en una ficha aparte cuando ORG-22 esté en main.

**Ubicación.** Menú «Configuración» (`configuracion`; el registro no tiene un menú «Organización»), submenú «Almacenamiento», subtítulo «Espacio y descargas de tu plan». Vista `bov01_suscripcion`, montada con `menus/BOV-01.ts` y `pantallas/BOV-01.tsx` y las secciones `BOV-01` de los índices. Quién la ve (confirmado por el CTO): administrador de la organización, DPO y coordinador, en solo lectura; el resto no ve el submenú. La autorización sigue en el servidor. No hay botón para cambiar de plan ni comprar.

**Contenido** (una tarjeta; una columna a 375 px, dos medidores lado a lado desde 768 px):
- h1 «Almacenamiento y descargas». Línea «Tu plan: {nombre del plan}», o solo «Tu plan» si no hay nombre legible.
- Medidor «Espacio usado»: «{usado} de {cuota}» y porcentaje. Medidor «Descargas de este mes»: igual, con la ayuda «Se cuentan los archivos que descargas de la plataforma. Se reinicia cada mes.»
- Unidades: GB con un decimal; por debajo de 1 GB, MB sin decimales; separador local; nunca bytes.
- Umbrales (confirmados por el CTO): hasta 79 % neutro; de 80 a 99 % «Cerca del límite» (ámbar); 100 % o más «Límite alcanzado» (rojo). Nunca solo color: texto e icono.
- Estado junto al título: «Activa», «Límite excedido» o «Suspendida». Línea bajo la etiqueta si no es «Activa»:
  - Límite excedido: «Alcanzaste el límite de tu plan. Mientras no lo amplíes, no podrás subir ni descargar más archivos de este tipo. Escribe al equipo de EVYDENTIA para ampliarlo.»
  - Suspendida: «Tu servicio de almacenamiento está suspendido. Escribe al equipo de EVYDENTIA para reactivarlo.»
- Sección «Certificaciones del proveedor de nube» (ISO 27001, ISO 27701, SOC 2) solo si el servidor las trae, con la nota fija: «Son certificaciones de la infraestructura del proveedor. No certifican a tu organización ni sustituyen tu propio cumplimiento.» Lista vacía: no se pinta la sección. No se escribe «certificado», «conforme» ni «cumple» fuera de ese contexto.

**Estados.** Cargando: `role=status` «Cargando tu plan de almacenamiento…». 404 `BOVEDA_SUSCRIPCION_NO_ENCONTRADA`: `role=status` «Tu organización aún no tiene un plan de almacenamiento activo. Escribe al equipo de EVYDENTIA.» Error: `role=alert` «No pudimos cargar tu plan de almacenamiento. Inténtalo de nuevo.» y botón «Volver a cargar». 401 global; 403, la vista no se pinta. Mensajes fijos para quien consuma los 409: `BOVEDA_CUOTA_ALMACENAMIENTO_EXCEDIDA` «No hay espacio suficiente en tu plan para subir este archivo.»; `BOVEDA_CUOTA_EGRESS_EXCEDIDA` «Alcanzaste el límite de descargas de este mes.»

**Accesibilidad.** Vista `main`/`region` «Almacenamiento y descargas»; medidores `meter` «Espacio usado» y «Descargas de este mes», con `aria-valuetext` «{usado} de {cuota}, {porcentaje} %»; estado `status`; certificaciones `list` «Certificaciones del proveedor de nube»; botón «Volver a cargar». Contraste 4.5:1; solo tokens `--ui-*` y `badge-render-*`; sin tokens de gobernanza.

**Criterios de prueba.** (1) 50 % sin aviso, 85 % «Cerca del límite», 100 % «Límite alcanzado». (2) Excedido y suspendida muestran etiqueta y línea. (3) Certificaciones vacías: sin sección; con datos, nota fija. (4) 404, 500 y cargando con los textos fijos; el 500 nunca muestra el texto del servidor. (5) Ningún texto con bytes sin convertir, «certificado» sin la nota ni caracteres de gobernanza. (6) A 375 px, sin desplazamiento horizontal.

## Enmienda (Arquitecto ADPA, 2026-11-13; aprobada por el CTO): catálogo de paquetes y techos

**Entrega (añadido).**
- Tabla global `boveda_paquetes` (dato del operador, sin `tenant_id`): `codigo` PK, `nombre`, `cuota_almacenamiento_bytes`, `cuota_egress_mensual_bytes`, `peticiones_api_minuto`, `tokens_ia_mes`, `max_claves_integracion`, `max_webhooks`. Las cuatro últimas `INTEGER`/`BIGINT NULL` con `CHECK (valor IS NULL OR valor > 0)`; `NULL` = personalizado.
- La misma migración siembra cuatro filas con los valores del PRD §2.3 (peticiones por minuto / tokens de IA al mes / claves / webhooks): INICIAL 300 / 2 000 000 / 2 / 2; PROFESIONAL 1 200 / 10 000 000 / 10 / 10; CORPORATIVO 5 000 / 50 000 000 / 50 / 50; ENTERPRISE `NULL` en las cuatro. Las cuotas de GB y transferencia, las que ya define esta ficha.
- `boveda_suscripciones_tenant.paquete_codigo` pasa a FK a `boveda_paquetes(codigo)`.
- `lopdp_app` solo con `SELECT` sobre `boveda_paquetes`; la edición es del rol del operador de plataforma.
- Migración sin fecha `bov01_boveda_paquetes_cuotas.py` (sustituye a `20260501_01_…`); `down_revision` = la cabeza de `main` al implementar (FUSION_ALEMBIC).
- Pasillo `app_core/pasillo/boveda_cloud.py#BOV-01`: `techos_integracion(session, tenant_id) -> {"claves": int|None, "webhooks": int|None}` y `limites_uso(session, tenant_id) -> {"peticiones_api_minuto": int|None, "tokens_ia_mes": int|None}`; las dos leen el paquete de la suscripción; sin suscripción, `ErrorNegocio` `BOVEDA_SUSCRIPCION_NO_ENCONTRADA`.
- `limites_uso` es solo dato: no lo usan el limitador de SEC-13 ni `ia_tope_organizacion` (eso es SEC-13c, ficha aparte).

**Pruebas (añadidas).**
- `test_catalogo_paquetes_prd`: las cuatro filas con los valores exactos del PRD §2.3; ENTERPRISE con los cuatro `NULL`.
- `test_techos_integracion_por_paquete`: PROFESIONAL → `{claves: 10, webhooks: 10}`; ENTERPRISE → `{None, None}`; sin suscripción → `BOVEDA_SUSCRIPCION_NO_ENCONTRADA`.
- `test_limites_uso_solo_dato`: INICIAL → `{300, 2000000}`; un recorrido del AST comprueba que ningún módulo de `api/middleware` ni de `app_core/limites` importa `limites_uso`.
- `test_lopdp_app_no_edita_paquetes`: `UPDATE` o `INSERT` sobre `boveda_paquetes` con `lopdp_app` → permiso denegado.
- Mutaciones: m1 `max_claves_integracion` de INICIAL a 3 → falla el catálogo; m2 `techos_integracion` devuelve siempre INICIAL → falla; m3 `GRANT UPDATE` a `lopdp_app` → falla; m4 conectar `limites_uso` al limitador → falla.

**Ficha siguiente anotada (sin escribir):** SEC-13c, parametrizar `api_general` (por organización) e `ia_organizacion` con `limites_uso(tenant)`; `NULL` lo fija el operador; el límite transversal de 300 por usuario se mantiene; depende de BOV-01.

## Unidad de las cuotas (CTO, 2026-11-13): VERIFICADO
Base binaria, 1 GB = 2^30 bytes: es la unidad de la factura de Cloud Storage (https://cloud.google.com/storage/pricing, registrada en FUENTES_Y_BIBLIOGRAFIA.md). La interfaz muestra la misma unidad que la factura. El reinicio mensual del contador de descargas queda fuera de esta ficha; ningún texto de BOV-01 lo promete.
