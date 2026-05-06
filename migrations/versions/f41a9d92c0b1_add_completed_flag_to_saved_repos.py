"""add completed flag to saved repositories

Revision ID: f41a9d92c0b1
Revises: ab12c3d4e5f6
Create Date: 2026-05-05 15:55:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "f41a9d92c0b1"
down_revision = "ab12c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE saved_repositories "
        "ADD COLUMN IF NOT EXISTS is_completed BOOLEAN NOT NULL DEFAULT FALSE"
    )


def downgrade():
    op.execute("ALTER TABLE saved_repositories DROP COLUMN IF EXISTS is_completed")
