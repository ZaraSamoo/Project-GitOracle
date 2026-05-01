"""add saved repositories indexes

Revision ID: ab12c3d4e5f6
Revises: 9574cb866ab0
Create Date: 2026-05-01 20:20:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "ab12c3d4e5f6"
down_revision = "9574cb866ab0"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE INDEX IF NOT EXISTS idx_saved_user ON saved_repositories(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_saved_repo ON saved_repositories(repo_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_saved_user_repo ON saved_repositories(user_id, repo_id)")


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_saved_user_repo")
    op.execute("DROP INDEX IF EXISTS idx_saved_repo")
    op.execute("DROP INDEX IF EXISTS idx_saved_user")
