+++
id = "NORM-05"
titulo = "El backend no adopta el rol del monitoreo: revisión con UPDATE por columna y disparo manual que lanza el Job"
ola = "backlog"
estado = "pendiente"
tanda = 104
sala = "inteligencia_normativa"
depende_de = ["NORM-01", "NORM-02", "NORM-03", "NORM-04"]
propiedad = ["features/inteligencia_normativa/services/revision.py", "features/inteligencia_normativa/inteligencia_normativa_service.py#NORM-05", "api/routers/inteligencia_normativa.py#NORM-05", "features/inteligencia_normativa/services/lanzador_trabajo.py", "alembic/versions/norm05_revision_sin_rol_monitoreo.py", "tests/test_norm05_privilegios_backend.py", "tests/test_norm02_centro_vigilancia.py"]
crea = ["features/inteligencia_normativa/services/lanzador_trabajo.py", "alembic/versions/norm05_revision_sin_rol_monitoreo.py", "tests/test_norm05_privilegios_backend.py"]
arbitro = "pytest tests/test_norm05_privilegios_backend.py tests/test_norm02_centro_vigilancia.py tests/test_norm01_inteligencia_normativa.py tests/test_alembic_cabeza_por_sala.py contra PostgreSQL, conectado como lopdp_app; mutaciones m1 a m5."
rastros = ["¤vigilancia-spdp", "¤inteligencia-normativa", "¤seguridad", "¤arbitro", "¤monitoreo-job"]
+++

# NORM-05 · El backend no adopta el rol del monitoreo

**Contrato:** `governance/especificaciones/NORM-05.md` (manda sobre esta ficha).

**Origen.** Hallazgo del CTO (2026-11-24), medido por el Arquitecto: ninguna migración concede `lopdp_normativa` a `lopdp_app`, pero el backend hace `SET LOCAL ROLE lopdp_normativa` al revisar una resolución. En producción, «Revisar» de NORM-02 daría `permission denied`.

## Entrega
- La revisión escribe como `lopdp_app`, con `UPDATE` solo sobre sus cuatro columnas.
- El disparo manual del operador lanza el Job del monitoreo de NORM-04, en lugar de correr el monitoreo dentro del backend.
- Una prueba conectada como `lopdp_app`: revisa, pero no inserta versiones ni bitácora.
- `test_bitacora_y_disparo_manual` de `tests/test_norm02_centro_vigilancia.py` pasa a esperar el lanzamiento del Job, con el lanzador sustituido por un doble.

## Límites
- El monitoreo (NORM-01, NORM-02b y NORM-04) sigue escribiendo como `lopdp_normativa` desde su Job.
- NORM-03 no cambia: ya escribe como `lopdp_app` con sus propios permisos.
- El permiso del backend para lanzar el Job lo concede el propietario (brief).
