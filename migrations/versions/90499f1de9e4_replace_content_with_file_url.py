"""Replace content with file_url

Revision ID: 90499f1de9e4
Revises: 380d6c004a86
Create Date: 2026-03-17 17:15:47.917557

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '90499f1de9e4'
down_revision: Union[str, Sequence[str], None] = '380d6c004a86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('file_url', sa.String(length=1024), nullable=True))

    op.execute(
        """
        UPDATE documents
        SET file_url = 'legacy-content://document/' || id
        WHERE file_url IS NULL
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('content', sa.TEXT(), nullable=True))

    op.execute(
        """
        UPDATE documents
        SET content = COALESCE(content, file_url)
        WHERE content IS NULL
        """
    )
