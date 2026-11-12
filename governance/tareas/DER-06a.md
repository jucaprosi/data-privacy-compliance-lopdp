+++
id = "DER-06a"
titulo = "Tipos nuevos de solicitud (suspensión, decisiones automatizadas, queja): expandir el enum sin activarlos"
ola = "backlog"
estado = "hecha"
sala = "derechos_arco"
depende_de = ["DER-05"]
propiedad = ["alembic/versions/20261123_der06a_tipos_solicitud.py", "features/derechos_arco/domain/models.py", "features/derechos_arco/domain/plazos.py", "features/derechos_arco/derechos_arco_service.py", "api/routers/arco_router.py", "tests/test_der06a_tipos_expandir.py"]
crea = ["alembic/versions/20261123_der06a_tipos_solicitud.py", "tests/test_der06a_tipos_expandir.py"]
arbitro = "pytest tests/test_der06a_tipos_expandir.py contra el PostgreSQL 16 del arnés + tests/test_alembic_una_cabeza.py; mutaciones documentadas"
rastros = ["¤regulation-code", "¤arbitro"]
+++

# DER-06a · Tipos nuevos de solicitud (suspensión, decisiones automatizadas, queja): expandir el enum sin activarlos

Diseño del Arquitecto ADPA (2026-11-09). Primera mitad de «expandir y contraer». Plazos por tipo de solicitud: 15 días (arts. 13 a 16: acceso, rectificación, eliminación, oposición) y 10 días (art. 62: portabilidad, suspensión, decisiones automatizadas y quejas), validado por un abogado local, comunicado por el propietario el 2026-11-09; el documento del abogado no consta en el repositorio. Fuente: PR #557 y #558 de Aleczandra. La unidad (hábiles o corridos) sigue pendiente y la regla provisional son días corridos, marcada como estimada.

## El problema
El tipo nativo `tiposolicitud` lo creó la migración 20261020 con cinco valores y el modelo lo lee con `Enum(TipoSolicitud)`. Si se añade un valor y una fila lo usa, la revisión anterior de Cloud Run, que sigue sirviendo durante el despliegue progresivo, falla al listar las solicitudes porque no conoce el valor. El verificador de GCP-07 (`scripts/verificar_migracion_compatible.py`) solo atrapa DROP y RENAME, no esto: por eso esta ficha lleva su propia prueba. PostgreSQL no permite retirar valores de un tipo nativo: **la contracción no existe y no se promete**.

## Entrega
- Migración nueva con `ALTER TYPE tiposolicitud ADD VALUE IF NOT EXISTS …` para suspensión, decisiones automatizadas y queja. Su `down_revision` es la cabeza vigente al lanzar (medida con `ScriptDirectory`; hoy `20261106_diag_prueba_y_real`). Es la primera de las migraciones pendientes de derechos (DER-01, DER-02), pequeña y aislada. Aplica FUSION_ALEMBIC.
- `models.py` y `plazos.py` aceptan leer los tres valores (10 días cada uno). Un solo punto de activación: `TIPOS_ACTIVOS` en `plazos.py`, sin los tres.
- **El rechazo vive en la compuerta:** `crear_solicitud_arco` de `derechos_arco_service.py` rechaza **crear** un tipo no activo con un error de dominio («tipo no disponible») y no crea fila. Tiene que estar ahí y no solo en el router, porque el portal público de DER-02 también llama a esa función. Por eso esta ficha toma `derechos_arco_service.py` entero (DER-05, que ya es dueña del archivo entero, está hecha antes) y `arco_router.py` solo traduce el error.

## Árbitros (PostgreSQL 16 del arnés)
- (a) Tras la migración, un lector con una copia congelada del enum de cinco valores lista sin error todas las filas existentes y las que se creen mientras los tipos nuevos están inactivos.
- (b) Crear un tipo nuevo con `TIPOS_ACTIVOS` sin ellos devuelve el error y no crea fila.
- (c) La migración es idempotente: aplicarla dos veces no falla.
- Mutación que demuestra el porqué: activar un tipo nuevo, crear una fila y comprobar que el lector de cinco valores falla con `LookupError`. Otra mutación: quitar el rechazo de creación.
