+++
id = "SEC-10"
titulo = "Cerrar la llave maestra: credencial del dueño solo para migraciones, producción como lopdp_app y permisos mínimos en users y tenants"
ola = "D"
estado = "pendiente"
sala = "gobernanza"
depende_de = ["SEC-02", "SEC-03"]
propiedad = ["governance/operaciones/CREDENCIALES_Y_ROLES_BD.md", "tests/test_permisos_tablas_globales.py"]
arbitro = "pytest tests/test_permisos_tablas_globales.py + suite completa contra una rama Neon propia; el propietario sigue el procedimiento y confirma producción"
rastros = ["¤seguridad", "¤rbac-tenant"]
+++

# SEC-10 · Cerrar la llave maestra

**Objetivo.** Medido el 2026-10-21 en la rama `test` (solo lectura): el rol dueño `lopdp_beta_owner` es miembro de `neon_superuser` y tiene **`BYPASSRLS`**, de modo que quien use esa credencial ve los datos de **todas** las organizaciones, con RLS forzado o sin él. La aplicación de producción conecta como `lopdp_app` según el `.env` local (sin `BYPASSRLS`, el RLS sí se aplica), pero la configuración real del despliegue no está verificada. Además, las tablas globales `tenants` y `users` **no tienen RLS**. Y otra sesión informó de que la contraseña del dueño se expuso en una conversación.

## Entrega
- `governance/operaciones/CREDENCIALES_Y_ROLES_BD.md`: inventario de roles (`lopdp_beta_owner`, `lopdp_app`) con sus atributos reales (`BYPASSRLS`, superusuario) obtenidos por consulta de solo lectura; qué credencial usa cada cosa (aplicación, migraciones, CI, pruebas); y el **procedimiento para el propietario**, completo y pegable: comprobar con qué usuario conecta el despliegue de producción (sin mostrar contraseñas), rotar la contraseña del dueño y actualizar a la vez todos los sitios que la usan (`.env`, archivos de ramas, secreto del CI, despliegue) sin dejar producción sin conexión.
- `tests/test_permisos_tablas_globales.py`, con base real: los privilegios de `lopdp_app` sobre `tenants` y `users` son los mínimos que usa el código (inventariados con `git grep` de las consultas reales) y no incluyen `DELETE`; la aplicación no conecta con un rol con `BYPASSRLS` (comprobando el rol de la URL de la aplicación cuando esté disponible). Sin SQL interpolado.
- Un análisis, dentro del documento, de si `users` y `tenants` necesitan RLS o vistas restringidas: qué consultas del código leen esas tablas sin filtrar por organización (por ejemplo, la búsqueda del usuario por su identidad de Google) y qué se rompería al protegerlas. Recomendación argumentada; **no se aplica RLS a esas tablas en esta tarea**.
- **Prueba de mutación documentada:** conceder a propósito `DELETE` sobre `users` a `lopdp_app` en la rama de pruebas y comprobar que la prueba falla; revocarlo y comprobar que pasa.

## Límites
- No rota contraseñas ni cambia la configuración del despliegue: eso lo hace el propietario con el procedimiento.
- No cambia el código de la aplicación ni de las migraciones existentes.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
