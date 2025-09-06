"""add utm_track table

Revision ID: 630785bf65fd
Revises: 2c2cdbbe5226
Create Date: 2025-09-06 19:39:26.074358

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '630785bf65fd'
down_revision: Union[str, Sequence[str], None] = '2c2cdbbe5226'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    if bind.engine.name == 'postgresql':
        now_func = sa.text('now()')
    else:
        now_func = sa.text('CURRENT_TIMESTAMP')

    op.create_table(
        'utm_track',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('utm_source', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=now_func, nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('utm_track')
