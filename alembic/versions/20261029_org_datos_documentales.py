# ¤rbac-tenant
"""ORG-14: datos de la organización para documentos (domicilio, contactos y representante legal).

Solo añade columnas opcionales a `tenants`: no cambia columnas existentes ni exige valores a las
organizaciones ya creadas. El formato de cada valor lo valida el servidor
(`features/organizacion/services/datos_documentales_engine.py`); aquí solo se acota la longitud.
Los permisos de `lopdp_app` sobre `tenants` son de tabla y cubren las columnas nuevas.
"""
from alembic import op
import sqlalchemy as sa

revision = "20261029_org_datos_documentales"
down_revision = "20261028_organizaciones_persona"
branch_labels = None
depends_on = None

COLUMNAS = (
    ("direccion", 300),
    ("ciudad", 120),
    ("telefono", 30),
    ("correo_contacto", 254),
    ("correo_privacidad", 254),
    ("sitio_web", 300),
    ("representante_legal_nombre", 200),
    ("representante_legal_identificacion", 13),
    ("representante_legal_cargo", 150),
)


def upgrade() -> None:
    for nombre, longitud in COLUMNAS:
        op.add_column("tenants", sa.Column(nombre, sa.String(length=longitud), nullable=True))


def downgrade() -> None:
    for nombre, _ in reversed(COLUMNAS):
        op.drop_column("tenants", nombre)
