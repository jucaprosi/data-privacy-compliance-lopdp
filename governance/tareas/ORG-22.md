+++
id = "ORG-22"
titulo = "Rol auditor: lectura de su tenant, registro y verificación en auditoria_capa, sin ejecutar ni cerrar"
ola = "backlog"
estado = "pendiente"
sala = "organizacion"
depende_de = ["DEMO-03", "ORG-22a"]
propiedad = ["features/organizacion/domain/roles.py", "api/routers/auditoria_capa.py", "api/routers/auditoria_capa_controles.py", "data/demo/cooperativa_demo.json", "tests/test_demo_siembra.py", "tests/test_org22_rol_auditor.py", "tests/test_matriz_permisos.py", "features/organizacion/services/sod_engine.py", "alembic/versions/20261123_auditor_sod_trigger.py", "tests/test_org22b_sod_auditor.py"]
crea = ["tests/test_org22_rol_auditor.py", "alembic/versions/20261123_auditor_sod_trigger.py", "tests/test_org22b_sod_auditor.py"]
arbitro = "pytest tests/test_org22_rol_auditor.py tests/test_demo_siembra.py + suites de CAPA-01 y CAPA-02 + tests/test_alembic_una_cabeza.py; mutaciones documentadas; revisión de Seguridad"
rastros = ["¤rbac-tenant"]
+++

# ORG-22 · Rol auditor

Diseño del Arquitecto ADPA (2026-11-09). El PRD (l. 52) y `UX_DEMO_EVYDENTIA.md` (l. 40-55) ya definen al Auditor, que es la cuarta firma de la ruta de cuatro ojos. En `main` no existe: ni `Role` ni el CHECK `ck_utr_role` lo admiten. DEMO-03 siembra cinco personas; el auditor no figura en su JSON. Esta ficha agrega el rol y siembra la persona auditor en `data/demo/cooperativa_demo.json`, que asume cuando DEMO-03 esté hecha.

## Entrega
- **`roles.py`:** `Role.auditor`, fuera de `AREA_SCOPED_ROLES`.
- **Migración nueva `20261122_rol_auditor.py`:** recrea `ck_utr_role` con `'auditor'`. Es de expansión, sin contraer (GCP-07): una sola cabeza. Aplica FUSION_ALEMBIC sobre la cabeza vigente: ADPA-08 y DIAG-11 traen migraciones.
- **Permisos:**
  1. lectura de las salas de su tenant, solo con RLS: entra en `ROLES_LECTURA_CAPA` y `ROLES_CONSULTA`;
  2. escritura solo en `auditoria_capa`: registra hallazgos y actas (`ROLES_REGISTRO_CAPA`) y verifica acciones correctivas (`ROLES_VERIFICACION`);
  3. no ejecuta, no aprueba, no cierra ni sella: queda fuera de `ROLES_GESTION`, `ROLES_CIERRE_CAPA` y `ROLES_VENCIMIENTO`, y no responde el diagnóstico, que es del DPO.
- **Segregación:** no puede verificar una acción que él mismo ejecutó. Va en `INCOMPATIBILIDADES_ROLES` frente a `implementador`, con base en el PRD l. 52 y la independencia de la función de auditoría. Sin un artículo vinculante concreto, se anota como regla de negocio.
- **`api/rbac.py`:** valida con `Role.__members__`, así que no necesita cambios (medido en 811c7b0).
- **Otros routers:** `ROLES_CONSULTA` también aparece en `diagnostico_resultados.py`, `incidentes.py` y `roadmaps_hallazgos.py`. Esos tres archivos van en ORG-23 (Arquitecto, 2026-11-09). ORG-22 toca solo los dos routers de `auditoria_capa`.

## Pruebas (cada una con su mutación)
- El CHECK acepta `'auditor'`.
- El auditor recibe 403 al escribir fuera de CAPA y al cerrar un CAPA.
- Se deniega que verifique una acción propia.
- La incompatibilidad con `implementador` está presente.
- La plantilla demo tiene seis personas de un solo rol.

Revisión de Seguridad antes de repartirla, porque toca el RBAC (CTO, 2026-11-09). Asume también `tests/test_demo_siembra.py`, para pasar el árbitro a seis personas. Sin frontend, así que no pasa por UX/UI; si añade un menú, sí.

**Ajuste 2026-11-11 (Arquitecto, tras medir lo que rompe la revisión anterior de Cloud Run): ORG-22 se parte en expandir y activar.** Esta ficha es la fase **activar** (ORG-22b): `Role.auditor`, la fila del rol en `tests/test_matriz_permisos.py`, la segregación y la revisión de Seguridad; depende de ORG-22a y de la compuerta humana del brief de despliegue tipo DER-06b (la revisión que sirve y la estable son posteriores a ORG-22a). La migración `20261122_rol_auditor.py` pasa a ORG-22a.
- **Segregación (corrección del Arquitecto):** el §3 del PRD de EVYDENTIA solo dice del auditor «No ejecuta las tareas operativas que él mismo audita»: es una regla **por tarea**, no una exclusión de roles. Se conserva la incompatibilidad con `implementador` y se añade la regla por tarea: el auditor no verifica el cierre ni valida la evidencia de una tarea que ejecutó o cuya evidencia subió (409, con su mutación). Excluir además `coordinador` y `responsable_area` iría más allá del PRD: es una pregunta al CTO.

**Decisión del CTO (2026-11-11) sobre la SoD del auditor, que sustituye a la regla por tarea como regla principal:** el `auditor` **no acumula ningún otro rol en el mismo tenant** (`coordinador`, `responsable_area`, `implementador`, `admin_organizacion` ni `dpo`). El CTO la escribe en el §3 del PRD de EVYDENTIA y en el invariante de SoD, en un PR aparte después de #603: es la **fuente** de esta ficha. Esta ficha depende de ORG-22a, de ese PR del CTO y de la compuerta humana de revisiones (brief tipo DER-06b).
- **Dónde va la regla (dos direcciones y dos capas):** (1) compuerta: `features/organizacion/services/sod_engine.py` (función nueva o ampliación de `check_dpo_sod`) usada por `roles_engine` y las invitaciones; (2) trigger de `user_tenant_roles` (migración `20261123_auditor_sod_trigger`, de una en una con FUSION_ALEMBIC sobre la cabeza real): rechaza un auditor cuando hay otro rol activo y rechaza otro rol cuando hay un auditor activo, de modo que también se bloquea la escritura directa en la base.
- **Excepciones:** el mecanismo de excepciones temporales (`excepcion_sod_engine.py`, invariante 7) no aplica al auditor salvo decisión explícita del CTO; prueba de que una excepción no lo habilita.
- **Árbitro:** cinco casos en cada dirección con 409 `SOD_VIOLATION`, una inserción directa rechazada por el trigger y la fila del rol en `tests/test_matriz_permisos.py`. Mutaciones: quitar un rol de la lista de incompatibles y quitar el trigger; cada una hace fallar su caso.
- **Regla por tarea del PRD** («no verifica lo que ejecutó»): sigue igual, aunque con la exclusión total no puede ocurrir; basta una sola prueba que lo compruebe.
