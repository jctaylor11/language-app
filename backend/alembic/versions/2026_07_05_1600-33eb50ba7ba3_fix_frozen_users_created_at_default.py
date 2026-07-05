"""fix frozen users created_at default

Revision ID: 33eb50ba7ba3
Revises: 334d2c6d0fe9
Create Date: 2026-07-05 16:00:30.108919

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '33eb50ba7ba3'
down_revision: Union[str, Sequence[str], None] = '334d2c6d0fe9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # The original migration set server_default='now()' (a quoted string), which
    # Postgres evaluates once and freezes as a literal timestamp at CREATE TABLE
    # time, instead of the unquoted now() function call that re-evaluates on
    # every insert. Every users row has been getting that same frozen instant
    # as its created_at ever since.
    op.alter_column('users', 'created_at', server_default=sa.text('now()'))


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('users', 'created_at', server_default=sa.text("'now()'"))
