"""create posts table

Revision ID: 8c725ffe941b
Revises:
Create Date: 2026-04-12 19:51:06.417999
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8c725ffe941b"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "posts",
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("headline", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("slug"),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table("posts")
