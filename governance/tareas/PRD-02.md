+++
id = "PRD-02"
titulo = "Los invariantes citados existen en el archivo de EVYDENTIA; escala de madurez y mapa de rastros sobre sus archivos"
ola = "backlog"
estado = "pendiente"
sala = "gobernanza"
depende_de = ["DIAG-10", "GOB-01"]
propiedad = ["governance/artefactos/INVARIANTS_EVYDENTIA_REVENTA_NUBE.md", "scripts/verificar_escala_madurez.py", "tests/test_vpa_map.py", "governance/artefactos/VPA_MAP_EVYDENTIA_REVENTA_NUBE.md", "tests/test_inv_citados_existen.py"]
crea = ["tests/test_inv_citados_existen.py"]
arbitro = "pytest tests/test_inv_citados_existen.py tests/test_vpa_map.py tests/test_escala_madurez.py: todo INV_ citado fuera de los cuatro archivos inhabilitados y de APORTES existe en INVARIANTS_EVYDENTIA_REVENTA_NUBE.md; mutación documentada: borrar uno de los INV heredados del archivo hace fallar la prueba; otra con la escala 0 a 3 en el archivo nuevo"
rastros = ["¤triaje"]
+++

# PRD-02 · Los invariantes citados existen en el archivo de EVYDENTIA; escala de madurez y mapa de rastros sobre sus archivos

Diseño del Arquitecto ADPA, 2026-11-11 (nombre único EVYDENTIA y PRD único; decisión del propietario comunicada por el CTO), medido sobre origin/main 4141c452 por lectura; no se ejecutaron pruebas.

## Orden
PRD-00 (el CTO, en su PR: apartado `### 7.1 Catálogo de salas` en `PRD_EVYDENTIA_REVENTA_NUBE.md` y decisión sobre los 25 INV heredados) se fusiona antes. PRD-01 y PRD-02 pueden ir en paralelo; PRD-03, al final. **Bloqueante:** `PRD_EVYDENTIA_REVENTA_NUBE.md` no tiene el apartado 7.1 que lee `salas_del_prd`; devuelve 0 salas frente a 35 y cambiar solo la ruta rompería todas las fichas.

## Entrega
- Los INV del archivo viejo que siguen vivos se **trasladan con el mismo ID** a un apartado «Heredados del PMV» de `INVARIANTS_EVYDENTIA_REVENTA_NUBE.md`, **tras la decisión del CTO** sobre cuáles siguen rigiendo (no se renombran los ID en el código). Los 7 sin uso no se trasladan (`DEMO_NUNCA_PRODUCCION`, `ESCALA_MADUREZ_UNICA`, `EVIDENCE_DOMAIN_PURGE`, `LAST_ADMIN_PROTECTED`, `PRUNING_TREE_ANTECEDENCE`, `UI_ACHROMATIC_INVERTED_HIERARCHY`, `UI_ANTIGRAVITY_CURSOR`). Entre los vivos, `MULTIDIMENSIONAL_METRICS` (21 archivos) y `PMV_DECLARED_EVIDENCE` (6; choca con la evidencia real en GCS de EVYDENTIA). Los que el CTO derogue: sus referencias en código pasan a comentario de historia o se quitan en la ficha de la sala dueña.
- `scripts/verificar_escala_madurez.py`: la lista `DOCTRINA` cambia `INVARIANTS.md` por `INVARIANTS_EVYDENTIA_REVENTA_NUBE.md`; el inhabilitado deja de revisarse.
- `tests/test_vpa_map.py`: `MAPA` pasa a `VPA_MAP_EVYDENTIA_REVENTA_NUBE.md`; antes, dar de alta en ese mapa los rastros que faltan (`¤aportes`, `¤arquitectura`, `¤auditoria`, `¤doctrinas`, `¤dpo`, `¤fuentes`, `¤metodologias`, `¤regulacion`, `¤riesgos`, `¤triaje`) o medir cuáles siguen usándose y dar de alta solo esos.
- El docstring de `tests/test_diag13_evidencia_declarada.py` (cita `INV_LOPDP_PMV_DECLARED_EVIDENCE`) lo cambia su dueña (NEON-02 o la ficha de DIAG-07b), no esta ficha.

## Lista aprobada por el CTO (2026-11-11): los 32 invariantes heredados (prefijo `INV_LOPDP_`)
Regla para los equivalentes: si un invariante viejo ya está cubierto por uno de EVY con otro ID, **pasa con su mismo ID** como una línea de equivalencia («`INV_viejo`: equivale a EVY n.º X; se conserva el ID porque lo citan <archivos>»); así no se renombra nada en el código, la prueba queda en verde y no hay dos textos normativos que puedan divergir. Los que no tienen equivalente pasan con el texto adaptado. Retirados: 0.

