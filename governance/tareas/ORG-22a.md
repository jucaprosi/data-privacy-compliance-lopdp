+++
id = "ORG-22a"
titulo = "Rol auditor, expandir: el CHECK lo admite y la revisión anterior lee roles desconocidos sin romperse"
ola = "backlog"
estado = "hecha"
sala = "organizacion"
depende_de = ["ADPA-02", "ORG-02", "ORG-05", "ORG-13", "ORG-16", "RM-01", "RM-16"]
propiedad = ["alembic/versions/20261122_rol_auditor.py", "features/organizacion/services/roles_engine.py", "features/organizacion/services/invitaciones_personas_engine.py", "tests/test_org22a_roles_desconocidos.py"]
crea = ["alembic/versions/20261122_rol_auditor.py", "tests/test_org22a_roles_desconocidos.py"]
arbitro = "pytest tests/test_org22a_roles_desconocidos.py tests/test_alembic_una_cabeza.py + suite de organización: una fila con un rol desconocido no da 500 al asignar un rol ni al invitar y la SoD falla cerrada; el CHECK acepta auditor; mutaciones documentadas: volver a Role(...) estricto hace fallar la prueba"
rastros = ["¤rbac-tenant"]
+++

# ORG-22a · Rol auditor, expandir

Diseño del Arquitecto ADPA, 2026-11-11 (medido leyendo origin/main; no se ejecutaron pruebas). Expandir: la migración que admite `auditor` en `ck_utr_role` y las dos lecturas tolerantes, para que la revisión anterior de Cloud Run no dé 500 cuando exista una fila `auditor` en `user_tenant_roles` (durante el despliegue por escalones, el 90 % del tráfico va a la revisión vieja).

## Entrega
- `alembic/versions/20261122_rol_auditor.py`: recrea `ck_utr_role` admitiendo `auditor` (es un CHECK sobre String, no un ENUM nativo); de expansión, sin contraer; **de una en una con FUSION_ALEMBIC** sobre la cabeza real de `origin/main`.
- Las dos lecturas que hoy hacen `Role(valor)` sobre filas de la base pasan a ser tolerantes: ignoran los valores que no están en `Role`, y un valor desconocido cuenta como rol activo para la SoD, que **falla cerrada** (si un rol desconocido podría chocar, rechaza): `features/organizacion/services/roles_engine.py:95` (`check_dpo_sod(..., Role(r["role"]) ...)`) y `features/organizacion/services/invitaciones_personas_engine.py:49` (`{Role(r) for r in filas}`). `get_context` (`api/rbac.py`) ya compara con `Role.__members__` y responde 403 ante una cabecera desconocida: no se toca. `RoleGrant.role: Role` es de entrada y no afecta; `clon_plantilla_engine.py:101` y `scripts/datos_sinteticos` construyen desde datos propios.
- **No añade `Role.auditor`**: nadie puede conceder el rol todavía (eso es ORG-22).

## Pruebas (cada una con su mutación)
- Una fila sembrada con un rol desconocido no da 500 en ninguna de las dos lecturas y el alta sigue pasando la SoD; un rol desconocido que podría chocar se rechaza (falla cerrada). Mutación: volver a `Role(...)` estricto hace fallar la prueba.
- El CHECK acepta `'auditor'`; `pytest tests/test_alembic_una_cabeza.py`.
