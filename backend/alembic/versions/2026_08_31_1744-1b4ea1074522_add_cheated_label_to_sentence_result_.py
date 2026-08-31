"""add cheated label to sentence result status enum

Revision ID: 1b4ea1074522
Revises: 87d44bf1010a
Create Date: 2026-08-31 17:44:56.273194

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '1b4ea1074522'
down_revision: Union[str, Sequence[str], None] = '87d44bf1010a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE sentence_result_status ADD VALUE 'cheated' BEFORE 'skipped'")


def downgrade() -> None:
    """Downgrade schema."""
    # Left unused if downgraded since Postgres cannot drop an enum value
    pass
