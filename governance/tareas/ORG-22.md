+++
id = "ORG-22"
titulo = "Rol auditor: lectura de su tenant, registro y verificación en auditoria_capa, sin ejecutar ni cerrar"
ola = "backlog"
estado = "en_curso"
sala = "organizacion"
depende_de = ["DEMO-03", "ORG-22a"]
propiedad = ["features/organizacion/domain/roles.py", "api/routers/auditoria_capa.py", "api/routers/auditoria_capa_controles.py", "data/demo/cooperativa_demo.json", "tests/test_demo_siembra.py", "tests/test_org22_rol_auditor.py", "tests/test_matriz_permisos.py", "features/organizacion/services/sod_engine.py", "features/organizacion/services/roles_engine.py", "alembic/versions/org22b_auditor_sod_trigger.py", "tests/test_org22b_sod_auditor.py", "tests/test_matriz_incompatibilidades.py", "tests/test_org22a_roles_desconocidos.py"]
crea = ["tests/test_org22_rol_auditor.py", "alembic/versions/org22b_auditor_sod_trigger.py", "tests/test_org22b_sod_auditor.py"]
arbitro = "pytest tests/test_org22_rol_auditor.py tests/test_org22b_sod_auditor.py tests/test_demo_siembra.py + suites de CAPA-01 y CAPA-02 + tests/test_alembic_una_cabeza.py; mutaciones documentadas por cada prueba nueva; revisión de Seguridad"
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
- **Dónde va la regla (dos direcciones y dos capas):** (1) compuerta: `features/organizacion/services/sod_engine.py` (función nueva o ampliación de `check_dpo_sod`) usada por `roles_engine` y las invitaciones; (2) trigger de `user_tenant_roles` (migración `alembic/versions/org22b_auditor_sod_trigger.py`, de una en una con FUSION_ALEMBIC sobre la cabeza real): rechaza un auditor cuando hay otro rol activo y rechaza otro rol cuando hay un auditor activo, de modo que también se bloquea la escritura directa en la base.
- **Excepciones:** el mecanismo de excepciones temporales (`excepcion_sod_engine.py`, invariante 7) no aplica al auditor salvo decisión explícita del CTO; prueba de que una excepción no lo habilita.
- **Árbitro:** cinco casos en cada dirección con 409 `SOD_VIOLATION`, una inserción directa rechazada por el trigger y la fila del rol en `tests/test_matriz_permisos.py`. Mutaciones: quitar un rol de la lista de incompatibles y quitar el trigger; cada una hace fallar su caso.
- **Regla por tarea del PRD** («no verifica lo que ejecutó»): sigue igual, aunque con la exclusión total no puede ocurrir; basta una sola prueba que lo compruebe.

**Decisión del CTO (2026-11-12) y diseño del Arquitecto, que cierran la SoD del auditor:** `dpo` y `auditor` son roles **exclusivos**: quien tiene uno no tiene ningún otro rol activo en el mismo tenant. La razón es el invariante `INV_LOPDP_FOUR_EYES_CLOSURE`: el auditor verifica hallazgos y el DPO es la segunda verificación independiente del cierre, así que juntarlos rompe los cuatro ojos. Se implementa con el menor número de archivos:
- **Aplicación (`roles.py`):** se agregan a `INCOMPATIBILIDADES_ROLES` las tuplas `(auditor, X)` para `coordinador`, `responsable_area`, `implementador`, `admin_organizacion` y `dpo`; la base legal dice «regla de negocio: INV_LOPDP_FOUR_EYES_CLOSURE (decisión del CTO, 2026-11-12); sin artículo vinculante». `DPO_INCOMPATIBLE_ROLES` se deriva de esa tupla y suma al auditor sola.
- **`sod_engine.py`:** `check_dpo_sod` se generaliza a cualquier par de `INCOMPATIBILIDADES_ROLES` en las dos direcciones. Conserva el nombre para que los llamadores no cambien y da un mensaje propio para el auditor.
- **`roles_engine.py` (una sola línea):** `motivo_sod_tolerante` falla cerrada con un rol desconocido solo si `nuevo == Role.dpo`; debe ser `nuevo in {dpo, auditor}`. `invitaciones_personas_engine.py` no se toca. ORG-22a (ya hecha) lo preparó para el DPO.
- **Base:** un solo cambio de `fn_utr_dpo_sod`, sin trigger nuevo, en la migración `alembic/versions/org22b_auditor_sod_trigger.py` (sin fecha, como `der01_derechos_respuestas.py`; `down_revision` = cabeza de `main` al implementar, una cabeza al fusionar con FUSION_ALEMBIC). La función se reescribe: si `NEW.role IN ('dpo','auditor')` y existe otro rol activo, `check_violation`; si `NEW.role` es otro y existe `'dpo'` o `'auditor'` activo, `check_violation`. El downgrade restaura el cuerpo de `20261019_dpo_sin_operativos`.
- **Datos existentes:** antes de reemplazar la función, la migración cuenta los pares `(user_id, tenant_id)` con `dpo` o `auditor` activo y algún otro rol activo; si hay alguno, aborta con el recuento, sin `UPDATE` ni `DELETE`.
- **Pruebas en `tests/test_org22b_sod_auditor.py`, cada una con su mutación:** (1) auditor→dpo y dpo→auditor por la aplicación dan 409 `SOD_VIOLATION` (mutación: quitar la tupla `(auditor, dpo)`); (2) auditor frente a los otros cuatro roles, en las dos direcciones (quitar una tupla); (3) `INSERT` directo con `lopdp_app` en las dos direcciones, rechazado por el trigger (quitar `'auditor'` de la función); (4) auditor con un rol desconocido, rechazado (volver al `== Role.dpo`); (5) migración con un par dpo+auditor ya presente aborta con recuento 1 (reemplazar el recuento por un `DELETE`); (6) una excepción temporal (`excepcion_sod_engine`) no habilita al auditor (dejar que la excepción lo cubra).
- **Pruebas ajenas que cambian con este diseño (propiedad ampliada por el Tech Lead, 2026-11-12, a petición de la sesión):** `tests/test_matriz_incompatibilidades.py` (ORG-01, hecha) fija `len(INCOMPATIBILIDADES_ROLES)==4`, `DPO_INCOMPATIBLE_ROLES` con los cuatro roles operativos y la lista de roles de `fn_utr_dpo_sod`; con las cinco tuplas `(auditor, X)` pasa a 9 y `DPO_INCOMPATIBLE_ROLES` suma `auditor`: se actualizan esas expectativas y la comparación Python↔trigger. `tests/test_org22a_roles_desconocidos.py` (ORG-22a, hecha) usa `'auditor'` como «rol desconocido»; con `Role.auditor` ya es conocido: se cambia a un valor realmente desconocido (DDL temporal dentro de la transacción).
