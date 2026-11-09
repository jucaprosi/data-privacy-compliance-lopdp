"""BIB-117: el dueño de la base concede y revoca capacidades de la Biblioteca pese a la RLS forzada; nadie se las concede a sí mismo. ¤seguridad

Revision ID: 20261108_bib_cap_propietario
Revises: 20261030_diagnostico_no_aplica

Con FORCE ROW LEVEL SECURITY, el dueño de una tabla también queda sujeto a sus políticas, salvo que su rol
tenga BYPASSRLS (en Neon y en Cloud SQL no es el mismo atributo). La migración base solo dio una política de
SELECT, `bib_cap_propia`, que filtra por `app.current_user_id`. Sin BYPASSRLS el dueño no podía listar ni
revocar capacidades ajenas, y el disparador `bib_auditar_capacidad` (SECURITY DEFINER, del mismo dueño) no
podía escribir en `biblioteca_auditoria_capacidades`. Las políticas `TO CURRENT_USER` (el rol que migra, el
dueño) lo vuelven determinista. `lopdp_app` sigue solo con SELECT de sus filas: ninguna política nueva es
para él, y no hay política de DELETE (se revoca con UPDATE).
"""
from alembic import op

revision = "20261108_bib_cap_propietario"
down_revision = "20261030_diagnostico_no_aplica"
branch_labels = None
depends_on = None

# ¤adpa
def upgrade() -> None:
    # Una política TO CURRENT_USER corrida como la aplicación le daría la escritura: se aborta antes.
    op.execute("""
        DO $$ BEGIN
            IF current_user = 'lopdp_app' THEN
                RAISE EXCEPTION 'BIB-117: la migración no se corre como lopdp_app';
            END IF;
        END $$;
    """)
    op.execute("""
        ALTER TABLE biblioteca_capacidades
            ADD CONSTRAINT bib_cap_sin_autoconcesion CHECK (usuario_id <> concedida_por),
            ADD CONSTRAINT bib_cap_sin_autorrevocacion CHECK (revocada_por IS NULL OR revocada_por <> usuario_id);

        CREATE POLICY bib_cap_propietario_lectura ON biblioteca_capacidades
            FOR SELECT TO CURRENT_USER USING (true);
        CREATE POLICY bib_cap_propietario_alta ON biblioteca_capacidades
            FOR INSERT TO CURRENT_USER WITH CHECK (usuario_id <> concedida_por);
        CREATE POLICY bib_cap_propietario_cambio ON biblioteca_capacidades
            FOR UPDATE TO CURRENT_USER USING (true)
            WITH CHECK (usuario_id <> concedida_por AND (revocada_por IS NULL OR revocada_por <> usuario_id));

        CREATE POLICY bib_audcap_propietario_lectura ON biblioteca_auditoria_capacidades
            FOR SELECT TO CURRENT_USER USING (true);
        CREATE POLICY bib_audcap_propietario_alta ON biblioteca_auditoria_capacidades
            FOR INSERT TO CURRENT_USER WITH CHECK (true);
    """)


# ¤adpa
def downgrade() -> None:
    op.execute("""
        DROP POLICY IF EXISTS bib_audcap_propietario_alta ON biblioteca_auditoria_capacidades;
        DROP POLICY IF EXISTS bib_audcap_propietario_lectura ON biblioteca_auditoria_capacidades;
        DROP POLICY IF EXISTS bib_cap_propietario_cambio ON biblioteca_capacidades;
        DROP POLICY IF EXISTS bib_cap_propietario_alta ON biblioteca_capacidades;
        DROP POLICY IF EXISTS bib_cap_propietario_lectura ON biblioteca_capacidades;
    """)
    op.execute("""
        ALTER TABLE biblioteca_capacidades
            DROP CONSTRAINT IF EXISTS bib_cap_sin_autorrevocacion,
            DROP CONSTRAINT IF EXISTS bib_cap_sin_autoconcesion;
    """)
