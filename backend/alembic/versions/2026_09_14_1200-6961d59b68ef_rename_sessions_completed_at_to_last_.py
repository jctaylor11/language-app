"""rename sessions completed_at to last_result_at and add completed_at

Revision ID: 6961d59b68ef
Revises: 1b4ea1074522
Create Date: 2026-09-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6961d59b68ef'
down_revision: Union[str, Sequence[str], None] = '1b4ea1074522'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename written by hand - autogenerate would emit drop + add, losing existing timestamps
    op.alter_column(
        'sessions',
        'completed_at',
        new_column_name='last_result_at'
    )

    # Must run after the rename, since the name is freed by it. Existing sessions stay NULL (not completed)
    op.add_column('sessions', sa.Column('completed_at', postgresql.TIMESTAMP(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('sessions', 'completed_at')     # Completion data is lost on downgrade

    op.alter_column(
        'sessions',
        'last_result_at',
        new_column_name='completed_at'
    )
