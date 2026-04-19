"""create dummy post

Revision ID: e6e91bad4eac
Revises: 8c725ffe941b
Create Date: 2026-04-12 19:52:18.342224

"""

from typing import Sequence, Union

from alembic import op
from simple_alembic.models import Post

# revision identifiers, used by Alembic.
revision: str = "e6e91bad4eac"
down_revision: Union[str, Sequence[str], None] = "8c725ffe941b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.bulk_insert(
        Post.__table__,  # ty:ignore[invalid-argument-type]
        [
            {
                "slug": "dummy-post",
                "headline": "A dummy post",
                "body": "lorem ipsum dolor sit amet",
            }
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
