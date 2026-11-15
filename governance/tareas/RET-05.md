+++
id = "RET-05"
titulo = "Una sola entrada de la API y despliegue solo en Cloud Run"
ola = "backlog"
estado = "hecha"
sala = "operaciones, frontend"
depende_de = ["RET-01", "CI-02", "CI-03", "CI-09", "CI-10", "CI-17", "DEMO-08", "EP-03", "GCP-03", "GCP-08", "GOB-04", "MARCA-01", "OPS-06", "RET-03", "CI-29"]
propiedad = [".gitignore", "frontend/.gitignore", "tests/test_cabeceras_seguridad.py", "tests/test_health_routers.py", "tests/test_gcp03_frontend_cloudrun.py", "tests/test_ret05_una_entrada.py", "pytest.ini", "app_core/security.py", "app_core/bucle_eventos.py", "api/routers/firma_anf.py", "features/roadmap/services/generacion_en_linea.py", "frontend/src/lib/auth/modo.ts", "frontend/next.config.cloudrun.ts", "tests/humo/servidor_humo.py", "tests/test_servidor_humo.py", "frontend/.dockerignore", "frontend/README.md", "frontend/tests/seguridad/cabeceras.spec.ts", "frontend/package-lock.json", "frontend/pnpm-lock.yaml", "frontend/package.json"]
crea = ["tests/test_ret05_una_entrada.py"]
arbitro = "pytest tests/test_ret05_una_entrada.py tests/test_cabeceras_seguridad.py tests/test_health_routers.py tests/test_sec16_secretos_obligatorios.py tests/test_sec17_configuracion_nube.py + Playwright de frontend/tests/humo/01_arranque.spec.ts + tsc --noEmit + npm run build + suite completa; prueba de mutación documentada"
rastros = ["¤arquitectura", "¤frontend-ide"]
+++

# RET-05 · Una sola entrada de la API

Diseño del Arquitecto ADPA (2026-11-13): `governance/especificaciones/RET-05.md`. Modelo sugerido: sonnet. Va después de RET-01. SEC-21, que posee `test_sec16_secretos_obligatorios.py` y `test_sec17_configuracion_nube.py`, alinea los imports hacia `main`: esos dos archivos quedan fuera de esta ficha y la dependencia formal se declara cuando SEC-21 tenga su bloque.

**Problema.** `main.py` (`main:app`) es la entrada de Cloud Run, pero la aplicación consolida su entrada única en `main:app` para el despliegue integral en Cloud Run.

**Entrega.**
- La entrada única de backend es `main:app` desplegada en Cloud Run, con `.gitignore` depurados y recursos estáticos limpios en `frontend/public/`.
- `test_cabeceras_seguridad.py` verifica las cabeceras en `next.config.ts` y el timeout de 300 s en el manifiesto de Cloud Run; `test_health_routers.py` verifica que `main.app` expone `/health`, y `test_sec16_secretos_obligatorios.py` y `test_sec17_configuracion_nube.py` importan `main`.
- Comentarios y nombres en `pytest.ini`, `app_core/security.py`, `bucle_eventos.py`, `firma_anf.py`, `generacion_en_linea.py` y `frontend/src/lib/auth/modo.ts` reflejan Cloud Run.

**Cruce con GCP-11.** El diagnóstico verifica directamente el arranque único mediante `main:app`.

**No se lanza todavía.** La dependencia de texto con SEC-21 se acepta en este PR, pero RET-05 no se lanza hasta que el segundo PR de gobernanza la declare en `depende_de`.

**Nota.** `app_core/config.py` lo posee RET-01 (va antes); esta ficha solo ajusta comentarios después de ella.

