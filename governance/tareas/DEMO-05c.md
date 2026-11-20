+++
id = "DEMO-05c"
titulo = "Purga de la demo con políticas explícitas por rol, sin BYPASSRLS, y guardia que falla cerrada si falta alguna"
ola = "backlog"
estado = "pendiente"
sala = "demo"
depende_de = ["DEMO-05", "SEC-20", "DEMO-05b"]
propiedad = ["jobs/purga_demo/politicas_purga.sql", "jobs/purga_demo/guardias.py", "jobs/purga_demo/__main__.py", "governance/operaciones/BRIEF_PROPIETARIO_DEMO05.md", "tests/test_demo05c_politicas_purga.py", "jobs/purga_demo/purga.py", "jobs/purga_demo/usuarios.py", "tests/test_demo_purga_usuarios.py"]
crea = ["jobs/purga_demo/politicas_purga.sql", "tests/test_demo05c_politicas_purga.py"]
arbitro = "pytest tests/test_demo05c_politicas_purga.py tests/test_demo_purga_usuarios.py con TEST_DATABASE_URL de PostgreSQL 16, en transacción revertida; las pruebas de DEMO-05b pasan sin cambiarlas; mutaciones m1 a m9."
rastros = ["¤demo"]
+++

# DEMO-05c · Purga de la demo con políticas explícitas por rol

**Contrato:** `governance/especificaciones/DEMO-05c.md` (manda sobre esta ficha).

Diseño del Arquitecto ADPA (2026-11-12) por decisión del CTO: política explícita, sin `BYPASSRLS`. Es el paso 5 del brief del propietario de DEMO-05. Decisiones del CTO del 2026-11-19 sobre las tablas sin RLS, `usuarios.py` y la persona ficticia, aplicadas en la especificación.

## Entrega
- `jobs/purga_demo/politicas_purga.sql`: permisos y políticas `TO purga_demo` con el marcador `demo`; en las tablas sin RLS, solo los permisos; `demo_sesiones` por columnas; `users` solo `SELECT (id)`; la función `es_persona_ficticia` (`SECURITY DEFINER`, solo el criterio del correo y el marcador, `EXECUTE` solo para `purga_demo`).
- Guardias `faltan_politicas` y `tablas_sin_rls` en `guardias.py`; `faltan_politicas` se llama desde `__main__.py` antes de `purgar` y vigila también la función y el correo.
- `purga.py` sin el `UPDATE demo_sesiones`, con `purgar_tenant` que acepta un `Engine` o una `Connection`.
- `usuarios.py`: `es_persona_ficticia` en vez de leer el correo, y la comprobación de sesiones solo con las que tienen organización.
- Paso 5 del brief `BRIEF_PROPIETARIO_DEMO05.md` con las comprobaciones de solo lectura.
- `tests/test_demo_purga_usuarios.py`: solo casos añadidos; las pruebas de DEMO-05b no se reescriben.

## Límites
- La RLS de las cinco tablas sin ella no se activa aquí: la ficha de seguridad que da de alta el Arquitecto lo hace por Alembic.
- Los triggers de inmutabilidad de la biblioteca los resuelve DEMO-05d, que va después y comparte `jobs/purga_demo/`.
- Nada en Alembic.
