"""add_script_ai_draft_fields

Revision ID: a3d48f16b7c0
Revises: f2c37e05a6b9
Create Date: 2026-08-02 13:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a3d48f16b7c0"
down_revision: Union[str, Sequence[str], None] = "f2c37e05a6b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ai_jobs",
        sa.Column("script_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "ai_jobs",
        sa.Column("document_type", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "ai_jobs",
        sa.Column(
            "input_fingerprint_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_ai_jobs_script_id",
        "ai_jobs",
        "scripts",
        ["script_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_ai_jobs_script_id", "ai_jobs", ["script_id"])
    op.create_index("ix_ai_jobs_document_type", "ai_jobs", ["document_type"])
    op.create_index(
        "uq_ai_jobs_script_doc_idempotency",
        "ai_jobs",
        ["requested_by", "script_id", "document_type", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text(
            "idempotency_key IS NOT NULL AND script_id IS NOT NULL "
            "AND document_type IS NOT NULL"
        ),
    )

    op.add_column(
        "ai_generations",
        sa.Column("script_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "ai_generations",
        sa.Column("document_type", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "ai_generations",
        sa.Column(
            "input_fingerprint_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "ai_generations",
        sa.Column(
            "warnings_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.create_foreign_key(
        "fk_ai_generations_script_id",
        "ai_generations",
        "scripts",
        ["script_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_ai_generations_script_id", "ai_generations", ["script_id"])
    op.create_index(
        "ix_ai_generations_document_type", "ai_generations", ["document_type"]
    )

    op.add_column(
        "ai_settings",
        sa.Column(
            "brand_voice",
            sa.Text(),
            nullable=True,
        ),
    )
    op.add_column(
        "ai_settings",
        sa.Column(
            "quality_requirements",
            sa.Text(),
            nullable=True,
        ),
    )
    op.add_column(
        "ai_settings",
        sa.Column(
            "default_target_duration_seconds",
            sa.Integer(),
            server_default=sa.text("60"),
            nullable=False,
        ),
    )
    op.add_column(
        "ai_settings",
        sa.Column(
            "default_target_words_per_minute",
            sa.Integer(),
            server_default=sa.text("150"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("ai_settings", "default_target_words_per_minute")
    op.drop_column("ai_settings", "default_target_duration_seconds")
    op.drop_column("ai_settings", "quality_requirements")
    op.drop_column("ai_settings", "brand_voice")

    op.drop_index("ix_ai_generations_document_type", table_name="ai_generations")
    op.drop_index("ix_ai_generations_script_id", table_name="ai_generations")
    op.drop_constraint(
        "fk_ai_generations_script_id", "ai_generations", type_="foreignkey"
    )
    op.drop_column("ai_generations", "warnings_json")
    op.drop_column("ai_generations", "input_fingerprint_json")
    op.drop_column("ai_generations", "document_type")
    op.drop_column("ai_generations", "script_id")

    op.drop_index("uq_ai_jobs_script_doc_idempotency", table_name="ai_jobs")
    op.drop_index("ix_ai_jobs_document_type", table_name="ai_jobs")
    op.drop_index("ix_ai_jobs_script_id", table_name="ai_jobs")
    op.drop_constraint("fk_ai_jobs_script_id", "ai_jobs", type_="foreignkey")
    op.drop_column("ai_jobs", "input_fingerprint_json")
    op.drop_column("ai_jobs", "document_type")
    op.drop_column("ai_jobs", "script_id")
