"""rename pre_correct_input to raw_keystrokes

Revision ID: 4d36249dcf42
Revises: 5e4d074dba55
Create Date: 2026-05-10 23:27:26.572479

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d36249dcf42'
down_revision: Union[str, Sequence[str], None] = '5e4d074dba55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'session_results',
        'pre_correction_input',
        new_column_name='raw_keystrokes'
    )


def downgrade() -> None:
    op.alter_column(
        'session_results',
        'raw_keystrokes',
        new_column_name='pre_correction_input'
    )