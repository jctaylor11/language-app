"""rename session_results to vocab_results

Revision ID: 293af9d7c673
Revises: abc8e711eff2
Create Date: 2026-06-08 23:18:42.092324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '293af9d7c673'
down_revision: Union[str, Sequence[str], None] = 'abc8e711eff2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table("session_results", "vocab_results")


def downgrade() -> None:
    """Downgrade schema."""
    op.rename_table("vocab_results", "session_results")
