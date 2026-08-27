"""add cheated label to result status enum

Revision ID: 87d44bf1010a
Revises: d131507aa777
Create Date: 2026-08-27 17:53:06.021954

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '87d44bf1010a'
down_revision: Union[str, Sequence[str], None] = 'd131507aa777'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE result_status ADD VALUE 'cheated' BEFORE 'skipped'")


def downgrade() -> None:
    """Downgrade schema."""
    # Left unused if downgraded since Postgres cannot drop an enum value
    pass
