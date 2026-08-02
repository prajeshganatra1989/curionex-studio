"""add_production_settings

Revision ID: c5f60b38d9e2
Revises: b4e59a27c8d1
Create Date: 2026-08-02 15:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c5f60b38d9e2"
down_revision: Union[str, Sequence[str], None] = "b4e59a27c8d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "production_settings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "approved_script_target",
            sa.Integer(),
            server_default=sa.text("120"),
            nullable=False,
        ),
        sa.Column(
            "daily_approved_script_target",
            sa.Integer(),
            server_default=sa.text("2"),
            nullable=False,
        ),
        sa.Column(
            "weekly_approved_script_target",
            sa.Integer(),
            server_default=sa.text("14"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["updated_by"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Helpful for membership-scoped production queue joins.
    op.create_index(
        "ix_scripts_project_id_status",
        "scripts",
        ["project_id", "status"],
    )
    op.create_index(
        "ix_ai_jobs_status_created_at",
        "ai_jobs",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_ai_generations_purpose_created_at",
        "ai_generations",
        ["purpose", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_ai_generations_purpose_created_at", table_name="ai_generations")
    op.drop_index("ix_ai_jobs_status_created_at", table_name="ai_jobs")
    op.drop_index("ix_scripts_project_id_status", table_name="scripts")
    op.drop_table("production_settings")
