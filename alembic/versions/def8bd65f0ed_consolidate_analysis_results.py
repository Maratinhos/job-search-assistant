"""Consolidate analysis results

Revision ID: def8bd65f0ed
Revises: 9c2b05343c2f
Create Date: 2025-09-03 18:45:27.419617

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'def8bd65f0ed'
down_revision: Union[str, Sequence[str], None] = '9c2b05343c2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('analysis_results', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True))
        batch_op.add_column(sa.Column('match_analysis', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('cover_letter', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('hr_call_plan', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('tech_interview_plan', sa.Text(), nullable=True))
        batch_op.create_index(batch_op.f('ix_analysis_results_resume_id'), ['resume_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_analysis_results_vacancy_id'), ['vacancy_id'], unique=False)
        batch_op.create_unique_constraint('uq_resume_vacancy', ['resume_id', 'vacancy_id'])

    with op.batch_alter_table('analysis_results', schema=None) as batch_op:
        batch_op.drop_column('file_path')
        batch_op.drop_column('action_type')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('analysis_results', schema=None) as batch_op:
        batch_op.add_column(sa.Column('action_type', sa.VARCHAR(length=255), nullable=False))
        batch_op.add_column(sa.Column('file_path', sa.VARCHAR(length=255), nullable=False))

    with op.batch_alter_table('analysis_results', schema=None) as batch_op:
        batch_op.drop_constraint('uq_resume_vacancy', type_='unique')
        batch_op.drop_index(batch_op.f('ix_analysis_results_vacancy_id'))
        batch_op.drop_index(batch_op.f('ix_analysis_results_resume_id'))
        batch_op.drop_column('tech_interview_plan')
        batch_op.drop_column('hr_call_plan')
        batch_op.drop_column('cover_letter')
        batch_op.drop_column('match_analysis')
        batch_op.drop_column('created_at')
