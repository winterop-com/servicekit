"""Initial database schema migration - no tables for pure framework."""

# revision identifiers, used by Alembic.
revision = "4d869b5fb06e"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply database schema changes."""
    # Servicekit is a pure framework - no domain-specific tables
    # Domain tables (tasks, artifacts, configs) are provided by chapkit
    pass


def downgrade() -> None:
    """Revert database schema changes."""
    pass
