"""drop todo tag column

Revision ID: aeeb0e9aa4df
Revises: 7ee3f652716e
Create Date: 2026-05-21 03:28:22.535077

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aeeb0e9aa4df'
down_revision: Union[str, Sequence[str], None] = '7ee3f652716e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        INSERT INTO tag (title, description, created_at)
        SELECT DISTINCT todo.tag, '(自動生成)', NOW()
        FROM todo
        WHERE todo.tag IS NOT NULL AND todo.tag != ''
          AND NOT EXISTS (SELECT 1 FROM tag WHERE tag.title = todo.tag)
    """)
    op.execute("""
        INSERT INTO todo_tag (todo_id, tag_id)
        SELECT todo.id, tag.id
        FROM todo
        JOIN tag ON tag.title = todo.tag
        WHERE todo.tag IS NOT NULL AND todo.tag != ''
    """)
    # カラム削除
    op.drop_index('ix_todo_tag', table_name='todo')
    op.drop_column('todo', 'tag')


def downgrade() -> None:
    """Downgrade schema."""
    pass
