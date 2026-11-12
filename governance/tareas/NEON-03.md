+++
id = "NEON-03"
titulo = "Playwright sin rama Neon: configs con base local o evydentia-pruebas y manifiesto E2E con base_pruebas"
ola = "backlog"
estado = "en_curso"
sala = "frontend"
depende_de = ["NEON-00", "TEST-03", "BIB-105", "FE-22"]
propiedad = ["frontend/playwright.humo.config.ts", "frontend/playwright.integracion.config.ts", "frontend/tests/biblioteca/editorial.spec.ts", "frontend/tests/integracion/recorrido1_roles.spec.ts", "frontend/tests/integracion/recorrido2_tamano.spec.ts", "tests/sin_neon/pendientes/NEON-03.txt"]
crea = []
arbitro = "npx playwright test --list + tsc --noEmit + pytest tests/test_sin_neon.py con pendientes/NEON-03.txt vacío"
rastros = ["¤arbitro"]
+++

# NEON-03 · Playwright

Diseño del Arquitecto ADPA (`DISENO_RETIRO_NEON_2026-11-09.md`), a partir del brief del CTO. Decisiones del propietario (2026-11-09):
- solo EVYDENTIA en `main`; el PMV congelado (rama `produccion`) no se toca;
- `app_core/huellas_produccion.py` se mantiene mientras exista la base Neon del PMV;
- la historia se conserva: fichas hechas, aportes, bibliografía, informes fechados y migraciones.

No borra ni crea recursos en Neon. No toca `.github/workflows/`, `verificadores/` ni migraciones. Sin `import yaml`.

**Reemplazo de la «rama Neon propia» (§0):**
- en local, la única base de pruebas es el contenedor PostgreSQL 16 del arnés (127.0.0.1), el mismo del CI desde CI-17;
- en el entorno desplegado, `evydentia-pruebas` de Cloud SQL (EP-05);
- una prueba con base corre si `TEST_DATABASE_URL` apunta a un host local o si `ARNES_BASE=postgresql_local`;
- una URL remota no habilita ninguna prueba con base.

## Entrega
- Las dos configs exigen `TEST_DATABASE_URL` con el mensaje «base PostgreSQL local del arnés o evydentia-pruebas».
- **Manifiesto E2E:** el campo `neon` (`editorial.spec.ts:92` y `103`) pasa a `base_pruebas`, con el mismo valor `"bib-105"`. El formato del manifiesto queda documentado en la cabecera del spec. Quien genere `BIB105_E2E_MANIFEST` lo ajusta; NEON-04 deja la nota en el brief del propietario.
- `recorrido1_roles.spec.ts` y `recorrido2_tamano.spec.ts`: solo comentarios.
- No hay cambios visibles, así que no pasa por UX/UI.
- Al terminar, `pendientes/NEON-03.txt` queda vacío o se borra.
