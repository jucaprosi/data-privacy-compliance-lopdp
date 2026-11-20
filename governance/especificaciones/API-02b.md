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
- **R5 · Techo.** La sección `API-02b` de `techos.py` cuenta las suscripciones activas; crear sobre el techo da 409 `TECHO_WEBHOOKS_ALCANZADO`. Desactivar libera cupo y es definitivo: una suscripción desactivada no se reactiva, y para volver a recibir avisos se crea otra.
- **R6 · Roles.** Solo `admin_organizacion`. Las rutas están en `tests/matriz/API-02b.py`, con `PREFIJOS = ("/api/v1/integraciones/webhooks",)` si el prefijo no lo cubre otro archivo.
- **R-ADPA · Ortogonalidad ZERAG (`API-02b`).** El techo del paquete llega por `app_core/pasillo/boveda_cloud`; sin imports cruzados.

## 4. Interfaz

Textos cerrados por UX/UI (2026-11-19). Van en `WebhooksPanel.tsx`, dentro de la sección `API-02b` de `IntegracionesView.tsx`, debajo de «Claves de acceso». Solo lo ve `admin_organizacion`: con 403 el panel no se pinta, y el 401 lo maneja la aplicación.

**Panel.** Encabezado h2 «Avisos automáticos (webhooks)».
- Ayuda: «Envían un aviso a otro sistema cuando ocurre algo en la plataforma. Cada aviso va firmado para que ese sistema compruebe que viene de EVYDENTIA.»
- Contador (`role=status`): «{N} de {M} webhooks activos».
- Tabla «Webhooks» (tarjetas a 375 px). Columnas:
  - «Dirección»: la URL en monoespaciada, cortada con «…»; completa en el `title` y en el nombre accesible.
  - «Eventos».
  - «Estado»: «Activo» o «Desactivado», con texto e icono.
  - «Último cambio de secreto»: dd/mm/aaaa, o «Sin cambios».
  - Acciones.
- Vacío: «Aún no hay webhooks. Añade uno para avisar a otro sistema.»

**Nombres de los eventos.** En pantalla nunca aparece el código:

| Código | Nombre |
| :--- | :--- |
| `webhook.prueba` | Aviso de prueba |
| `incidente.registrado` | Incidente registrado |
| `derecho.solicitud_recibida` | Solicitud de un titular recibida |
| `tarea.validada` | Tarea de la hoja de ruta validada |

El selector solo ofrece los eventos que ya tienen una sala emisora. Con esta ficha sale únicamente «Aviso de prueba», que se envía desde «Probar»; los demás se añaden al selector en la ficha de la sala que los emite.

**Añadir webhook.** Botón «Añadir webhook». Con el techo alcanzado lleva `aria-disabled` y la línea «Alcanzaste el máximo de webhooks de tu plan ({M}). Desactiva uno para añadir otro.»

Diálogo «Añadir webhook»:
- Campo «Dirección del webhook», con la ayuda «Debe empezar por https:// y ser una dirección pública.»
- Grupo «Eventos»: casillas con el nombre de cada evento. Sin ninguna marcada, «Elige al menos un evento.»
- Botones «Cancelar» (foco inicial) y «Añadir webhook».

**Secreto.** Tras crear o rotar, es un paso del mismo diálogo y no se cierra con Escape ni con un clic fuera.
- Título «Copia el secreto ahora».
- Aviso: «Guárdalo ahora: no volverá a mostrarse. Tu sistema lo necesita para comprobar la firma de cada aviso.»
- Campo de solo lectura «Secreto del webhook», en monoespaciada, y botón «Copiar el secreto». Al copiar, el estado dice «Secreto copiado.»
- Casilla «Guardé el secreto en un lugar seguro», que habilita «Ya lo guardé».
- Al cerrar, el secreto sale del estado de la página. Nunca va a la URL, al almacenamiento local ni a la consola.

**Probar.** Botón por fila «Probar», con nombre accesible «Probar el webhook {dirección}».
- Mientras envía: `aria-busy` y «Enviando un aviso de prueba… puede tardar unos segundos.»
- Si llega: «El aviso de prueba llegó. Tu sistema respondió con el código {estado_http} tras {intentos} {intento|intentos}.»
- Si no llega (`role=alert`): «El aviso de prueba no llegó tras {intentos} intentos. Comprueba la dirección y que tu sistema responda.» Si hubo respuesta, añade «Tu sistema respondió con el código {estado_http}.»

**Rotar secreto.** Botón «Rotar secreto», con nombre accesible «Rotar el secreto del webhook {dirección}».
- Diálogo «¿Rotar el secreto de este webhook?» con el texto «Se crea un secreto nuevo y los próximos avisos se firman con él. Actualiza tu sistema con el secreto nuevo; si no, rechazará los avisos.»
- Botones «Cancelar» (foco inicial) y «Rotar el secreto». Después sigue el paso «Copia el secreto ahora».

