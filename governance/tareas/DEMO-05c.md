+++
id = "DEMO-05c"
titulo = "Purga de la demo con políticas explícitas por rol, sin BYPASSRLS, y guardia que falla cerrada si falta alguna"
ola = "backlog"
estado = "pendiente"
sala = "demo"
depende_de = ["DEMO-05", "SEC-20", "DEMO-05b"]
propiedad = ["jobs/purga_demo/politicas_purga.sql", "jobs/purga_demo/guardias.py", "jobs/purga_demo/__main__.py", "governance/operaciones/BRIEF_PROPIETARIO_DEMO05.md", "tests/test_demo05c_politicas_purga.py", "jobs/purga_demo/purga.py"]
crea = ["jobs/purga_demo/politicas_purga.sql", "tests/test_demo05c_politicas_purga.py"]
arbitro = "pytest tests/test_demo05c_politicas_purga.py con TEST_DATABASE_URL de PostgreSQL 16; mutaciones m1 a m5."
rastros = ["¤demo"]
+++

# DEMO-05c · Purga de la demo con políticas explícitas por rol

**Contrato:** `governance/especificaciones/DEMO-05c.md` (manda sobre esta ficha).

Diseño del Arquitecto ADPA (2026-11-12) por decisión del CTO: política explícita, sin `BYPASSRLS`. Es el paso 5 del brief del propietario de DEMO-05.

## Entrega
- `jobs/purga_demo/politicas_purga.sql`: permisos y políticas `TO purga_demo` con el marcador `demo`, la plantilla fuera en la base, `tenants` solo vencidos, `demo_sesiones` por columnas y caducidad a 90 días.
- Guardia `faltan_politicas` en `guardias.py`, llamada desde `__main__.py` antes de `purgar`.
- `purga.py` sin el `UPDATE demo_sesiones`.
- Paso 5 del brief `BRIEF_PROPIETARIO_DEMO05.md` con la comprobación de solo lectura.

## Límites
- Los triggers de inmutabilidad de la biblioteca los resuelve DEMO-05d (opción a, confirmada por el CTO), que va después y comparte `jobs/purga_demo/`.
- Nada en Alembic.
