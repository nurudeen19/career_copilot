"""workflow_threads: map LangGraph thread_id to user for secure deletion.

Revision ID: 20260424_01
Revises: 20260421_01
Create Date: 2026-04-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260424_01"
down_revision: Union[str, Sequence[str], None] = "20260421_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workflow_threads",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("thread_id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("thread_id"),
    )
    op.create_index(op.f("ix_workflow_threads_user_id"), "workflow_threads", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_workflow_threads_user_id"), table_name="workflow_threads")
    op.drop_table("workflow_threads")
