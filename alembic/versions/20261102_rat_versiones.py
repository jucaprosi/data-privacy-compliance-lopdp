# ¤¤security-engineer
"""RAT-05: versiones inmutables de cada ficha y origen `rat` de los hallazgos. ¤rat ¤hallazgos ¤rbac-tenant

- Tabla `rat_versiones` por organización, con RLS (ENABLE y FORCE, USING y WITH CHECK por tenant_id).
  Append-only: la aplicación (lopdp_app) solo lee e inserta.
- `rat_actividades.condicion_habilitante`: circunstancia del art. 26 LOPDP que permite tratar datos
  sensibles. Nula mientras no se declare. lopdp_app ya tiene UPDATE sobre toda la tabla.
- `ck_hallazgos_origen` admite `rat`.

Contrato: governance/especificaciones/RAT-05.md §1 y §3.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261102_rat_versiones"
down_revision = "20261030_controles_periodicos"
branch_labels = None
depends_on = None

_ORIGENES = "'diagnostico','auditoria','eipd','incidente','tercero','control_periodico'"
_CONDICIONES = (
    "'CONSENTIMIENTO_EXPLICITO','LABORAL_SEGURIDAD_SOCIAL','INTERESES_VITALES','DATOS_PUBLICOS',"
    "'ORDEN_JUDICIAL','ARCHIVO_INVESTIGACION_ESTADISTICA','SALUD_SEGUN_LEY'"
)


def upgrade() -> None:
    op.create_table(
        "rat_versiones",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("tratamiento_id", sa.String(), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("contenido", postgresql.JSONB(), nullable=False),
        sa.Column("creado_por", sa.String(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "tratamiento_id", "numero", name="ux_rat_versiones_numero"),
    )
    op.execute("ALTER TABLE rat_versiones ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE rat_versiones FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_rat_versiones ON rat_versiones "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("REVOKE ALL ON rat_versiones FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT ON rat_versiones TO lopdp_app")

    op.add_column("rat_actividades", sa.Column("condicion_habilitante", sa.Text(), nullable=True))
    op.create_check_constraint(
        "ck_rat_condicion_habilitante", "rat_actividades", f"condicion_habilitante IN ({_CONDICIONES})"
    )

    op.drop_constraint("ck_hallazgos_origen", "hallazgos", type_="check")
    op.create_check_constraint("ck_hallazgos_origen", "hallazgos", f"origen IN ({_ORIGENES},'rat')")


def downgrade() -> None:
    # Si ya hay hallazgos de origen `rat`, se deja que la base lo rechace: borrarlos perdería el plan de acción.
    op.drop_constraint("ck_hallazgos_origen", "hallazgos", type_="check")
    op.create_check_constraint("ck_hallazgos_origen", "hallazgos", f"origen IN ({_ORIGENES})")
    op.drop_constraint("ck_rat_condicion_habilitante", "rat_actividades", type_="check")
    op.drop_column("rat_actividades", "condicion_habilitante")
    op.drop_table("rat_versiones")
