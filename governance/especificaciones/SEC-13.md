# SEC-13 · Límite de peticiones en la API por IP, usuario y organización
`¤sdd` `¤seguridad` `¤seguridad-tenant` `¤copiloto-ia`

## 1. Datos

Sin tablas. Contadores en Redis con clave `lim:<politica>:<ambito>:<id>` y caducidad igual a la ventana. El ámbito es `ip`, `usuario` u `organizacion`; la identidad y la organización salen del token, nunca del cuerpo.

Políticas iniciales (parámetros, ajustables por variable de entorno `LIMITE_<POLITICA>`):

| Política | Rutas | Ámbito | Límite inicial |
| :--- | :--- | :--- | :--- |
| `inicio_sesion` | rutas de autenticación | IP | 10 por minuto |
| `ia_usuario` | copiloto, preanálisis, hoja de ruta y cualquier llamada a un modelo | usuario | 30 por hora |
| `ia_organizacion` | las mismas | organización | 200 por día |
| `url_firmada` | emisión de URLs de subida o descarga de evidencias | usuario | 120 por hora |
| `api_general` | resto de `/api/v1` | usuario | 300 por minuto |

## 2. API

- Cualquier ruta cubierta -> `429 Too Many Requests` con cabecera `Retry-After` (segundos) y cuerpo `{"codigo": "LIMITE_PETICIONES", "politica": "<politica>"}`.
- Ruta de IA con Redis inaccesible -> `503` con `LIMITE_NO_DISPONIBLE`.
- `/health` y `/api/v1/health` quedan fuera de toda política.

## 3. Reglas

- **R1 · Ventana deslizante.** Se cuenta cada petición en su ventana; al superar el límite se rechaza sin ejecutar el manejador de la ruta.
- **R2 · Aislamiento por organización.** El consumo de una organización nunca descuenta el cupo de otra (`¤seguridad-tenant`).
- **R3 · Tope de gasto de IA.** Una petición de IA se admite solo si caben a la vez `ia_usuario` e `ia_organizacion`; el rechazo ocurre antes de llamar al proveedor del modelo.
- **R4 · Fallo seguro asimétrico.** Redis caído: IA cerrada (503), resto abierto con aviso en el registro.
- **R5 · Sin datos personales en las claves.** La clave usa el identificador interno del usuario o la IP, nunca el correo.

## 4. Interfaz

Sin pantalla nueva. El frontend muestra el 429 como aviso legible («Has superado el número de solicitudes; vuelve a intentarlo en N segundos»), sin datos simulados (`API-01`).

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una IP que hace 11 intentos de inicio de sesión en un minuto, **cuando** llega el undécimo, **entonces** responde 429 con `Retry-After` mayor que 0. | `test_inicio_sesion_429_con_retry_after` |
| **Dado** un usuario que agotó `ia_usuario`, **cuando** pide otra respuesta al copiloto, **entonces** responde 429 y el cliente del modelo no recibe ninguna llamada. | `test_ia_rechazada_antes_de_llamar_al_modelo` |
| **Dado** la organización A con su cupo de IA agotado, **cuando** un usuario de la organización B pide IA, **entonces** se admite. | `test_cupo_aislado_por_organizacion` |
| **Dado** Redis inaccesible, **cuando** llega una petición de IA y otra general, **entonces** la de IA responde 503 y la general se atiende con un aviso registrado. | `test_fallo_seguro_asimetrico` |
| **Dado** cualquier política agotada, **cuando** se consulta `/health`, **entonces** responde 200. | `test_health_fuera_de_politicas` |

## 6. Trazabilidad

- `PRD_EVYDENTIA_REVENTA_NUBE.md` §5.3 (Cloud Armor en el borde) y Módulo 6 (costo de Gemini); requisito 7 de la revisión del 2026-11-04.
- Complementa, sin sustituir, los límites del portal público de DER-02 y el diseño de SEC-12.
