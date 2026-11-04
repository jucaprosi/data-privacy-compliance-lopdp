# CCTV-02 · Congelamiento Forense (Hold Legal) y Acta Quincenal de Destrucción CCTV
`¤sdd` `¤videovigilancia-cctv` `¤incidentes` `¤derechos` `¤conservacion`

## 1. Datos

Tabla `cctv_clips_boveda`: `id` (UUID PK), `tenant_id`, `camara_id` (UUID FK), `sha256_clip` (CHAR(64)), `fecha_captura` (TIMESTAMPTZ), `expira_en` (TIMESTAMPTZ), `hold_legal_activo` (BOOLEAN DEFAULT FALSE), `expediente_origen_tipo` (`'INCIDENTE' | 'ARCOP' | NULL`), `expediente_origen_id` (VARCHAR(64) NULL), `bucket_actual` (`'short-ttl' | 'long-retention'`), `acta_destruccion_hash` (CHAR(64) NULL).

## 2. API

- `POST /api/v1/videovigilancia/clips/{clip_id}/hold-legal` -> `200 OK`
- `POST /api/v1/videovigilancia/purga-quincenal/ejecutar` -> `200 OK`

## 3. Reglas

- **R1 · Prevalencia absoluta del Hold Legal (`INV_LOPDP_CCTV_LEGAL_HOLD_OVERRIDE`).** El barrido de purga de 15 días filtra estrictamente `hold_legal_activo = False`; intentar purgar un clip con `hold_legal_activo = True` lanza `ErrorNegocio('CCTV_CLIP_PROTEGIDO_POR_HOLD_LEGAL')` (409).
- **R2 · Promoción WORM inmediata.** Activar el Hold Legal mueve el clip a `long-retention` con Object Lock y registra el vínculo con el incidente o solicitud ARCOP.
- **R3 · Acta quincenal inmutable.** Cada corrida de purga sella un certificado con la lista de hashes `sha256_clip` destruidos y su hash maestro.

## 4. Interfaz

Pantalla `frontend/src/components/pantallas/CCTV-02.tsx` con botón de congelamiento por incidente/ARCOP y descarga de actas quincenales de destrucción.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** diez clips vencidos a los 15 días donde uno tiene `hold_legal_activo = True` por un robo reportado, **cuando** corre la purga quincenal, **entonces** se destruyen 9 clips, se genera el acta `SHA-256` y el clip en Hold Legal se conserva en el bucket WORM. | `test_purga_15_dias_respeta_hold_legal_y_emite_acta` |
| **Dado** un intento directo de eliminar un clip con `hold_legal_activo = True`, **cuando** se invoca el servicio, **entonces** responde 409 `CCTV_CLIP_PROTEGIDO_POR_HOLD_LEGAL`. | `test_bloqueo_borrado_clip_con_hold_legal` |

## 6. Trazabilidad

- PRD §8.3, §9 criterio 21 e invariante `INV_LOPDP_CCTV_LEGAL_HOLD_OVERRIDE`.
