# API-02b · Webhooks firmados HMAC-SHA256 con techo del paquete
`¤sdd` `¤seguridad` `¤seguridad-tenant` `¤frontend-ide` `¤arbitro`

## 1. Datos

Tabla `webhooks_suscripciones`, RLS ENABLE y FORCE por `tenant_id`, sin DELETE para `lopdp_app` (`GRANT SELECT, INSERT, UPDATE`):
- `id` (UUID PK), `tenant_id` (VARCHAR(64) NOT NULL), `url` (TEXT NOT NULL, `https://`), `eventos` (TEXT[] NOT NULL, no vacío), `secreto_cifrado` (TEXT NOT NULL), `activo` (BOOLEAN NOT NULL DEFAULT true), `creada_en` (TIMESTAMPTZ NOT NULL DEFAULT now()), `rotada_en` (TIMESTAMPTZ NULL).

Migración `alembic/versions/api02b_webhooks_suscripciones.py`, de la sala `boveda_cloud` (CI-28): `down_revision = "api02_claves_integracion"` (la cabeza de esa sala) y `branch_labels = None`.

Constantes en `app_core/integraciones/webhooks.py`:
- `EVENTOS_WEBHOOK = ("webhook.prueba", "incidente.registrado", "derecho.solicitud_recibida", "tarea.validada")`, catálogo cerrado.
- `VENTANA_SEGUNDOS = 300`; `REINTENTOS = 3` con espera de 1, 2 y 4 s; `TIMEOUT_SEGUNDOS = 5`.
- `VARIABLE_CLAVE_CIFRADO = "WEBHOOKS_CLAVE_CIFRADO"`: clave Fernet que llega de Secret Manager, como `INVENTARIO_CLAVE_CIFRADO`.

Hecho medido en `origin/main` 04292440: API-02 y BOV-01 están hechas; `techos.py` lee `boveda_cloud.techos_integracion(...)["webhooks"]`, cuenta `webhooks_activos = 0` y tiene la sección `API-02b` sembrada; `IntegracionesView.tsx` también la tiene. `api02_claves_integracion` es la cabeza de la sala `boveda_cloud`.

## 2. API

| Método y ruta | Roles | Respuesta |
| :--- | :--- | :--- |
| `POST /api/v1/integraciones/webhooks` | admin_organizacion | `201` con la suscripción y el secreto en claro una sola vez |
| `GET /api/v1/integraciones/webhooks` | admin_organizacion | `200` lista sin secreto |
| `POST /api/v1/integraciones/webhooks/{id}/rotar-secreto` | admin_organizacion | `200` con el secreto nuevo en claro una sola vez |
| `POST /api/v1/integraciones/webhooks/{id}/desactivar` | admin_organizacion | `200` |
| `POST /api/v1/integraciones/webhooks/{id}/probar` | admin_organizacion | `200` con `{entregado, intentos, estado_http}` del evento `webhook.prueba` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 404 | `WEBHOOK_NO_ENCONTRADO` | la suscripción no es de la organización |
| 409 | `TECHO_WEBHOOKS_ALCANZADO` | activos ≥ techo del paquete |
| 422 | `WEBHOOK_URL_NO_PERMITIDA` | no es `https`, o resuelve a una IP privada, loopback, de enlace local o de metadatos |
| 422 | `WEBHOOK_EVENTO_DESCONOCIDO` | un evento fuera de `EVENTOS_WEBHOOK` |
| 503 | `WEBHOOKS_CIFRADO_NO_CONFIGURADO` | falta `WEBHOOKS_CLAVE_CIFRADO` o no es una clave Fernet válida |

## 3. Reglas

