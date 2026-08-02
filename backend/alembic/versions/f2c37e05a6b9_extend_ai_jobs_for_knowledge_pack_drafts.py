"""extend_ai_jobs_for_knowledge_pack_drafts

Revision ID: f2c37e05a6b9
Revises: e1b26d94f5a8
Create Date: 2026-08-02 12:30:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f2c37e05a6b9"
down_revision: Union[str, Sequence[str], None] = "e1b26d94f5a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ai_jobs",
        sa.Column("purpose", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "ai_jobs",
        sa.Column("knowledge_pack_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "ai_jobs",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "ai_jobs",
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "ai_jobs",
        sa.Column(
            "cancel_requested",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.create_foreign_key(
        "fk_ai_jobs_knowledge_pack_id",
        "ai_jobs",
        "knowledge_packs",
        ["knowledge_pack_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_ai_jobs_project_id",
        "ai_jobs",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_ai_jobs_purpose", "ai_jobs", ["purpose"])
    op.create_index("ix_ai_jobs_knowledge_pack_id", "ai_jobs", ["knowledge_pack_id"])
    op.create_index("ix_ai_jobs_project_id", "ai_jobs", ["project_id"])
    op.create_index(
        "uq_ai_jobs_requester_idempotency",
        "ai_jobs",
        ["requested_by", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )

    op.add_column(
        "ai_generations",
        sa.Column("purpose", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "ai_generations",
        sa.Column("knowledge_pack_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "ai_generations",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "ai_generations",
        sa.Column("structured_output_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "ai_generations",
        sa.Column("provider_request_id", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "ai_generations",
        sa.Column("model_identifier", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "ai_generations",
        sa.Column("tokens_total", sa.Integer(), nullable=True),
    )
    op.add_column(
        "ai_generations",
        sa.Column(
            "applied_sections_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "ai_generations",
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_ai_generations_knowledge_pack_id",
        "ai_generations",
        "knowledge_packs",
        ["knowledge_pack_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_ai_generations_project_id",
        "ai_generations",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_ai_generations_purpose", "ai_generations", ["purpose"])
    op.create_index(
        "ix_ai_generations_knowledge_pack_id", "ai_generations", ["knowledge_pack_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_ai_generations_knowledge_pack_id", table_name="ai_generations")
    op.drop_index("ix_ai_generations_purpose", table_name="ai_generations")
    op.drop_constraint("fk_ai_generations_project_id", "ai_generations", type_="foreignkey")
    op.drop_constraint(
        "fk_ai_generations_knowledge_pack_id", "ai_generations", type_="foreignkey"
    )
    op.drop_column("ai_generations", "applied_at")
    op.drop_column("ai_generations", "applied_sections_json")
    op.drop_column("ai_generations", "tokens_total")
    op.drop_column("ai_generations", "model_identifier")
    op.drop_column("ai_generations", "provider_request_id")
    op.drop_column("ai_generations", "structured_output_json")
    op.drop_column("ai_generations", "project_id")
    op.drop_column("ai_generations", "knowledge_pack_id")
    op.drop_column("ai_generations", "purpose")

    op.drop_index("uq_ai_jobs_requester_idempotency", table_name="ai_jobs")
    op.drop_index("ix_ai_jobs_project_id", table_name="ai_jobs")
    op.drop_index("ix_ai_jobs_knowledge_pack_id", table_name="ai_jobs")
    op.drop_index("ix_ai_jobs_purpose", table_name="ai_jobs")
    op.drop_constraint("fk_ai_jobs_project_id", "ai_jobs", type_="foreignkey")
    op.drop_constraint("fk_ai_jobs_knowledge_pack_id", "ai_jobs", type_="foreignkey")
    op.drop_column("ai_jobs", "cancel_requested")
    op.drop_column("ai_jobs", "idempotency_key")
    op.drop_column("ai_jobs", "project_id")
    op.drop_column("ai_jobs", "knowledge_pack_id")
    op.drop_column("ai_jobs", "purpose")
