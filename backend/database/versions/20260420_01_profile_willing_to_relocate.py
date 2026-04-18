"""Add willing_to_relocate to user_profiles.

Revision ID: 20260420_01
Revises: 20260419_01
Create Date: 2026-04-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260420_01"
down_revision: Union[str, Sequence[str], None] = "20260419_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_profiles",
        sa.Column("willing_to_relocate", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_profiles", "willing_to_relocate")
