"""add comment content column

Revision ID: 6c1f9c7b4e2a
Revises: 9e8542120d1d
Create Date: 2026-01-22 10:15:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6c1f9c7b4e2a"
down_revision = "9e8542120d1d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "comments",
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
    )
    op.alter_column("comments", "content", server_default=None)


def downgrade() -> None:
    op.drop_column("comments", "content")
