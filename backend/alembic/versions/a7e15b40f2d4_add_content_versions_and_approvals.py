"""add_content_versions_and_approvals

Revision ID: a7e15b40f2d4
Revises: f6d04a39e1c3
Create Date: 2026-08-02 00:20:00.000000

Immutable ContentVersion snapshots and append-only Approvals for M2G.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a7e15b40f2d4"
down_revision: Union[str, Sequence[str], None] = "f6d04a39e1c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_versions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=sa.text("'draft'"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "version_number",
            name="uq_content_versions_project_version_number",
        ),
    )
    op.create_index(
        "ix_content_versions_project_id",
        "content_versions",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_content_versions_status",
        "content_versions",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_content_versions_created_by",
        "content_versions",
        ["created_by"],
        unique=False,
    )
    op.create_index(
        "ix_content_versions_project_version",
        "content_versions",
        ["project_id", "version_number"],
        unique=False,
    )

    op.create_table(
        "approvals",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("content_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["content_version_id"],
            ["content_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_approvals_content_version_id",
        "approvals",
        ["content_version_id"],
        unique=False,
    )
    op.create_index("ix_approvals_status", "approvals", ["status"], unique=False)
    op.create_index(
        "ix_approvals_requested_by",
        "approvals",
        ["requested_by"],
        unique=False,
    )
    # At most one pending approval per content version.
    op.create_index(
        "uq_approvals_pending_per_version",
        "approvals",
        ["content_version_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_approvals_pending_per_version",
        table_name="approvals",
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.drop_index("ix_approvals_requested_by", table_name="approvals")
    op.drop_index("ix_approvals_status", table_name="approvals")
    op.drop_index("ix_approvals_content_version_id", table_name="approvals")
    op.drop_table("approvals")

    op.drop_index(
        "ix_content_versions_project_version",
        table_name="content_versions",
    )
    op.drop_index("ix_content_versions_created_by", table_name="content_versions")
    op.drop_index("ix_content_versions_status", table_name="content_versions")
    op.drop_index("ix_content_versions_project_id", table_name="content_versions")
    op.drop_table("content_versions")
