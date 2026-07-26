"""fix frozen user_words added_at and sentences created_at defaults

Revision ID: c0c693fdf3b8
Revises: 9da2458b7250
Create Date: 2026-07-26 16:31:08.250510

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0c693fdf3b8'
down_revision: Union[str, Sequence[str], None] = '9da2458b7250'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Same frozen-default bug that 33eb50ba7ba3 fixed for users.created_at, in the two
    # columns it missed: server_default='now()' is a quoted string, so Postgres evaluates
    # it once at CREATE TABLE time and freezes that instant as a literal. Every row has
    # been stamped with the migration's own timestamp instead of its insert time.
    op.alter_column('user_words', 'added_at', server_default=sa.text('now()'))
    op.alter_column('sentences', 'created_at', server_default=sa.text('now()'))


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('sentences', 'created_at', server_default=sa.text("'now()'"))
    op.alter_column('user_words', 'added_at', server_default=sa.text("'now()'"))
