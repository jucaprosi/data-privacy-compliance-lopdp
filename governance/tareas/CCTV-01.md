+++
id = "CCTV-01"
titulo = "Sala Videovigilancia LOPDP: inventario de cámaras/NVR, auditoría de perfil técnico (H.265, eventos, sin audio, máscaras) y retención de 15 días"
ola = "D"
estado = "pendiente"
sala = "videovigilancia"
depende_de = ["ADPA-06", "ADPA-07", "BOV-01", "MARCA-01"]
propiedad = ["alembic/versions/20260501_02_cctv01_camaras_y_politicas.py", "features/videovigilancia/__init__.py", "features/videovigilancia/models.py", "features/videovigilancia/schemas.py", "features/videovigilancia/videovigilancia_service.py#CCTV-01", "features/videovigilancia/domain/__init__.py", "features/videovigilancia/domain/errores.py#CCTV-01", "features/videovigilancia/routes/__init__.py", "features/videovigilancia/routes/videovigilancia_routes.py", "app_core/pasillo/videovigilancia.py#CCTV-01", "app_core/pasillo/rat.py#CCTV-01", "main.py#CCTV-01", "frontend/src/components/layout/menus/index.ts#CCTV-01", "frontend/src/components/layout/pantallas/index.tsx#CCTV-01", "frontend/src/components/layout/pantallas/CCTV-01.tsx", "tests/test_cctv01_inventario_y_perfil_camaras.py"]
arbitro = "pytest tests/test_cctv01_inventario_y_perfil_camaras.py + suite completa + vigilantes"
rastros = ["¤videovigilancia-cctv", "¤boveda-cloud", "¤rat"]
+++
# CCTV-01 · Sala Videovigilancia LOPDP: inventario de cámaras/NVR, auditoría de perfil técnico (H.265, eventos, sin audio, máscaras) y retención de 15 días

## Entrega
- Tablas `cctv_camaras_inventario` y `cctv_clips_boveda` con RLS forzado por `tenant_id` (`sede_nombre`, `codec` en `{'H265', 'H265_PLUS'}`, `modo_grabacion` en `{'EVENTO_MOVIMIENTO'}`, `audio_ambiental_activo` BOOL que debe ser `False`, `mascara_privacidad_activa` BOOL, `plazo_retencion_dias` DEFAULT 15, `actividad_rat_id`).
- Compuerta `features/videovigilancia/videovigilancia_service.py#CCTV-01` que valida los 4 requisitos técnicos LOPDP de cada cámara antes de habilitar su ingesta en la Bóveda Cloud, rechazando con `CCTV_AUDIO_AMBIENTAL_PROHIBIDO` (422) o `CCTV_CODEC_NO_OPTIMIZADO` (422) configuraciones intrusivas o sin compresión H.265.
- Pantalla `frontend/src/components/layout/pantallas/CCTV-01.tsx` con el inventario de cámaras por sede, semáforo de cumplimiento técnico LOPDP y asistente de configuración NVR.

## Pruebas
- `pytest tests/test_cctv01_inventario_y_perfil_camaras.py` comprueba el rechazo de cámaras con audio ambiental activo o grabación continua sin eventos, el vínculo con el RAT vía `app_core/pasillo/rat.py#CCTV-01` y el aislamiento RLS.
