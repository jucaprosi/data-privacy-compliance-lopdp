+++
id = "RET-05"
titulo = "Una sola entrada de la API y despliegue solo en Cloud Run"
ola = "backlog"
estado = "pendiente"
sala = "operaciones, frontend"
depende_de = ["RET-01", "CI-02", "CI-03", "CI-09", "CI-10", "CI-17", "DEMO-08", "EP-03", "GCP-03", "GCP-08", "GOB-04", "MARCA-01", "NEON-01", "OPS-06", "RET-03"]
propiedad = ["vercel.json", "frontend/vercel.json", "api/index.py", "frontend/public/vercel.svg", ".gitignore", "frontend/.gitignore", "tests/test_vercel_despliegue.py", "tests/test_cabeceras_seguridad.py", "tests/test_health_routers.py", "tests/test_gcp03_frontend_cloudrun.py", "tests/test_ret05_una_entrada.py", "pytest.ini", "app_core/security.py", "app_core/bucle_eventos.py", "api/routers/firma_anf.py", "features/roadmap/services/generacion_en_linea.py", "frontend/src/lib/auth/modo.ts", "frontend/next.config.cloudrun.ts", "tests/humo/servidor_humo.py", "tests/test_servidor_humo.py", "tests/plataforma_unica/pendientes/RET-05.txt"]
crea = ["tests/test_ret05_una_entrada.py"]
arbitro = "pytest tests/test_ret05_una_entrada.py tests/test_cabeceras_seguridad.py tests/test_health_routers.py tests/test_sec16_secretos_obligatorios.py tests/test_sec17_configuracion_nube.py + Playwright de frontend/tests/humo/01_arranque.spec.ts + tsc --noEmit + npm run build + suite completa; prueba de mutación documentada"
rastros = ["¤arquitectura", "¤frontend-ide"]
+++

# RET-05 · Una sola entrada de la API

Diseño del Arquitecto ADPA (2026-11-13): `governance/especificaciones/RET-05.md`. Modelo sugerido: sonnet. Va después de RET-01. SEC-21, que posee `test_sec16_secretos_obligatorios.py` y `test_sec17_configuracion_nube.py`, debe cambiar antes en su propio PR el import de `api.index` a `main` (si no, retirar `api/index.py` las rompe): esos dos archivos quedan fuera de esta ficha y la dependencia formal se declara cuando SEC-21 tenga su bloque.

**Problema.** `main.py` (`main:app`) es la entrada de Cloud Run, pero el árbol conserva una segunda entrada (`api/index.py`) y archivos de configuración de despliegue que ya no se usan.

**Entrega.**
- Se retiran `vercel.json` (raíz y `frontend/`), `api/index.py`, `frontend/public/vercel.svg` (si ninguna pantalla lo muestra; si alguna lo muestra, pasa por UX/UI) y las entradas correspondientes de los `.gitignore`.
- Dos pruebas cambian en la misma ficha porque dependían de lo retirado: `test_cabeceras_seguridad.py` (el tiempo máximo de 300 s de RM-13 pasa a comprobarse en el manifiesto de Cloud Run) y `test_health_routers.py` (ahora comprueba que `main.app` expone `/health`). Las otras dos que importaban `api.index` (`test_sec16_secretos_obligatorios.py` y `test_sec17_configuracion_nube.py`) las cambia SEC-21. Se retira `tests/test_vercel_despliegue.py`.
- Los comentarios y nombres de `pytest.ini`, `app_core/security.py`, `bucle_eventos.py`, `firma_anf.py`, `generacion_en_linea.py` y `frontend/src/lib/auth/modo.ts` describen la plataforma actual.
- `.github/workflows/` es del propietario: si algún workflow nombra lo retirado, va un brief.

**Cruce con GCP-11.** El diagnóstico de la revisión 00006 comprueba si arranca con una entrada distinta de `main:app` (por ejemplo `api.index`); si lo hace, el hallazgo se usa antes de retirar `api/index.py`.

**No se lanza todavía.** La dependencia de texto con SEC-21 se acepta en este PR, pero RET-05 no se lanza hasta que el segundo PR de gobernanza la declare en `depende_de`.

**Nota.** `app_core/config.py` lo posee RET-01 (va antes); esta ficha solo ajusta comentarios después de ella.

