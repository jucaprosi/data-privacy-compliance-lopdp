+++
id = "ORG-22"
titulo = "Rol auditor: lectura de su tenant, registro y verificación en auditoria_capa, sin ejecutar ni cerrar"
ola = "backlog"
estado = "pendiente"
sala = "organizacion"
depende_de = ["DEMO-03"]
propiedad = ["features/organizacion/domain/roles.py", "alembic/versions/20261122_rol_auditor.py", "api/routers/auditoria_capa.py", "api/routers/auditoria_capa_controles.py", "data/demo/cooperativa_demo.json", "tests/test_org22_rol_auditor.py"]
crea = ["alembic/versions/20261122_rol_auditor.py", "tests/test_org22_rol_auditor.py"]
arbitro = "pytest tests/test_org22_rol_auditor.py tests/test_demo_siembra.py + suites de CAPA-01 y CAPA-02 + tests/test_alembic_una_cabeza.py; mutaciones documentadas; revisión de Seguridad"
rastros = ["¤rbac-tenant"]
+++

# ORG-22 · Rol auditor

Diseño del Arquitecto ADPA (2026-11-09). El PRD (l. 52) y `UX_DEMO_EVYDENTIA.md` (l. 40-55) ya definen al Auditor, que es la cuarta firma de la ruta de cuatro ojos. En `main` no existe: ni `Role` ni el CHECK `ck_utr_role` lo admiten. DEMO-03 siembra cinco personas y deja declarada la sexta. Esta ficha agrega el rol y siembra la persona auditor en `data/demo/cooperativa_demo.json`, que asume cuando DEMO-03 esté hecha.

## Entrega
- **`roles.py`:** `Role.auditor`, fuera de `AREA_SCOPED_ROLES`.
- **Migración nueva `20261122_rol_auditor.py`:** recrea `ck_utr_role` con `'auditor'`. Aplica FUSION_ALEMBIC sobre la cabeza vigente: ADPA-08 y DIAG-11 traen migraciones.
- **Permisos:**
  1. lectura de las salas de su tenant, solo con RLS: entra en `ROLES_LECTURA_CAPA` y `ROLES_CONSULTA`;
  2. escritura solo en `auditoria_capa`: registra hallazgos y actas (`ROLES_REGISTRO_CAPA`) y verifica acciones correctivas (`ROLES_VERIFICACION`);
  3. no ejecuta, no aprueba, no cierra ni sella: queda fuera de `ROLES_GESTION`, `ROLES_CIERRE_CAPA` y `ROLES_VENCIMIENTO`, y no responde el diagnóstico, que es del DPO.
- **Segregación:** no puede verificar una acción que él mismo ejecutó. Va en `INCOMPATIBILIDADES_ROLES` frente a `implementador`, con base en el PRD l. 52 y la independencia de la función de auditoría. Sin un artículo vinculante concreto, se anota como regla de negocio.
- **`api/rbac.py`:** valida con `Role.__members__`, así que no necesita cambios (medido en 811c7b0).
- **Otros routers:** `ROLES_CONSULTA` también aparece en `diagnostico_resultados.py`, `incidentes.py` y `roadmaps_hallazgos.py`. Si la lectura del auditor necesita esos archivos, para y consulta al Tech Lead: `diagnostico_resultados.py` tiene sección de DIAG-11.

## Pruebas (cada una con su mutación)
- El CHECK acepta `'auditor'`.
- El auditor recibe 403 al escribir fuera de CAPA y al cerrar un CAPA.
- Se deniega que verifique una acción propia.
- La incompatibilidad con `implementador` está presente.
- La plantilla demo tiene seis personas de un solo rol.

Revisión de Seguridad, porque toca el RBAC. Sin frontend, así que no pasa por UX/UI; si añade un menú, sí.
