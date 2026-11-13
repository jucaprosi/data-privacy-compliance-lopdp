+++
id = "NEON-04"
titulo = "Gobernanza vigente sin Neon: documentos del PMV al histórico y menciones corregidas"
ola = "backlog"
estado = "en_curso"
sala = "gobernanza"
depende_de = ["NEON-00", "OPS-01", "OPS-02", "OPS-04", "OPS-06", "ORG-08", "QA-03", "SEC-02", "SEC-10", "SEC-12", "TEST-05", "ADPA-10", "BIB-105", "CI-02", "CI-03", "CI-08", "CI-10", "CI-12", "CI-13", "CI-17", "CI-18", "DEV-01", "EP-11", "GCP-04", "GOB-02", "GOB-03", "GOB-04", "MARCA-06"]
propiedad = ["docs/politica-credenciales-neon.md", "governance/METODOLOGIAS.md", "governance/Metodología de trabajo en equipo.md", "governance/PLAN_HOJA_DE_RUTA_INTELIGENTE.md", "governance/apoyo/AUDITORIA_CRITERIOS_MVP.md", "governance/apoyo/BIBLIOTECA_ESTADO.md", "governance/apoyo/BIBLIOTECA_README.md", "governance/apoyo/BRIEFS_POR_BLOQUE.md", "governance/apoyo/DISENO_CAPACIDADES_BIBLIOTECA.md", "governance/apoyo/DISENO_PORTALES_EXTERNOS.md", "governance/apoyo/FLUJOS_DEMO_COMERCIAL.md", "governance/arquitectura/HOJA_DE_RUTA_ADPA.md", "governance/especificaciones/DIAG-08.md", "governance/especificaciones/FIRMA-05.md", "governance/especificaciones/RM-21.md", "governance/operaciones/CI_SIN_NEON.md", "governance/operaciones/CONSOLIDACION_PRUEBAS.md", "governance/operaciones/CONSULTAS_POR_PRUEBA.md", "governance/operaciones/CREDENCIALES_Y_ROLES_BD.md", "governance/operaciones/ENTORNO_LOCAL.md", "governance/operaciones/FUSION_ALEMBIC.md", "governance/operaciones/MEDICION_PRUEBAS_LENTAS.md", "governance/operaciones/MIGRACION_CLOUDSQL_POSTGRES.md", "governance/operaciones/PROCEDIMIENTO_VERCEL.md", "governance/operaciones/PRUEBAS_DE_HUMO.md", "governance/operaciones/PRUEBAS_EN_FISICO.md", "governance/operaciones/PUBLICACION_PMV.md", "governance/operaciones/RAMAS_NEON_DE_DESARROLLO.md", "governance/operaciones/REGISTRO_MIGRACIONES_MANUALES.md", "governance/operaciones/VARIABLES_VERCEL.md", "governance/operaciones/VARIACION_NEON_CI.md", "governance/operaciones/VERIFICACION_GENERACION.md", "governance/apoyo/UX_DEMO_COMERCIAL.md", "governance/tareas/README.md", "governance/historico/pmv/RAMAS_NEON_DE_DESARROLLO.md", "governance/historico/pmv/VARIACION_NEON_CI.md", "governance/historico/pmv/CI_SIN_NEON.md", "governance/historico/pmv/VARIABLES_VERCEL.md", "governance/historico/pmv/PUBLICACION_PMV.md", "governance/historico/pmv/PROCEDIMIENTO_VERCEL.md", "governance/historico/pmv/politica-credenciales-neon.md", "governance/historico/pmv/FLUJOS_DEMO_COMERCIAL.md", "governance/historico/pmv/UX_DEMO_COMERCIAL.md", "governance/apoyo/BRIEF_PROPIETARIO_NEON.md", "tests/sin_neon/pendientes/NEON-04.txt"]
crea = ["governance/historico/pmv/RAMAS_NEON_DE_DESARROLLO.md", "governance/historico/pmv/VARIACION_NEON_CI.md", "governance/historico/pmv/CI_SIN_NEON.md", "governance/historico/pmv/VARIABLES_VERCEL.md", "governance/historico/pmv/PUBLICACION_PMV.md", "governance/historico/pmv/PROCEDIMIENTO_VERCEL.md", "governance/historico/pmv/politica-credenciales-neon.md", "governance/historico/pmv/FLUJOS_DEMO_COMERCIAL.md", "governance/historico/pmv/UX_DEMO_COMERCIAL.md", "governance/apoyo/BRIEF_PROPIETARIO_NEON.md"]
arbitro = "pytest tests/test_sin_neon.py con pendientes/NEON-04.txt vacío; ningún documento vigente contiene DEMO_MODE; 0 enlaces a rutas movidas"
rastros = ["¤arbitro"]
+++

# NEON-04 · Gobernanza vigente (Tech Lead)

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
1. **Documentos que pasan a `governance/historico/pmv/`**, sin borrarse:
   - `RAMAS_NEON_DE_DESARROLLO.md`, `VARIACION_NEON_CI.md`, `CI_SIN_NEON.md`, `VARIABLES_VERCEL.md`, `PUBLICACION_PMV.md`, `PROCEDIMIENTO_VERCEL.md` y `docs/politica-credenciales-neon.md`, con el encabezado «Histórico · PMV congelado; vigente solo para la rama produccion». La política de credenciales sigue aplicando al PMV y conserva ese aviso;
   - `FLUJOS_DEMO_COMERCIAL.md` y `UX_DEMO_COMERCIAL.md`, con el encabezado «sustituido por PRD_EVYDENTIA §5.6 y UX_DEMO_EVYDENTIA.md» (§3b: la demo usa una instancia Cloud SQL propia, protegida por SEC-20 con `entorno_marcador='demo'`).
2. **Menciones sueltas:** se corrigen en los demás documentos de la propiedad. Las fichas hechas no se editan. En las fichas vivas solo cambia el texto que presenta a Neon como procedimiento vigente.
3. **Enlaces:** se corrigen todos los que apuntaban a los documentos movidos. Una búsqueda de las rutas viejas da 0.
4. **`BRIEF_PROPIETARIO_NEON.md`**, con tres cosas para el propietario:
   - el parche de `verificadores/README.md` y `arnes_local.py`, que son gobernanza reservada;
   - la nota del manifiesto `base_pruebas` de NEON-03;
   - la limpieza de las ramas de Neon en la consola.
5. **PR:** va en un único PR de gobernanza, corto, porque `BRIEFS_POR_BLOQUE.md` es un archivo de cierre que tocan todos.

6. **Nota sobre el PMV (CTO, 2026-11-09)**, corta, junto a los documentos que pasan a `governance/historico/pmv/`: el propietario creó la rama `pmv/consolidacion` a partir de `produccion` (6cf7131d). El trabajo de Aleczandra sobre el PMV va en ramas `pmv/aleczandra/<tema>` con PR hacia `pmv/consolidacion`, probado contra la base Neon `test-aleczandra`; `main` queda solo para EVYDENTIA. Publicar al PMV es un PR de `pmv/consolidacion` hacia `produccion` con aprobación de otra persona, decisión del propietario.

## Árbitros
- `pendientes/NEON-04.txt` queda vacío.
- Ningún documento vigente fuera del histórico contiene `DEMO_MODE`.
- 0 enlaces a las rutas movidas.