- **R1 · Secreto cifrado.** El secreto (32 bytes aleatorios, `secrets.token_urlsafe`) se guarda cifrado con Fernet y solo se muestra al crear y al rotar. Sin clave configurada no se crea ni se firma nada (falla cerrada, 503).
- **R2 · Destino seguro.** Solo `https`. El nombre se resuelve al crear y en cada entrega; si alguna dirección es privada, loopback, de enlace local (incluida 169.254.169.254) o no enrutable, se rechaza. La entrega no sigue redirecciones.
- **R3 · Firma.** Cada entrega lleva `X-Evydentia-Marca-Tiempo` (segundos UTC) y `X-Evydentia-Firma: sha256=<hex>`, que es el HMAC-SHA256 del secreto sobre `"<marca>.<cuerpo>"`. `verificar_firma(secreto, marca, cuerpo, firma, ahora)` compara en tiempo constante y rechaza marcas a más de `VENTANA_SEGUNDOS`.
- **R4 · Entrega síncrona.** `entregar(suscripcion, evento, datos)` hace hasta `REINTENTOS` intentos con espera 1, 2 y 4 s y `TIMEOUT_SEGUNDOS`; un 2xx es entregado. Sin cola ni trabajos en segundo plano (RET-03). Cada sala que emita un evento del catálogo lo hace por `app_core/pasillo` en su propia ficha; esta ficha entrega `webhook.prueba`.
- **R5 · Techo.** La sección `API-02b` de `techos.py` cuenta las suscripciones activas; crear sobre el techo da 409 `TECHO_WEBHOOKS_ALCANZADO`. Desactivar libera cupo.
- **R6 · Roles.** Solo `admin_organizacion`. Las rutas están en `tests/matriz/API-02b.py`, con `PREFIJOS = ("/api/v1/integraciones/webhooks",)` si el prefijo no lo cubre otro archivo.
- **R-ADPA · Ortogonalidad ZERAG (`API-02b`).** El techo del paquete llega por `app_core/pasillo/boveda_cloud`; sin imports cruzados.

## 4. Interfaz

Propuesta para UX/UI, que la cierra antes de lanzar la ficha. Panel «Webhooks» (`WebhooksPanel.tsx`) en la sección `API-02b` de `IntegracionesView.tsx`, debajo de las claves:
- Lista con URL, eventos, estado y fecha de la última rotación, y el contador «N de M webhooks» del techo.
- Botones «Añadir webhook», «Probar», «Rotar secreto» y «Desactivar», con diálogo de confirmación en los dos últimos.
- El secreto se muestra una vez, con botón de copiar y el aviso «Guárdalo ahora: no volverá a mostrarse».
- Los textos y los mensajes de error los cierra UX/UI.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una suscripción, **cuando** se firma un evento y se verifica con su secreto, **entonces** es válido. Mutación m1: verificar con otro secreto falla. | `test_firma_hmac_valida` |
| **Dado** una marca de hace 301 s, **entonces** `verificar_firma` la rechaza. Mutación m2: aceptar la marca vieja hace fallar la prueba. | `test_marca_fuera_de_ventana` |
| **Dado** URLs `http://`, `https://127.0.0.1`, `https://10.0.0.5`, `https://169.254.169.254` y un nombre que resuelve a una IP privada, **entonces** 422 `WEBHOOK_URL_NO_PERMITIDA`. Mutación m3: aceptar una de ellas hace fallar la prueba. | `test_url_interna_rechazada` |
| **Dado** un paquete con techo 2 y dos activas, **cuando** se crea la tercera, **entonces** 409; tras desactivar una, 201. Mutación m4: crear sobre el techo hace fallar la prueba. | `test_techo_de_webhooks` |
| **Dado** el GET, **entonces** ninguna fila trae el secreto ni `secreto_cifrado`. Mutación m5: devolverlo hace fallar la prueba. | `test_secreto_nunca_en_el_listado` |
| **Dado** un receptor que responde 500, 500 y 200, **cuando** se prueba, **entonces** `entregado` con 3 intentos; con 500 siempre, no entregado tras 3. | `test_entrega_con_reintentos` |
| **Dado** organizaciones A y B, **cuando** B lista, **entonces** no ve las de A. | `test_webhooks_rls_aislamiento_tenant` |
| **Dado** un rol distinto de admin_organizacion, **entonces** 403 en las cinco rutas. | `tests/test_matriz_permisos.py` |
| **Dado** la pantalla, **entonces** el secreto aparece una vez y el contador refleja el techo. | `frontend/tests/integraciones/webhooks.spec.ts` |

Las pruebas no salen a la red: el receptor es un servidor local y la resolución DNS se inyecta. Sin `import yaml`.

## 6. Trazabilidad

- Ficha: `governance/tareas/API-02b.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Hija de API-02 (R4 «Webhooks verificables»); invariante `INV_API_INTEGRATION_SCOPED_KEYS_VERSIONED`. PRD §5.4, pilar 4.
- El secreto `WEBHOOKS_CLAVE_CIFRADO` lo crea el propietario en Secret Manager con `governance/operaciones/BRIEF_PROPIETARIO_SECRETO_WEBHOOKS.md`, como el de inventario.
- Depende de API-02 y BOV-01, hechas. Pasa por UX/UI (§4) antes de lanzarse.
