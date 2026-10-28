# ¤¤security-engineer
"""ORG-13: una persona pertenece a varias organizaciones solo como DPO o implementador. ¤rbac-tenant ¤seguridad

Decisión del propietario (2026-10-26): quien tiene admin_organizacion, coordinador o
responsable_area pertenece a una sola organización; dpo e implementador pueden repetirse en
varias. Solo cuentan las asignaciones vigentes (valid_to vacío o futuro).

- Disparador BEFORE INSERT OR UPDATE en user_tenant_roles, SECURITY DEFINER con search_path
  fijo: ve las demás organizaciones de la persona sin abrir la RLS a la aplicación, y cubre todos
  los caminos que conceden roles. Un candado por persona serializa asignaciones simultáneas.
- Función mis_organizaciones(usuario): SECURITY DEFINER, EXECUTE solo para lopdp_app; devuelve
  las organizaciones de esa persona con sus roles vigentes, y nada de otras personas.
- Antes de crear el disparador se comprueba que nadie incumpla ya la regla: si alguien la
  incumple, la migración se detiene y lista los id internos (nunca correos). No borra ni cambia
  asignaciones.
"""
from alembic import op
import sqlalchemy as sa

revision = "20261028_organizaciones_persona"
down_revision = "20261028_bitacora_incidentes"
branch_labels = None
depends_on = None

INCUMPLIDORES = """
SELECT DISTINCT a.user_id
FROM user_tenant_roles a
JOIN user_tenant_roles b
  ON b.user_id = a.user_id AND b.tenant_id <> a.tenant_id
WHERE (a.valid_to IS NULL OR a.valid_to > now())
  AND (b.valid_to IS NULL OR b.valid_to > now())
  AND (a.role NOT IN ('dpo', 'implementador') OR b.role NOT IN ('dpo', 'implementador'))
ORDER BY a.user_id
"""

FUNCION_DISPARADOR = """
CREATE OR REPLACE FUNCTION verificar_organizaciones_por_persona()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    IF NEW.valid_to IS NOT NULL AND NEW.valid_to <= now() THEN
        RETURN NEW;
    END IF;
    -- Dos asignaciones simultáneas de la misma persona en organizaciones distintas no se cuelan.
    PERFORM pg_advisory_xact_lock(hashtext('organizaciones_por_persona:' || NEW.user_id));
    IF EXISTS (
        SELECT 1
        FROM user_tenant_roles otra
        WHERE otra.user_id = NEW.user_id
          AND otra.tenant_id <> NEW.tenant_id
          AND (otra.valid_to IS NULL OR otra.valid_to > now())
          AND (NEW.role NOT IN ('dpo', 'implementador') OR otra.role NOT IN ('dpo', 'implementador'))
    ) THEN
        RAISE EXCEPTION 'ORGANIZACION_EXCLUSIVA: el usuario % ya tiene un rol vigente en otra organizacion', NEW.user_id
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$
"""

FUNCION_MIS_ORGANIZACIONES = """
CREATE OR REPLACE FUNCTION mis_organizaciones(usuario text)
RETURNS TABLE (tenant_id text, nombre_comercial text, roles text[])
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
    SELECT t.id::text, t.nombre_comercial::text, array_agg(DISTINCT r.role::text ORDER BY r.role::text)
    FROM user_tenant_roles r
    JOIN tenants t ON t.id = r.tenant_id
    WHERE r.user_id = usuario
      AND (r.valid_to IS NULL OR r.valid_to > now())
    GROUP BY t.id, t.nombre_comercial
    ORDER BY t.nombre_comercial, t.id
$$
"""


def upgrade() -> None:
    incumplidores = [fila[0] for fila in op.get_bind().execute(sa.text(INCUMPLIDORES))]
    if incumplidores:
        raise RuntimeError(
            "ORG-13: estas personas (id internos) ya tienen roles vigentes en varias organizaciones "
            "con un rol que no se puede compartir; el propietario debe decidir qué rol retirar antes "
            "de migrar: " + ", ".join(incumplidores)
        )
    op.execute(FUNCION_DISPARADOR)
    op.execute("REVOKE ALL ON FUNCTION verificar_organizaciones_por_persona() FROM PUBLIC")
    op.execute(
        "CREATE TRIGGER trg_utr_organizaciones_por_persona "
        "BEFORE INSERT OR UPDATE ON user_tenant_roles "
        "FOR EACH ROW EXECUTE FUNCTION verificar_organizaciones_por_persona()"
    )
    op.execute(FUNCION_MIS_ORGANIZACIONES)
    op.execute("REVOKE ALL ON FUNCTION mis_organizaciones(text) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION mis_organizaciones(text) TO lopdp_app")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS mis_organizaciones(text)")
    op.execute("DROP TRIGGER IF EXISTS trg_utr_organizaciones_por_persona ON user_tenant_roles")
    op.execute("DROP FUNCTION IF EXISTS verificar_organizaciones_por_persona()")
