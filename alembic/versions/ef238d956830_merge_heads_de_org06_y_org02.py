"""merge heads de org06 y org02

Revision ID: ef238d956830
Revises: 20261019_org06_designaciones, 20261020_sod_exceptions
Create Date: 2026-10-20 10:38:39.188699

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef238d956830'
down_revision: Union[str, None] = ('20261019_org06_designaciones', '20261020_sod_exceptions')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
