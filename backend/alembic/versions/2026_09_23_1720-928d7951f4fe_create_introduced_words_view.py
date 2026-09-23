"""create introduced_words view

Revision ID: 928d7951f4fe
Revises: 6961d59b68ef
Create Date: 2026-09-23 17:20:53.274416

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '928d7951f4fe'
down_revision: Union[str, Sequence[str], None] = '6961d59b68ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema. This view includes all words except for those that are skipped or cheated. And therefore, words they have reasonably been awarded in line with Principle 1 (Progress metrics must be earned)"""
    op.execute("""
        CREATE VIEW introduced_words AS
        SELECT user_id, word_id, MIN(answered_at) AS introduced_at
        FROM vocab_results
        WHERE status IN ('correct_first_try', 'corrected')
        GROUP BY user_id, word_id
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
        DROP VIEW introduced_words
    """)
