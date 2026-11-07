+++
id = "NORM-01"
titulo = "Sala Inteligencia Normativa: modelos, conector resiliente a la SPDP, validación SHA-256 y custodia del original"
ola = "D"
estado = "pendiente"
sala = "inteligencia_normativa"
depende_de = ["ADPA-05", "ADPA-06", "GCP-01"]
propiedad = ["alembic/versions/20261104_norm01_inteligencia_normativa.py", "features/inteligencia_normativa/__init__.py", "features/inteligencia_normativa/models.py", "features/inteligencia_normativa/schemas.py", "features/inteligencia_normativa/inteligencia_normativa_service.py#NORM-01", "features/inteligencia_normativa/domain/__init__.py", "features/inteligencia_normativa/domain/errores.py#NORM-01", "features/inteligencia_normativa/services/__init__.py", "features/inteligencia_normativa/services/conector_spdp.py", "features/inteligencia_normativa/services/deduplicacion.py", "features/inteligencia_normativa/services/monitoreo.py", "app_core/pasillo/inteligencia_normativa.py#NORM-01", "tests/test_norm01_inteligencia_normativa.py"]
arbitro = "pytest tests/test_norm01_inteligencia_normativa.py contra un PostgreSQL 16 local en contenedor + suite completa + vigilantes"
rastros = ["¤inteligencia-normativa", "¤vigilancia-spdp", "¤adpa"]
+++
# NORM-01 · Sala Inteligencia Normativa: modelos, conector resiliente a la SPDP, validación SHA-256 y custodia del original

**Origen.** `PRD_EVYDENTIA_REVENTA_NUBE.md`, Módulo 6.1 (BRF-001, `RF-01..05`) e invariantes 39 a 42. El tablero `TASKS_EVYDENTIA_REVENTA_NUBE.md` la citaba (BL-187, tanda 44) sin ficha; esta es la ficha.

**Contrato:** `governance/especificaciones/NORM-01.md`.

## Entrega
- Tablas globales `normativa_resoluciones`, `normativa_versiones` y `normativa_monitoreo_logs`: el corpus normativo es público y común a todas las organizaciones, así que no lleva `tenant_id`. `lopdp_app` solo puede leer; escribe el proceso de monitoreo con un rol propio.
- Conector `services/conector_spdp.py` hacia las secciones oficiales de la SPDP (`/resoluciones/`, `/marco-normativo/`, `/consultas-absueltas/`): peticiones en serie, pausa de cortesía, reintentos con espera exponencial y `User-Agent` genérico de la plataforma.
- Validación en `services/deduplicacion.py`: cabecera `%PDF-`, SHA-256 calculado mientras se descarga y deduplicación en tres capas (número y año, hash, cambio en la fuente).
- El original se guarda intacto, por `app_core/storage`, con el hash como nombre. Va a GCS (`gs://evydentia-corpus-normativo/spdp/`), sin pasar por R2.
- Corrida de monitoreo en `services/monitoreo.py`, invocable a mano. Se programa a las 05:00 en `America/Guayaquil` con Cloud Scheduler tras GCP-01; cada corrida queda registrada.
- Compuerta `inteligencia_normativa_service.py#NORM-01` y pasillo `app_core/pasillo/inteligencia_normativa.py#NORM-01`.

## Decisiones asumidas
- Todo documento nuevo entra como `pendiente_revision`; ninguno pasa a `vigente` sin validación humana (NORM-02 y NORM-03).
- El conector no evade controles del sitio: si la SPDP bloquea o pide verificación, la corrida se registra como fallida y se avisa; no se reintenta en bucle.

## Pruebas
- `pytest tests/test_norm01_inteligencia_normativa.py`, con un servidor HTTP simulado, comprueba:
  - el rechazo de lo que no es PDF;
  - el SHA-256 en streaming;
  - las tres capas de deduplicación, en especial que el mismo número con otro hash crea una versión sin sobrescribir;
  - la espera exponencial;
  - el registro de cada corrida;
  - que `lopdp_app` no puede escribir en las tablas.
