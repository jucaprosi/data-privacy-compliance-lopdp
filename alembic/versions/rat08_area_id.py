# ¤¤backend-developer
"""RAT-08: Área responsable del tratamiento como referencia al área de la organización. ¤rat

Revision ID: rat08_area_id
Revises: ret02_clave_objeto
Create Date: 2026-11-16

Primera migración de la sala rat en el esquema CI-28 (cuelga de BASE_COMUN).
Cambios:
- uq_areas_id_tenant UNIQUE (id, tenant_id) en areas
- area_id VARCHAR NULL en rat_actividades
- fk_rat_area FOREIGN KEY (area_id, tenant_id) REFERENCES areas(id, tenant_id)
- ix_rat_actividades_area INDEX (tenant_id, area_id)
- Migración de datos: empareja por lower(trim) de coincidencias únicas
"""
from alembic import op
import sqlalchemy as sa

revision = "rat08_area_id"
down_revision = "ret02_clave_objeto"
branch_labels = ("rat",)
depends_on = None


def upgrade() -> None:
    # 1. Restricción única en areas para permitir FK compuesta
    op.execute("ALTER TABLE areas ADD CONSTRAINT uq_areas_id_tenant UNIQUE (id, tenant_id);")

    # 2. Columna area_id en rat_actividades
    op.execute("ALTER TABLE rat_actividades ADD COLUMN area_id VARCHAR;")

    # 3. Foreign key compuesta que asegura mismo tenant
    op.execute(
        "ALTER TABLE rat_actividades ADD CONSTRAINT fk_rat_area "
        "FOREIGN KEY (area_id, tenant_id) REFERENCES areas (id, tenant_id);"
    )

    # 4. Índice para búsquedas por tenant y área
    op.execute("CREATE INDEX ix_rat_actividades_area ON rat_actividades (tenant_id, area_id);")

    # 5. Emparejado de datos existentes:
    # lower(trim(area_responsable)) = lower(trim(nombre)) de exactamente un área viva (deleted_at IS NULL)
    conn = op.get_bind()

    # Recuento antes de actualizar
    res_conteos = conn.execute(sa.text("""
        SELECT categoria, count(*) AS total FROM (
            SELECT
                r.id,
                CASE
                    WHEN count(a.id) = 1 THEN 'emparejada'
                    WHEN count(a.id) = 0 THEN 'sin_emparejar'
                    ELSE 'ambigua'
                END AS categoria
            FROM rat_actividades r
            LEFT JOIN areas a
                ON a.tenant_id = r.tenant_id
                AND a.deleted_at IS NULL
                AND lower(trim(a.nombre)) = lower(trim(r.area_responsable))
            GROUP BY r.id
        ) sub GROUP BY categoria;
    """)).fetchall()

    conteos = {row[0]: row[1] for row in res_conteos}
    emparejadas = conteos.get("emparejada", 0)
    sin_emparejar = conteos.get("sin_emparejar", 0)
    ambiguas = conteos.get("ambigua", 0)

    # Actualizar solo coincidencias únicas
    conn.execute(sa.text("""
        UPDATE rat_actividades r
        SET area_id = m.area_id
        FROM (
            SELECT
                r2.id AS rat_id,
                min(a.id) AS area_id
            FROM rat_actividades r2
            JOIN areas a
                ON a.tenant_id = r2.tenant_id
                AND a.deleted_at IS NULL
                AND lower(trim(a.nombre)) = lower(trim(r2.area_responsable))
            GROUP BY r2.id
            HAVING count(a.id) = 1
        ) m
        WHERE r.id = m.rat_id;
    """))

    print(f"[RAT-08] Datos migrados: {emparejadas} emparejadas, {sin_emparejar} sin emparejar, {ambiguas} ambiguas.")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_rat_actividades_area;")
    op.execute("ALTER TABLE rat_actividades DROP CONSTRAINT IF EXISTS fk_rat_area;")
    op.execute("ALTER TABLE rat_actividades DROP COLUMN IF EXISTS area_id;")
    op.execute("ALTER TABLE areas DROP CONSTRAINT IF EXISTS uq_areas_id_tenant;")
