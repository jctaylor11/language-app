"""cascade delete rows dependent on users and sessions

Revision ID: 9da2458b7250
Revises: 40977b73b613
Create Date: 2026-07-19 17:03:29.347194

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9da2458b7250'
down_revision: Union[str, Sequence[str], None] = '40977b73b613'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("sessions_user_id_fkey", "sessions", type_="foreignkey")
    op.create_foreign_key("sessions_user_id_fkey", "sessions", "users", ["user_id"], ["id"], ondelete="CASCADE")

    op.drop_constraint("user_words_user_id_fkey", "user_words", type_="foreignkey")
    op.create_foreign_key("user_words_user_id_fkey", "user_words", "users", ["user_id"], ["id"], ondelete="CASCADE")

    # vocab_results constraints kept their session_results_* names through the table rename; recreate under current names
    op.drop_constraint("session_results_user_id_fkey", "vocab_results", type_="foreignkey")
    op.create_foreign_key("vocab_results_user_id_fkey", "vocab_results", "users", ["user_id"], ["id"], ondelete="CASCADE")

    op.drop_constraint("session_results_session_id_fkey", "vocab_results", type_="foreignkey")
    op.create_foreign_key("vocab_results_session_id_fkey", "vocab_results", "sessions", ["session_id"], ["id"], ondelete="CASCADE")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("vocab_results_session_id_fkey", "vocab_results", type_="foreignkey")
    op.create_foreign_key("session_results_session_id_fkey", "vocab_results", "sessions", ["session_id"], ["id"])

    op.drop_constraint("vocab_results_user_id_fkey", "vocab_results", type_="foreignkey")
    op.create_foreign_key("session_results_user_id_fkey", "vocab_results", "users", ["user_id"], ["id"])

    op.drop_constraint("user_words_user_id_fkey", "user_words", type_="foreignkey")
    op.create_foreign_key("user_words_user_id_fkey", "user_words", "users", ["user_id"], ["id"])

    op.drop_constraint("sessions_user_id_fkey", "sessions", type_="foreignkey")
    op.create_foreign_key("sessions_user_id_fkey", "sessions", "users", ["user_id"], ["id"])
