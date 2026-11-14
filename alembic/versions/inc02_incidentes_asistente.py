# ¤¤security-engineer
"""INC-02: asistente de vulneración en ocho secciones, en tablas que solo se agregan. ¤incidentes ¤hallazgos

`incidentes` no se toca (INC-01 la define inmutable; lopdp_app solo SELECT e INSERT). Cada guardado de
una sección es una versión nueva; la vigente es la de mayor `version`. Informes, notificaciones,
tratamientos y lecciones también solo se agregan. Las cinco tablas cuelgan de `incidentes` por la FK
compuesta (incidente_id, tenant_id) sobre `uq_incidentes_id_tenant` (INC-03).
"""
from alembic import op
import sqlalchemy as sa

revision = "inc02_incidentes_asistente"
down_revision = "norm02_nota_revision"
branch_labels = None
depends_on = None

_TABLAS = (
    "incidentes_asistente_secciones",
    "incidentes_informes",
    "incidentes_notificaciones",
    "incidentes_tratamientos",
    "incidentes_lecciones",
)


def _comunes() -> list:
    return [
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("incidente_id", sa.String(), nullable=False),
    ]


def _fk(nombre: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        ["incidente_id", "tenant_id"], ["incidentes.id", "incidentes.tenant_id"], name=f"fk_{nombre}_incidente_tenant"
    )


def _autoria() -> list:
    return [
        sa.Column("registrado_por", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("registrado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    ]


def upgrade() -> None:
    op.create_table(
        "incidentes_asistente_secciones",
        *_comunes(),
        sa.Column("seccion", sa.SmallInteger(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("datos", sa.dialects.postgresql.JSONB(), nullable=False),
        *_autoria(),
        sa.CheckConstraint("seccion BETWEEN 1 AND 8", name="ck_inc_secciones_rango"),
        sa.CheckConstraint("version >= 1", name="ck_inc_secciones_version"),
        sa.CheckConstraint(
            "seccion <> 4 OR datos->>'tipo' IN ('confidencialidad', 'integridad', 'disponibilidad')",
            name="ck_inc_secciones_tipo",
        ),
        sa.CheckConstraint(
            "seccion <> 7 OR (datos->>'decision' IN ('spdp', 'titulares', 'ambos', 'ninguno') "
            "AND length(trim(coalesce(datos->>'justificacion', ''))) >= 20)",
            name="ck_inc_secciones_decision",
        ),
        # Dos guardados simultáneos de la misma sección chocan aquí: el segundo recibe 409.
        sa.UniqueConstraint("incidente_id", "seccion", "version", name="uq_inc_secciones_version"),
        _fk("inc_secciones"),
    )
    op.create_table(
        "incidentes_informes",
        *_comunes(),
        sa.Column("destino", sa.String(length=10), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("evidencia_id", sa.String(), nullable=False),
        sa.Column("emitido_por", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("emitido_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("destino IN ('spdp', 'titulares')", name="ck_inc_informes_destino"),
        sa.CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'", name="ck_inc_informes_sha256"),
        _fk("inc_informes"),
    )
    op.create_table(
        "incidentes_notificaciones",
        *_comunes(),
        sa.Column("destino", sa.String(length=10), nullable=False),
        sa.Column("notificado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidencia_sha256", sa.String(length=64), nullable=False),
        *_autoria(),
        sa.CheckConstraint("destino IN ('spdp', 'titulares')", name="ck_inc_notificaciones_destino"),
        sa.CheckConstraint("evidencia_sha256 ~ '^[0-9a-f]{64}$'", name="ck_inc_notificaciones_sha256"),
        _fk("inc_notificaciones"),
    )
    op.create_table(
        "incidentes_tratamientos",
        *_comunes(),
        sa.Column("tratamiento_id", sa.String(), nullable=False),
        *_autoria(),
        _fk("inc_tratamientos"),
    )
    op.create_table(
        "incidentes_lecciones",
        *_comunes(),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("hallazgo_id", sa.String(), nullable=True),
        *_autoria(),
        sa.CheckConstraint("numero >= 1", name="ck_inc_lecciones_numero"),
        sa.CheckConstraint("length(trim(texto)) >= 1", name="ck_inc_lecciones_texto"),
        sa.UniqueConstraint("incidente_id", "numero", name="uq_inc_lecciones_numero"),
        _fk("inc_lecciones"),
    )
    for tabla in _TABLAS:
        op.execute(f"ALTER TABLE {tabla} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {tabla} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation_{tabla} ON {tabla} "
            "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
            "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
        )
        op.execute(f"REVOKE ALL ON {tabla} FROM lopdp_app")
        op.execute(f"GRANT SELECT, INSERT ON {tabla} TO lopdp_app")


def downgrade() -> None:
    for tabla in reversed(_TABLAS):
        op.drop_table(tabla)
