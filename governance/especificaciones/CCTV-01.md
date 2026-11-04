# CCTV-01 · Gobernanza de Cámaras de Videovigilancia LOPDP y Ciclo de 15 Días
`¤sdd` `¤videovigilancia-cctv` `¤boveda-cloud` `¤rat`

## 1. Datos

Tabla `cctv_camaras_inventario` (RLS forzado por `tenant_id`):
- `id` (UUID PK), `tenant_id` (VARCHAR(64) NOT NULL), `nombre_ubicacion` (VARCHAR(160) NOT NULL), `codec` (`'H265' | 'H265_PLUS'`), `modo_grabacion` (`'EVENTO_MOVIMIENTO'`), `audio_ambiental_activo` (BOOLEAN NOT NULL DEFAULT FALSE), `mascara_privacidad_activa` (BOOLEAN NOT NULL DEFAULT TRUE), `plazo_retencion_dias` (INTEGER NOT NULL DEFAULT 15 CHECK (`plazo_retencion_dias` BETWEEN 1 AND 30)), `estado_conformidad` (`'CONFORME' | 'BLOQUEADA_POR_CONFIG'`).

## 2. API

- `GET /api/v1/videovigilancia/camaras` -> `200 OK`
- `POST /api/v1/videovigilancia/camaras` -> `201 Created` | `422 Unprocessable Entity`

## 3. Reglas

- **R1 · Prohibición de audio ambiental por defecto.** Si `audio_ambiental_activo = True`, el registro para subida a la Bóveda se rechaza con `ErrorNegocio('CCTV_AUDIO_AMBIENTAL_PROHIBIDO')` (422).
- **R2 · Minimización por eventos y códec H.265.** Solo se habilitan cámaras con `codec IN ('H265', 'H265_PLUS')`, `modo_grabacion = 'EVENTO_MOVIMIENTO'` y `mascara_privacidad_activa = True` (`CCTV_CONFIGURACION_NO_CONFORME`, 422).

## 4. Interfaz

Pantalla `frontend/src/components/pantallas/CCTV-01.tsx` accesible desde el menú Inventario/Operación con checklist técnico para el NVR del cliente.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una cámara que intenta registrarse con `audio_ambiental_activo = True`, **cuando** se envía a `POST /api/v1/videovigilancia/camaras`, **entonces** se rechaza con 422 `CCTV_AUDIO_AMBIENTAL_PROHIBIDO`. | `test_rechazo_camara_con_audio_ambiental` |
| **Dado** una cámara con `H265_PLUS`, grabación por movimiento, sin audio y con máscara de privacidad, **cuando** se registra, **entonces** queda activa con retención de 15 días en el bucket `short-ttl`. | `test_alta_camara_conforme_retencion_15_dias` |

## 6. Trazabilidad

- PRD §8.3, §7.1 (`videovigilancia`) y Principio de Minimización (Art. 10 LOPDP).
