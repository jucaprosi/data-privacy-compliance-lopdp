+++
id = "NORM-07"
titulo = "Fecha de vigencia opcional al revisar una resolución, y la revisión dispara la propuesta de la IA"
ola = "D"
estado = "pendiente"
tanda = 109
sala = "inteligencia_normativa"
depende_de = ["BIB-406"]
propiedad = ["alembic/versions/20261125_norm07_fecha_vigencia.py", "features/inteligencia_normativa/services/revision.py", "features/inteligencia_normativa/inteligencia_normativa_service.py", "api/routers/inteligencia_normativa.py", "app_core/pasillo/inteligencia_normativa.py", "frontend/src/components/normativa/PanelResolucion.tsx", "frontend/src/components/normativa/cliente.ts", "tests/test_norm05_privilegios_backend.py", "tests/test_norm07_fecha_vigencia.py"]
crea = ["alembic/versions/20261125_norm07_fecha_vigencia.py", "tests/test_norm07_fecha_vigencia.py"]
arbitro = "pytest tests/test_norm07_fecha_vigencia.py tests/test_norm05_privilegios_backend.py tests/test_alembic_cabeza_por_sala.py tests/test_adpa_bulkhead.py; mutaciones m1 a m5."
rastros = ["¤monitoreo-job", "¤arbitro"]
+++

# NORM-07 · Fecha de vigencia opcional al revisar una resolución, y la revisión dispara la propuesta de la IA

**Contrato:** `governance/especificaciones/NORM-07.md` (manda sobre esta ficha).

**Origen.** Brief del CTO `ARQUITECTO_UXUI_PROPUESTAS_IA_PLANTILLAS` v1, v2 y v3 (2026-11-25), base `origin/main` ed575cd2, con las decisiones D1 a D7 del CTO y la propuesta de pantallas y textos del UX/UI (2026-11-25).

## Entrega
- Columna `fecha_vigencia` en `normativa_resoluciones`, con su permiso de UPDATE.
- `revisar_estado` la acepta y, con `reformada`, `derogada` o `vigente`, llama a `proponer_por_resolucion` por el pasillo de la biblioteca.
- El pasillo de la sala expone la fecha. El panel de la resolución tiene el campo.
- Prueba exógena con mutaciones.

## Límites
- En `test_norm05_privilegios_backend.py` (NORM-05, hecha) solo cambia la lista de columnas con UPDATE, que gana `fecha_vigencia`; el resto de los privilegios no cambia.
- En `inteligencia_normativa_service.py` solo cambia `revisar_estado`.