**Desactivar.** Botón «Desactivar», con nombre accesible «Desactivar el webhook {dirección}».
- Diálogo «¿Desactivar este webhook?» con el texto «Deja de enviar avisos a {dirección} de inmediato y libera un lugar de tu plan. No se puede volver a activar: si lo necesitas otra vez, añade uno nuevo.»
- Botones «Cancelar» (foco inicial) y «Desactivar el webhook».
- Al terminar, el estado dice «Webhook desactivado.» y la fila queda «Desactivado», sin «Probar» ni «Rotar secreto».

**Errores.** Cada código tiene un texto fijo; nunca se muestra el texto del servidor.

| Caso | Texto |
| :--- | :--- |
| 404 `WEBHOOK_NO_ENCONTRADO` | «No encontramos este webhook. Actualizamos la lista.» (y recarga) |
| 409 `TECHO_WEBHOOKS_ALCANZADO` | «Alcanzaste el máximo de webhooks de tu plan. Desactiva uno para añadir otro.» |
| 422 `WEBHOOK_URL_NO_PERMITIDA` | en el campo: «Esta dirección no está permitida. Usa una dirección pública que empiece por https://.» |
| 422 `WEBHOOK_EVENTO_DESCONOCIDO` | «Uno de los eventos elegidos ya no existe. Vuelve a elegir los eventos.» (y recarga el catálogo) |
| 503 `WEBHOOKS_CIFRADO_NO_CONFIGURADO` | «Los webhooks no están disponibles en este momento. Escribe al equipo de EVYDENTIA.» |
| Fallo al cargar | `role=alert`: «No pudimos cargar los webhooks. Inténtalo de nuevo.», con «Volver a cargar» |
| Fallo de otra acción | «No pudimos completar la acción. El webhook sigue como estaba.» |

Ningún texto de la pantalla nombra el algoritmo de firma ni el de cifrado, los rangos de red bloqueados, las cabeceras ni los códigos de evento. Ese detalle va en la documentación técnica para integradores.

**Accesibilidad.**

| Elemento | Rol | Nombre |
| :--- | :--- | :--- |
| Panel | region | Avisos automáticos (webhooks) |
| Tabla | table | Webhooks |
| Añadir | button | Añadir webhook |
| Diálogos | dialog | Añadir webhook / Copia el secreto ahora / ¿Rotar el secreto de este webhook? / ¿Desactivar este webhook? |
| Dirección | textbox | Dirección del webhook |
| Eventos | group | Eventos |
| Secreto | textbox (solo lectura) | Secreto del webhook |
| Copiar | button | Copiar el secreto |
| Por fila | button | Probar el webhook {dirección} / Rotar el secreto del webhook {dirección} / Desactivar el webhook {dirección} |

Requisitos generales: el foco queda atrapado en los diálogos y vuelve al botón de origen; contraste de 4.5:1 con los tokens del tema; sin desbordes a 375 px.

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
| **Dado** la pantalla con el techo alcanzado, **entonces** «Añadir webhook» lleva `aria-disabled` y aparece la línea del máximo. | `frontend/tests/integraciones/webhooks.spec.ts` |
| **Dado** el paso del secreto, **entonces** Escape no lo cierra; y tras «Ya lo guardé», ni el DOM ni `localStorage` contienen el secreto. | `frontend/tests/integraciones/webhooks.spec.ts` |
| **Dado** «Probar» con `entregado` verdadero y falso, una URL rechazada con 422 y un 503, **entonces** se ven sus textos fijos, el del 422 en el campo. | `frontend/tests/integraciones/webhooks.spec.ts` |
| **Dado** «Desactivar», **entonces** la fila queda «Desactivado» sin acciones; y ningún texto visible contiene el algoritmo de firma o de cifrado, `webhook.prueba` ni ids. | `frontend/tests/integraciones/webhooks.spec.ts` |

Las pruebas no salen a la red: el receptor es un servidor local y la resolución DNS se inyecta. Sin `import yaml`.

## 6. Trazabilidad

- Ficha: `governance/tareas/API-02b.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Hija de API-02 (R4 «Webhooks verificables»); invariante `INV_API_INTEGRATION_SCOPED_KEYS_VERSIONED`. PRD §5.4, pilar 4.
- El secreto `WEBHOOKS_CLAVE_CIFRADO` lo crea el propietario en Secret Manager con `governance/operaciones/BRIEF_PROPIETARIO_SECRETO_WEBHOOKS.md`, como el de inventario.
- Depende de API-02 y BOV-01, hechas. UX/UI cerró §4 el 2026-11-19.