- **Equivalencia con EVY:** `60MIN_TIMEBOX_LIMIT` (EVY 1), `MTGE_DETERMINISTIC_TRIGGER` (EVY 11), `INCIDENT_TIMELOCK` (EVY 16; se quita «CSIRT nacional conforme a la Ley de Ciberseguridad 2026» mientras no figure en `CITAS_LEGALES_VERIFICADAS.md`), `FORENSIC_ORIGINAL_HASH` (EVY 27), `EVIDENCE_BEFORE_COMPLIANCE` (EVY 2; el «madurez ≥ 2» viejo es de la escala 0-3 y no se traslada), `DEMO_NUNCA_PRODUCCION` (EVY 60-63), `CCTV_LEGAL_HOLD_OVERRIDE` (EVY 31), `PRUNING_TREE_ANTECEDENCE` (EVY 18).
- **Pasan con texto adaptado:** `MULTIDIMENSIONAL_METRICS` (madurez SMARTCIDI 1-5, conformidad jurídica, cobertura de evidencia y riesgo residual por separado, sin porcentaje único; complementa EVY 5), `ESCALA_MADUREZ_UNICA` (`escala_madurez.json`, árbitro `verificar_escala_madurez.py`), `CLOUD_SQL_AUTOPROXY` (sin proveedor externo de base: producción en Cloud SQL PostgreSQL 16, RLS forzado con `lopdp_app`, backup gestionado), `CLOUD_CONFIG_FAILS_CLOSED`, `NO_DEFAULT_SECRETS_IN_CLOUD` y `HEADERS_NEVER_WITH_PRODUCTION` (se quita Vercel: «en Cloud Run…»), `SINGLE_RTT_RLS_PGBOUNCER` (equivale a EVY 34 y añade `prepare_threshold=None` detrás de PgBouncer), `ROADMAP_RBAC_MATRIX` (remite al §3 del PRD de EVYDENTIA, no al «Módulo 5, §5.2» del PRD viejo), `EVIDENCE_DOMAIN_PURGE` (al cambiar de régimen se vacía la selección local y rige la lista blanca de EVY 19; nunca la evidencia guardada), `REGULATION_AS_CODE_DIFF` (la ruta es `features/regulacion_rag/`), `DIRECT_TO_GCS_ZERO_RAM_STREAM` (= EVY 26, sin la vía «o credenciales HMAC»: solo URL firmada V4).
- **Pasan sin cambios:** `SESSION_SINGLE_SOURCE`, `STANDALONE_FRONTEND_CONTAINER`, `APP_ROLE_NO_BYPASSRLS`, `LAST_ADMIN_PROTECTED`, `TENANT_BULKHEAD`, `EVIDENCE_FOUR_EYES` (compatible con EVY 14), `COMPLIANCE_GRAPH_SSOT` (ruta `features/rat/`).
- **Transitoria:** `PMV_DECLARED_EVIDENCE` no rige en EVYDENTIA (mandan EVI-01 y EVY 58-59); se anota «transitoria, la retira la ficha de contracción de EVI» y no se borra nada.
- **Los decide UX/UI:** `UI_ANTIGRAVITY_CURSOR` y `UI_ACHROMATIC_INVERTED_HIERARCHY` (esta última fija colores hexadecimales y EVY 37 prohíbe colores fijos sin variable semántica).
- **Textos finales de C3, C4 y C6:**
  - `ENCARGADO_RESPONSABLE_SIZE`: «El Coordinador (en el PMV, `encargado`) y el Responsable de Área solo se acumulan en organizaciones micro o pequeñas. Si el tamaño es nulo, 409 `TENANT_SIZE_NOT_CONFIGURED`; si es mediana o grande, 409 `SOD_VIOLATION`. El trigger de `user_tenant_roles` bloquea también las inserciones directas.» (`encargado` pasó a `coordinador` en ORG-00, `20261019_rol_coordinador.py`). El árbitro que cita el texto viejo, `tests/test_encargado_responsable_tamano.py`, **no existe**: la ficha mide qué prueba lo cubre (candidatas: `test_excepciones_sod.py`, `test_alta_unica_roles.py`, `test_errores_negocio.py`) y la nombra, o crea la prueba con su mutación.
  - `RESPONSABLE_ALTA_FLOW`: «El Coordinador (antes `encargado`) solicita y no ejecuta (403); el `implementador` no se asigna a sí mismo (409); el `dpo` no puede ser destino (409); cada transición deja evento. Árbitro: `tests/test_responsable_requests.py`.»
  - C4: la matriz de permisos remite al §3 del PRD de EVYDENTIA; `tests/test_permissions_matrix.py` no existe: el que existe es `tests/test_matriz_permisos.py` (lo corrige el CTO en su PR).
  - `VAULT_TIER_SEPARATION`: «Los objetos con retención normativa menor de 30 días van en Standard sin Autoclass, con regla Lifecycle Delete. Los de 30 días o más van en el pool long-retention con retención por objeto. El bloqueo WORM solo lo activa el propietario tras la confirmación legal.»
- C1 (EVY 5 dice «4 Dimensiones»; son 10 y las 4 son «ejes»), C2 y C5: resueltas en el PR #603 del CTO; los títulos «4 dimensiones» de TASKS y VPA_MAP los cambia la ficha de renombrado.
- **Catálogo de salas (§5.2):** PRD-01 cambia `salas_del_prd` para que busque el encabezado de §5.2 y lea solo esa tabla, hasta la primera línea que no empiece por `|` (no hasta el siguiente `## `), de modo que la fila `governance` de la otra tabla no entre. Prueba: `--verificar` da 0 y el conjunto de salas es el de `PRD.md` más las dos que añadió el CTO; mutación: quitar una fila hace fallar la ficha de esa sala. PRD-01 va después de #603.
