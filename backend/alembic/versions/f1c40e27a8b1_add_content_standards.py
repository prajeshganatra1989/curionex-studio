"""add content_standards

Revision ID: f1c40e27a8b1
Revises: e8b92d15f3a0
Create Date: 2026-08-02 18:20:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f1c40e27a8b1"
down_revision: Union[str, Sequence[str], None] = "e8b92d15f3a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_standards",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("version", sa.String(length=40), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="draft",
            nullable=False,
        ),
        sa.Column("mission", sa.Text(), nullable=False),
        sa.Column("target_audience", sa.Text(), nullable=False),
        sa.Column("brand_voice", sa.Text(), nullable=False),
        sa.Column("editorial_principles", sa.Text(), nullable=False),
        sa.Column("hook_rules", sa.Text(), nullable=False),
        sa.Column("story_structure", sa.Text(), nullable=False),
        sa.Column("fact_policy", sa.Text(), nullable=False),
        sa.Column("citation_policy", sa.Text(), nullable=False),
        sa.Column("tone_guidelines", sa.Text(), nullable=False),
        sa.Column("language_rules", sa.Text(), nullable=False),
        sa.Column("forbidden_patterns", sa.Text(), nullable=False),
        sa.Column("approved_cta_patterns", sa.Text(), nullable=False),
        sa.Column("quality_checklist", sa.Text(), nullable=False),
        sa.Column(
            "default_duration_seconds",
            sa.Integer(),
            server_default="60",
            nullable=False,
        ),
        sa.Column(
            "default_target_words",
            sa.Integer(),
            server_default="160",
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version", name="uq_content_standards_version"),
    )
    op.create_index(
        "ix_content_standards_status", "content_standards", ["status"], unique=False
    )
    op.create_index(
        "ix_content_standards_version", "content_standards", ["version"], unique=False
    )
    # Partial unique index: at most one active standard.
    op.execute(
        """
        CREATE UNIQUE INDEX uq_content_standards_one_active
        ON content_standards (status)
        WHERE status = 'active'
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_content_standards_one_active")
    op.drop_index("ix_content_standards_version", table_name="content_standards")
    op.drop_index("ix_content_standards_status", table_name="content_standards")
    op.drop_table("content_standards")
