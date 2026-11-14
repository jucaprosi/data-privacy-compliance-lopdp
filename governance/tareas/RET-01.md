+++
id = "RET-01"
titulo = "Configuración solo por variables de entorno y guardia de base local"
ola = "backlog"
estado = "pendiente"
sala = "pasillo_central"
depende_de = ["RET-00", "BIB-117", "BIB-205", "CI-07", "CI-08", "CI-09", "DEMO-03", "DEP-01", "EP-01", "EP-03", "EP-10", "EP-11", "FIRMA-06", "MARCA-01", "NEON-01", "NEON-04", "SEC-16", "SEC-17", "SEC-20"]
propiedad = ["app_core/config.py", "app_core/huellas_produccion.py", "app_core/entorno/guardias.py", "requirements.txt", ".env.example", "governance/operaciones/ENTORNO_LOCAL.md", "scripts/entorno_local.ps1", "tests/conftest.py", "alembic/env.py", ".githooks/pre-push", "scripts/capacidades_biblioteca.py", "scripts/crear_organizacion_dev.py", "scripts/demo/sembrar_plantilla.py", "scripts/sembrar_entorno_pruebas.py", "tests/test_sec15_guarda_arranque.py", "tests/test_ret01_configuracion.py", "tests/plataforma_unica/pendientes/RET-01.txt"]
crea = ["scripts/entorno_local.ps1", "tests/test_ret01_configuracion.py"]
arbitro = "pytest tests/test_ret01_configuracion.py tests/test_sec15_guarda_arranque.py tests/test_sec16_secretos_obligatorios.py tests/test_plataforma_unica.py contra un PostgreSQL 16 local + suite completa; prueba de mutación documentada por cada prueba nueva; revisión de Seguridad"
rastros = ["¤seguridad", "¤arbitro"]
+++

# RET-01 · Configuración solo por variables de entorno

Diseño del Arquitecto ADPA (2026-11-13): `governance/especificaciones/RET-01.md`. Modelo sugerido: **opus** (toca la guardia de arranque y los invariantes SEC-15, SEC-16 y SEC-20). Va después de RET-00. SEC-24 (sin tenant por defecto en la dependencia común) debe entrar antes: comparte con esta ficha la dependencia común de la cabecera de organización; la dependencia formal se declara cuando SEC-24 tenga su bloque.

**Problema.** La configuración debe salir solo del proceso (variables de entorno y Secret Manager). Hoy `app_core/config.py` carga un archivo de entorno y varios puntos de entrada repiten, cada uno por su cuenta, la comprobación de la base.

**Entrega.**
- `app_core/config.py` sin carga de archivo de entorno; `requirements.txt` sin `python-dotenv`; se retira `.env.example`.
- Una sola función de guardia en `app_core` para la suite de pruebas y los modos de desarrollo, usada por `tests/conftest.py`, `alembic/env.py`, `.githooks/pre-push`, `app_core/entorno/guardias.py` y los scripts que usan las huellas. Permite solo `localhost`, `127.0.0.1`, `::1` y el servicio de base del CI.
- `governance/operaciones/ENTORNO_LOCAL.md` y `scripts/entorno_local.ps1` (nuevo): variables en la ventana de PowerShell, sin secretos ni URLs reales.
- `app_core/huellas_produccion.py` queda con `K_SERVICE` como variable de nube; SEC-15, SEC-16 y SEC-20 siguen verdes.

**Decisión del CTO (2026-11-13) sobre `/cloudsql/`.** El socket `/cloudsql/` no cuenta como base local: es la base de la nube. La guardia «solo local o CI» rige para la suite y los modos de desarrollo, no para el arranque de producción, que sigue su propio camino con `HUELLA_PROYECTO_PRODUCCION` (SEC-15 y SEC-20). Dos pruebas lo dejan escrito: `test_cloudsql_no_es_local` y `test_arranque_produccion_usa_huella_del_proyecto`.

**Choques medidos.** `jobs/purga_demo/guardias.py` pertenece a DEMO-05c y DEMO-05d: esta ficha no lo edita y conserva la firma pública de `huellas_produccion` que ese archivo importa. `requirements.txt` también lo tocan RET-02 e IA-08: el orden es RET-01 → RET-02 → IA-08. El archivo del arnés citado en la especificación no existe en `main`; la guardia se aplica a los puntos de entrada que sí existen.

