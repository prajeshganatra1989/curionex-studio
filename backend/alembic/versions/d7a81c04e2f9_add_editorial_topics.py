"""add_editorial_topics

Revision ID: d7a81c04e2f9
Revises: c5f60b38d9e2
Create Date: 2026-08-02 16:30:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d7a81c04e2f9"
down_revision: Union[str, Sequence[str], None] = "c5f60b38d9e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "editorial_topics",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=sa.text("'idea'"),
            nullable=False,
        ),
        sa.Column(
            "difficulty",
            sa.String(length=16),
            server_default=sa.text("'medium'"),
            nullable=False,
        ),
        sa.Column(
            "evergreen_score",
            sa.Integer(),
            server_default=sa.text("70"),
            nullable=False,
        ),
        sa.Column(
            "curiosity_score",
            sa.Integer(),
            server_default=sa.text("70"),
            nullable=False,
        ),
        sa.Column(
            "viral_potential",
            sa.String(length=16),
            server_default=sa.text("'medium'"),
            nullable=False,
        ),
        sa.Column(
            "estimated_duration_seconds",
            sa.Integer(),
            server_default=sa.text("45"),
            nullable=False,
        ),
        sa.Column("target_audience", sa.String(length=200), nullable=True),
        sa.Column("source", sa.String(length=200), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("linked_project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("published_video_url", sa.String(length=500), nullable=True),
        sa.Column(
            "is_featured",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
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
            ["linked_project_id"],
            ["projects.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(
        "ix_editorial_topics_category", "editorial_topics", ["category"]
    )
    op.create_index("ix_editorial_topics_status", "editorial_topics", ["status"])
    op.create_index(
        "ix_editorial_topics_difficulty", "editorial_topics", ["difficulty"]
    )
    op.create_index(
        "ix_editorial_topics_linked_project_id",
        "editorial_topics",
        ["linked_project_id"],
    )
    op.create_index(
        "ix_editorial_topics_evergreen_score",
        "editorial_topics",
        ["evergreen_score"],
    )


def downgrade() -> None:
    op.drop_index("ix_editorial_topics_evergreen_score", table_name="editorial_topics")
    op.drop_index(
        "ix_editorial_topics_linked_project_id", table_name="editorial_topics"
    )
    op.drop_index("ix_editorial_topics_difficulty", table_name="editorial_topics")
    op.drop_index("ix_editorial_topics_status", table_name="editorial_topics")
    op.drop_index("ix_editorial_topics_category", table_name="editorial_topics")
    op.drop_table("editorial_topics")
