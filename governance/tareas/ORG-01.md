+++
id = "ORG-01"
titulo = "Una sola matriz de incompatibilidades de roles, con su base legal; el DPO sin roles operativos"
ola = "D"
estado = "pendiente"
sala = "organizacion"
depende_de = ["ORG-00", "RM-01", "RM-10", "RM-16"]
propiedad = ["governance/artefactos/PRD.md", "features/organizacion/domain/roles.py", "features/organizacion/services/sod_engine.py", "alembic/versions/*_dpo_sin_roles_operativos.py", "tests/test_rbac_rules.py", "tests/test_matriz_incompatibilidades.py", "features/organizacion/organizacion_service.py#ORG-01"]
arbitro = "pytest tests/test_matriz_incompatibilidades.py tests/test_rbac_rules.py + suite completa; el cambio del PRD lo aprueba el propietario"
rastros = ["¤rbac-tenant", "¤seguridad"]
+++

# ORG-01 · Una sola matriz de incompatibilidades de roles, con su base legal; el DPO sin roles operativos

**Objetivo.** Las reglas de qué roles no pueden recaer en la misma persona están repartidas, se contradicen y citan mal su base legal: el PRD §5.3 (punto 7) permite `dpo` + `responsable_area` «sujeta a cuatro ojos», pero §5.3.1 rechaza con 409 dar de alta a un DPO como responsable de área (lo aplica RM-10); `DPO_INCOMPATIBLE_ROLES` (`domain/roles.py`) solo cubre `implementador` y `coordinador`; el trigger `fn_utr_dpo_sod` repite esa lista en SQL; y RM-16 añade otra regla distinta para `coordinador` + `responsable_area`. Además `roles.py` y `app_core/security.py` atribuyen la independencia del DPO al Art. 48 de la LOPDP, que solo enumera los casos en que hay que designar delegado.

## Base legal (texto oficial de la LOPDP, Registro Oficial Suplemento 459, 26-may-2021)
- **Art. 4:** el *responsable del tratamiento* decide la finalidad y el tratamiento; el *encargado del tratamiento* trata datos a nombre y por cuenta del responsable (un tercero).
- **Art. 49 y 50:** el delegado de protección de datos (DPD) asesora, supervisa el cumplimiento, asesora en el análisis de riesgo y es punto de contacto con la Autoridad; tiene relación directa con el más alto nivel ejecutivo, no puede ser destituido ni sancionado por desempeñar bien su función, y solo puede tener otras funciones si no hay conflicto con las suyas.
- **Autoridad:** la Superintendencia de Protección de Datos Personales (Art. 76 y 77).
- **Reglamento del Delegado (Resolución SPDP-SPD-2025-0028-R, Registro Oficial 105, 19-ago-2025):** **texto vinculante pendiente de contraste** por el propietario. Los resúmenes jurídicos consultados coinciden en que el delegado no puede ser oficial de cumplimiento ni oficial de seguridad de la información y debe estar libre de conflicto de intereses; una sola fuente añade que no puede integrar órganos de administración o control ni ser socio.

## Cómo se aplica a los roles
| Rol de la plataforma | Equivalencia con la ley | Nota |
| :-- | :-- | :-- |
| `coordinador` | Ejerce la función del *responsable del tratamiento* (Art. 4, 47) | Designa a los responsables de área y supervisa todas las áreas. La responsabilidad legal es de la entidad, no de la persona. |
| `dpo` | Delegado de protección de datos (Art. 48 a 50) | Lo designa la organización, no la Autoridad; reporta al más alto nivel ejecutivo. |
| `responsable_area`, `implementador`, `admin_organizacion` | Sin base legal propia | Diseño organizacional de la plataforma. |

## Entrega
- Una sola tabla de pares incompatibles en `domain/roles.py` (de la que `sod_engine.check_dpo_sod` y cualquier regla futura leen), con el motivo y la **base legal de cada par**: `dpo` con `coordinador` (función de cumplimiento), con `implementador` (configura la estructura y la seguridad) y con `responsable_area` (dueño de controles que luego supervisa), todos por el criterio de conflicto de intereses del Art. 50. La combinación `dpo` + `admin_organizacion` sigue permitida, **a confirmar con el texto del reglamento**.
- PRD: corregir §5.3 punto 7 para que diga lo mismo que §5.3.1; ampliar el glosario «Equivalencias con la LOPDP» de ORG-00; y citar los Art. 49 y 50 y el reglamento donde hoy se cita el Art. 48 para la independencia.
- Corregir los comentarios de `domain/roles.py` que citan el Art. 48 para la independencia (el de `app_core/security.py` es de SEC-03, ya integrada: se anota en el informe).
- Migración que reemplaza `fn_utr_dpo_sod` para que la lista del trigger incluya `responsable_area`. **Antes de aplicarla** se ejecuta una consulta que lista los DPO que ya tienen `responsable_area` activo (el trigger no revisa filas existentes); la migración no las toca y el informe las entrega al propietario.
- Prueba que **compara las dos copias**: la lista de roles del trigger (leída de la base con `pg_get_functiondef`) debe ser igual a la tabla de Python.
- Ajustar `tests/test_rbac_rules.py`, que hoy afirma que `dpo` + `responsable_area` es compatible, y probar la matriz completa (cada par, en los dos sentidos) contra el servicio y contra el trigger.
- Sección reservada `# === ORG-01 ===` en la compuerta, solo para reexportar la tabla.

## Límites
- No cambia el motor de RM-10, que ya rechaza al DPO como destino.
- No toca la regla de `coordinador` + `responsable_area`: eso es ORG-02.
- **Acción previa del propietario:** contrastar con el texto vinculante del Reglamento del Delegado la lista de impedimentos antes de aprobar el cambio del PRD.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
