# ¤¤security-engineer
"""INC-03: estado del incidente (abierto o cerrado) como eventos que solo se agregan. ¤incidentes ¤rbac-tenant

`incidentes` es inmutable (huella encadenada, lopdp_app solo SELECT e INSERT): no tiene columna de estado.
El estado actual es el del último evento de `incidentes_eventos_estado`; sin eventos, el incidente está abierto.
Sin backfill: nada de lo existente se reescribe.
"""
from alembic import op
import sqlalchemy as sa

revision = "inc03_incidentes_estado"
down_revision = "20261031_evidencias_vigencia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Destino de la FK compuesta: DDL, no toca filas ni la huella.
    op.execute("ALTER TABLE incidentes ADD CONSTRAINT uq_incidentes_id_tenant UNIQUE (id, tenant_id)")
    op.create_table(
        "incidentes_eventos_estado",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("incidente_id", sa.String(), nullable=False),
        sa.Column("secuencia", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=16), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("decision_notificacion", sa.Text(), nullable=True),
        sa.Column("registrado_por", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("registrado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("secuencia >= 1", name="ck_incidentes_eventos_secuencia"),
        sa.CheckConstraint("tipo IN ('cierre', 'reapertura')", name="ck_incidentes_eventos_tipo"),
        sa.CheckConstraint("length(trim(motivo)) >= 10", name="ck_incidentes_eventos_motivo"),
        sa.CheckConstraint(
            "decision_notificacion IS NULL OR decision_notificacion = 'pendiente'",
            name="ck_incidentes_eventos_decision",
        ),
        # Dos cierres simultáneos del mismo incidente chocan aquí: el segundo recibe 409.
        sa.UniqueConstraint("incidente_id", "secuencia", name="uq_incidentes_eventos_secuencia"),
        # El evento solo puede colgar de un incidente de su propia organización.
        sa.ForeignKeyConstraint(
            ["incidente_id", "tenant_id"], ["incidentes.id", "incidentes.tenant_id"],
            name="fk_incidentes_eventos_incidente_tenant",
        ),
    )
    op.execute("ALTER TABLE incidentes_eventos_estado ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE incidentes_eventos_estado FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_incidentes_eventos_estado ON incidentes_eventos_estado "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("REVOKE ALL ON incidentes_eventos_estado FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT ON incidentes_eventos_estado TO lopdp_app")


def downgrade() -> None:
    op.drop_table("incidentes_eventos_estado")
    op.execute("ALTER TABLE incidentes DROP CONSTRAINT IF EXISTS uq_incidentes_id_tenant")
