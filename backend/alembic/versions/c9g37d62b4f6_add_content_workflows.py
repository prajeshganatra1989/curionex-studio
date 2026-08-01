"""add_content_workflows

Revision ID: c9g37d62b4f6
Revises: b8f26c51a3e5
Create Date: 2026-08-02 01:20:00.000000

Content production workflow orchestration for M2I.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c9g37d62b4f6"
down_revision: Union[str, Sequence[str], None] = "b8f26c51a3e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_workflows",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("script_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "current_stage",
            sa.String(length=32),
            server_default=sa.text("'workspace'"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column(
            "active_content_version_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["script_id"],
            ["scripts.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["active_content_version_id"],
            ["content_versions.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("script_id", name="uq_content_workflows_script_id"),
    )
    op.create_index(
        "ix_content_workflows_script_id",
        "content_workflows",
        ["script_id"],
        unique=False,
    )
    op.create_index(
        "ix_content_workflows_current_stage",
        "content_workflows",
        ["current_stage"],
        unique=False,
    )
    op.create_index(
        "ix_content_workflows_status",
        "content_workflows",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_content_workflows_active_content_version_id",
        "content_workflows",
        ["active_content_version_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_content_workflows_active_content_version_id",
        table_name="content_workflows",
    )
    op.drop_index("ix_content_workflows_status", table_name="content_workflows")
    op.drop_index("ix_content_workflows_current_stage", table_name="content_workflows")
    op.drop_index("ix_content_workflows_script_id", table_name="content_workflows")
    op.drop_table("content_workflows")
