# DER-02 · Portal público de solicitudes de titulares por organización, con enlace de seguimiento
`¤sdd` `¤seguridad` `¤rbac-tenant`

## 1. Datos

Migración `20261105_derechos_portal`: en `derechos_arco_solicitudes` columnas `canal VARCHAR(12) DEFAULT 'interno'`, `codigo_seguimiento_hash VARCHAR(64) UNIQUE NULL`; tabla `portal_config (tenant_id PK, activo BOOLEAN, slug VARCHAR(48) UNIQUE, texto_bienvenida TEXT)`. Función `SECURITY DEFINER` que resuelve `slug → tenant_id` y `codigo → estado` sin abrir RLS.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `GET /publico/solicitud/{slug}` | público | — | `200 {organizacion, derechos: [...], texto}` |
| `POST /publico/solicitud/{slug}` | público; límite 5 por IP y hora | `{derecho, nombre, email, descripcion}` | `201 {"codigo": str}` |
| `GET /publico/solicitud/seguir/{codigo}` | público | — | `200 {estado, recibida_en, respondida_en}` |
| `PUT /derechos/portal` | `admin_organizacion` | `{activo, slug, texto_bienvenida}` | `200` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 404 | — | slug inexistente o inactivo, o código desconocido (respuesta idéntica) |
| 429 | `PORTAL_LIMITE` | tasa superada |
| 422 | (FastAPI) | derecho fuera del catálogo, `email` inválido, descripción > 4.000 caracteres |

## 3. Reglas

- **R1 · Mínimo.** La solicitud pública solo toma derecho, nombre, correo y descripción; sin adjuntos en esta tarea.
- **R2 · Seguimiento.** Devuelve `estado`, `recibida_en`, `respondida_en`; nunca `respuesta_sha256` ni texto.
- **R3 · No enumeración.** 404 idéntico para slug inexistente, inactivo o código ajeno.
- **R4 · Tasa.** 5 solicitudes por IP y hora; el contador vive en Redis (`app_core/queue/redis_client.py`).

## 4. Interfaz

Página pública con marca de la organización, formulario de cuatro campos y confirmación con el código; página de seguimiento con el estado; Configuración interna del portal (activar, slug, texto).

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un código ajeno, **cuando** se consulta, **entonces** 404 con el mismo cuerpo que un código inexistente. Mutación: devolver el texto de la respuesta hace fallar la prueba. | `test_seguimiento_no_revela` |
| **Dado** 6 solicitudes desde una IP en una hora, **entonces** la sexta responde 429. | `test_portal_tasa` |
| **Dado** una solicitud pública creada, **entonces** aparece en la bandeja interna con `canal = portal`. | `test_portal_crea_solicitud` |
| **Dado** la página pública, **cuando** se envía el formulario, **entonces** muestra el código y el enlace de seguimiento. | `frontend/tests/derechos/portal.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/DER-02.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 2 («portal público… fase posterior con precondiciones»); SEC-12; Doctrina 8.
