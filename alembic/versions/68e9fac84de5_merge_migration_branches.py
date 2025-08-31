"""merge migration branches

Revision ID: 68e9fac84de5
Revises: 553f705546c6, 69ed90b555f5
Create Date: 2025-08-31 21:47:56.357841

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68e9fac84de5'
down_revision: Union[str, Sequence[str], None] = ('553f705546c6', '69ed90b555f5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
