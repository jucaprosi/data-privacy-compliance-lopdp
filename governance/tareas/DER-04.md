+++
id = "DER-04"
titulo = "Contracción de DER-03: retirar la columna tenant_id uuid y el trigger de compatibilidad de las solicitudes ARCO"
ola = "backlog"
estado = "pendiente"
sala = "derechos_arco"
depende_de = ["DER-03"]
propiedad = ["alembic/versions/20261109_derechos_contraccion_tenant.py", "tests/test_der04_contraccion.py", "governance/apoyo/BRIEF_PROPIETARIO_DER04.md"]
crea = ["alembic/versions/20261109_derechos_contraccion_tenant.py", "tests/test_der04_contraccion.py", "governance/apoyo/BRIEF_PROPIETARIO_DER04.md"]
arbitro = "pytest tests/test_der04_contraccion.py + suite completa + verificar_migracion_compatible.py; FUSION_ALEMBIC"
rastros = ["¤arbitro"]
+++

# DER-04 · Contracción de la migración de DER-03

Diseño del Arquitecto ADPA (2026-11-08). DER-03 aplica la fase de expansión (GCP-07): columna de texto nueva, FK `NOT VALID` más `VALIDATE`, y un trigger para la revisión estable. Esta ficha es la contracción, en una migración marcada con `CONTRACCION = True`.

## Criterio para desplegar (deben cumplirse las tres)
a. **Código.** Fuera de `alembic/versions`, ningún archivo de `features/`, `api/`, `app_core/`, `scripts/` ni `frontend/src` nombra la columna vieja ni el trigger: el `git grep` da 0. Lo comprueba la prueba 7.
b. **Servicio.** Lo comprueba el propietario con el brief, porque GCP es suyo, usando `gcloud run services describe` y `gcloud run jobs describe` en modo lectura. Cada pieza que toca la base sirve el 100 % del tráfico con una revisión que ya incluye DER-03, y ninguna revisión anterior tiene tráfico ni etiqueta. Esas piezas son:
   - el backend;
   - el frontend, si hace SSR contra la base;
   - el vault worker;
   - los Jobs purga-demo y migración.
c. **Ventana de vuelta atrás cerrada.** El propietario confirma por escrito que DER-03 lleva en servicio al menos una publicación completa sin vuelta atrás. Se proponen 7 días o el fin de la demo; el plazo lo decide él.

`governance/apoyo/BRIEF_PROPIETARIO_DER04.md` recoge (b) y (c) con sus comandos.

## Migración
1. En la misma transacción y antes de cualquier DDL, cuenta las filas cuyo tenant nuevo es NULL o no tiene fila correspondiente en `tenants`. Si hay alguna, aborta con el número de filas y sin ningún dato de ellas, ni cédulas ni nombres.
2. Si no hay ninguna, pone la columna nueva en NOT NULL (si DER-03 no lo hizo) y luego retira el trigger y la columna vieja, en ese orden.
3. Comprueba que la política RLS y FORCE siguen sobre la columna de texto.
4. `downgrade()` lanza un error explícito de «contracción irreversible»: un uuid no se puede reconstruir a partir de un tenant de texto.
5. FUSION_ALEMBIC: va después de DER-03, y también de DER-01 y DER-02 si tienen migración. El orden lo fija `down_revision`, no la fecha del nombre.

## Pruebas (PostgreSQL real, sin producción ni Cloud SQL)
1. Con una fila con tenant NULL, `upgrade` aborta y la tabla, la columna vieja y el trigger quedan intactos.
2. El mensaje de aborto no contiene datos de la fila.
3. Sin huérfanos, `upgrade` retira la columna vieja y el trigger, y la nueva queda NOT NULL.
4. Con `lopdp_app`, después del `upgrade` un tenant no ve las solicitudes de otro.
5. `downgrade` lanza el error.
6. `verificar_migracion_compatible.py` acepta el archivo solo con `CONTRACCION = True`.
7. El `git grep` de la condición (a) da 0.

**Mutaciones:**
- M1: quitar `CONTRACCION` deja en rojo la prueba 6.
- M2: mover la guardia después del DROP deja en rojo la prueba 1.
- M3: imprimir la fila en el aborto deja en rojo la prueba 2.

Sin `import yaml` en las pruebas.
