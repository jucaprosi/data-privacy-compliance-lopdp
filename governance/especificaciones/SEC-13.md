# SEC-13 · Límite de peticiones por organización, usuario, ruta e IP (Cloud Armor + Memorystore), bloqueo de inicio de sesión y cuota mensual de IA por paquete
`¤sdd` `¤limite-peticiones` `¤grado-productivo` `¤seguridad` `¤copiloto-ia`

## 1. Datos

Techo `TechoRuta` (`ruta: str`, `peticiones: int`, `ventana_s: int`). Consumo `ConsumoIA` (`tenant_id: UUID`, `periodo: str (AAAA-MM)`, `tokens_entrada: int`, `tokens_salida: int`, `techo_tokens: int`). Los techos por paquete se leen como dato de `boveda_cloud` a través de `app_core/pasillo/boveda_cloud.py`.

## 2. API

- Cualquier ruta -> `429 Too Many Requests` con cabecera `Retry-After` al superar su techo.
- Llamadas del Copiloto y de la Hoja de Ruta -> `402 Payment Required` con mensaje de cuota agotada cuando la organización alcanzó su techo mensual de IA.

## 3. Reglas

- **R1 · Contadores por tenant (`INV_RATE_LIMIT_PER_TENANT_USER_ROUTE`).** La clave de todo contador incluye `tenant_id` o la IP: el consumo de una organización nunca descuenta el de otra.
- **R2 · Inicio de sesión y portales (`INV_AUTH_AND_PUBLIC_PORTAL_THROTTLING`).** Cinco intentos fallidos por cuenta e IP en 15 minutos bloquean temporalmente; los portales aceptan 10 envíos por IP y hora; la respuesta no distingue cuenta inexistente de contraseña incorrecta.
- **R3 · Saldo de IA (`INV_AI_SPEND_QUOTA_PER_TENANT`).** La comprobación de cuota ocurre antes de la llamada a Vertex AI; las rutas con plazo legal (ARCOP+, vulneraciones, inspección SPDP) no dependen de la cuota.

## 4. Interfaz

Mensaje claro al usuario cuando recibe `429` (reintentar en N segundos) o cuando la cuota de IA se agotó (contactar al administrador para ampliar el paquete), sin exponer detalles internos.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una organización que supera el techo de una ruta, **cuando** envía una petición más, **entonces** recibe `429` con `Retry-After` y otra organización sigue atendida. | `test_techo_por_organizacion_independiente` |
| **Dado** una cuenta con cuatro intentos fallidos desde la misma IP, **cuando** falla el quinto, **entonces** el inicio de sesión queda bloqueado 15 minutos con un mensaje que no revela si la cuenta existe. | `test_bloqueo_quinto_intento` |
| **Dado** una organización con el 100 % de su cuota mensual de IA consumida, **cuando** pide una respuesta al Copiloto, **entonces** la llamada a Vertex AI no se ejecuta y una solicitud ARCOP+ sigue registrándose. | `test_cuota_ia_agotada_no_bloquea_plazos_legales` |

## 6. Trazabilidad

- PRD_EVYDENTIA_REVENTA_NUBE §2.3, §5.4 pilar 7 y criterio 28; invariantes `INV_RATE_LIMIT_PER_TENANT_USER_ROUTE`, `INV_AUTH_AND_PUBLIC_PORTAL_THROTTLING` e `INV_AI_SPEND_QUOTA_PER_TENANT`.
