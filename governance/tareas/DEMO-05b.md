+++
id = "DEMO-05b"
titulo = "Purga de las personas ficticias de users"
ola = "backlog"
estado = "pendiente"
sala = "operaciones"
depende_de = ["DEMO-05"]
propiedad = ["jobs/purga_demo/usuarios.py", "jobs/purga_demo/purga.py", "tests/test_demo_purga_usuarios.py"]
crea = ["jobs/purga_demo/usuarios.py", "tests/test_demo_purga_usuarios.py"]
arbitro = "pytest tests/test_demo_purga_usuarios.py tests/test_demo_purga.py contra el PostgreSQL 16 del arnés; mutaciones documentadas"
rastros = ["¤arbitro"]
+++

# DEMO-05b · Purga de las personas ficticias de users

Diseño del Arquitecto ADPA y decisiones del CTO (2026-11-09). Sale de la revisión de DEMO-05 (#570). Es otra superficie de seguridad: borra en `users`, que no tiene `tenant_id` ni RLS. Sin migración.

## Personas ficticias huérfanas de `users`
La purga de DEMO-05 deja huérfanas las personas ficticias (correo `.invalid`) de cada demo vencida y se acumulan noche a noche. La marca estructural ya existe: `tenants.es_demo` (DEMO-00). La regla, en este orden y todo en una sola transacción:
1. **Antes** de borrar filas de roles, el job lee los `user_id` con algún rol en `user_tenant_roles` de un tenant `es_demo` vencido que se está purgando.
2. Tras purgar, borra de ese conjunto **solo** a quien cumpla las cuatro: ningún rol restante en ningún tenant (plantilla, demo activa ni real); ninguna fila de `demo_sesiones` lo apunta (la purga deja `persona_usuario_id` en nulo); el correo termina en `.invalid` (segunda guarda, no la regla); y su única pertenencia fue a esos tenants vencidos.
3. Un `.invalid` sin ningún rol en el conjunto del paso 1 **no se toca**: no se puede probar que sea de la demo.
- **Por comprobar con DEMO-03a antes de repartir:** que las seis personas se crean con correo `.invalid` y que su relación con el tenant pasa por `user_tenant_roles`. Si DEMO-03a las comparte con la plantilla, la regla ya las protege.
- El rol de base de datos de la purga necesita `DELETE` sobre `users` y `SELECT` sobre `user_tenant_roles`; se pide en el brief de GCP de la demo, no en una migración.

## Versionado de buckets: ya hecho en DEMO-05
El rechazo de buckets con versionado activo (`versioning_enabled`) lo entregó DEMO-05 en el #575, mientras seguía `en_curso`. Esta ficha ya no lo lleva.

## Árbitros (PostgreSQL 16 del arnés; cada uno con su mutación)
- Se borra el usuario `.invalid` cuyos roles eran solo de demos vencidas.
- Se conserva un usuario real (correo sin `.invalid`) con un rol en una demo vencida.
- Se conserva un usuario con un rol en la plantilla.
- Se conserva un `.invalid` con un rol en una demo activa.
- Se conserva un `.invalid` sin ningún rol.
- Mutación común: quitar la comprobación de «ningún rol restante».
