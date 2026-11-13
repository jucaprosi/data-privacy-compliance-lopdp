# ¤¤security-engineer
"""DPO-03: consultas de la organización al DPO y su hilo de mensajes, con RLS por organización. ¤dpo-cockpit ¤rbac-tenant"""
from alembic import op
import sqlalchemy as sa

revision = "dpo03_consultas"
down_revision = "norm01_inteligencia_normativa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dpo_consultas",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("asunto", sa.Text(), nullable=False),
        sa.Column("estado", sa.String(length=10), nullable=False),
        sa.Column("creado_por", sa.String(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cerrada_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dictamen_id", sa.String(), nullable=True),
        sa.Column("evidencia_sha256", sa.String(length=64), nullable=True),
        sa.CheckConstraint("estado IN ('abierta','respondida','cerrada')", name="ck_dpo_consultas_estado"),
        sa.CheckConstraint("char_length(asunto) BETWEEN 1 AND 120", name="ck_dpo_consultas_asunto"),
        sa.CheckConstraint(
            "(estado = 'cerrada') = (cerrada_en IS NOT NULL AND dictamen_id IS NOT NULL "
            "AND evidencia_sha256 IS NOT NULL)",
            name="ck_dpo_consultas_cierre_completo",
        ),
    )
    op.create_index("ix_dpo_consultas_tenant_id", "dpo_consultas", ["tenant_id", "creado_en"])

    op.create_table(
        "dpo_consultas_mensajes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("consulta_id", sa.String(), sa.ForeignKey("dpo_consultas.id"), nullable=False),
        sa.Column("secuencia", sa.Integer(), nullable=False),
        sa.Column("autor_id", sa.String(), nullable=False),
        sa.Column("autor_rol", sa.String(length=32), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("consulta_id", "secuencia", name="uq_dpo_consultas_mensajes_secuencia"),
        sa.CheckConstraint("char_length(btrim(texto)) > 0", name="ck_dpo_consultas_mensajes_texto"),
    )
    op.create_index("ix_dpo_consultas_mensajes_tenant_id", "dpo_consultas_mensajes", ["tenant_id", "consulta_id"])

    for tabla in ("dpo_consultas", "dpo_consultas_mensajes"):
        op.execute(f"ALTER TABLE {tabla} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {tabla} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation_{tabla} ON {tabla} "
            "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
            "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
        )
        op.execute(f"REVOKE ALL ON {tabla} FROM lopdp_app")

    # El hilo solo se agrega: sin UPDATE ni DELETE para lopdp_app, y además un trigger que lo impide al dueño.
    op.execute("GRANT SELECT, INSERT ON dpo_consultas_mensajes TO lopdp_app")
    # La consulta solo cambia al responder o cerrar: nunca su asunto ni su autor.
    op.execute("GRANT SELECT, INSERT ON dpo_consultas TO lopdp_app")
    op.execute(
        "GRANT UPDATE (estado, evidencia_sha256, dictamen_id, cerrada_en) ON dpo_consultas TO lopdp_app"
    )

    op.execute(
        """
        CREATE FUNCTION dpo_consultas_mensajes_solo_agrega() RETURNS trigger AS $$
        BEGIN
            IF TG_OP IN ('UPDATE', 'DELETE') THEN
                RAISE EXCEPTION 'dpo_consultas_mensajes es de solo alta' USING ERRCODE = '42501';
            END IF;
            IF EXISTS (SELECT 1 FROM dpo_consultas c WHERE c.id = NEW.consulta_id AND c.estado = 'cerrada') THEN
                RAISE EXCEPTION 'la consulta está cerrada' USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        "CREATE TRIGGER trg_dpo_consultas_mensajes_solo_agrega "
        "BEFORE INSERT OR UPDATE OR DELETE ON dpo_consultas_mensajes "
        "FOR EACH ROW EXECUTE FUNCTION dpo_consultas_mensajes_solo_agrega()"
    )
    op.execute(
        """
        CREATE FUNCTION dpo_consultas_inmutable_tras_cierre() RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'dpo_consultas no se borra' USING ERRCODE = '42501';
            END IF;
            IF OLD.estado = 'cerrada' THEN
                RAISE EXCEPTION 'la consulta está cerrada' USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        "CREATE TRIGGER trg_dpo_consultas_inmutable_tras_cierre "
        "BEFORE UPDATE OR DELETE ON dpo_consultas "
        "FOR EACH ROW EXECUTE FUNCTION dpo_consultas_inmutable_tras_cierre()"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_dpo_consultas_inmutable_tras_cierre ON dpo_consultas")
    op.execute("DROP FUNCTION IF EXISTS dpo_consultas_inmutable_tras_cierre()")
    op.execute("DROP TRIGGER IF EXISTS trg_dpo_consultas_mensajes_solo_agrega ON dpo_consultas_mensajes")
    op.execute("DROP FUNCTION IF EXISTS dpo_consultas_mensajes_solo_agrega()")
    op.drop_index("ix_dpo_consultas_mensajes_tenant_id", table_name="dpo_consultas_mensajes")
    op.drop_table("dpo_consultas_mensajes")
    op.drop_index("ix_dpo_consultas_tenant_id", table_name="dpo_consultas")
    op.drop_table("dpo_consultas")
