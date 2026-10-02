"""rename_cheated_to_peeked

Revision ID: 879be98922e5
Revises: e034e4df4539
Create Date: 2026-10-02 18:54:53.263139

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '879be98922e5'
down_revision: Union[str, Sequence[str], None] = 'e034e4df4539'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE result_status RENAME VALUE 'cheated' TO 'peeked'")
    op.execute("ALTER TYPE sentence_result_status RENAME VALUE 'cheated' TO 'peeked'")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TYPE result_status RENAME VALUE 'peeked' TO 'cheated'")
    op.execute("ALTER TYPE sentence_result_status RENAME VALUE 'peeked' TO 'cheated'")
