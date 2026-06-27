"""add unique constraint to words target and server default to sessions started_at

Revision ID: 4a8b0cb0cb12
Revises: 02e6229abfef
Create Date: 2026-06-27 15:02:07.260650

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a8b0cb0cb12'
down_revision: Union[str, Sequence[str], None] = '02e6229abfef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(None, 'words', ['target'])
    op.alter_column('sessions', 'started_at', server_default=sa.text('now()'))


def downgrade() -> None:
    op.drop_constraint('words_target_key', 'words', type_='unique')
    op.alter_column('sessions', 'started_at', server_default=None)
