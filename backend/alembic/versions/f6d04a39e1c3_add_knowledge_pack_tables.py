"""add_knowledge_pack_tables

Revision ID: f6d04a39e1c3
Revises: e5c93f28d0b2
Create Date: 2026-08-02 00:10:00.000000

Knowledge Pack foundation for M2F: knowledge_packs and knowledge_pack_sections.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f6d04a39e1c3"
down_revision: Union[str, Sequence[str], None] = "e5c93f28d0b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_packs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=sa.text("'draft'"),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
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
    )
    op.create_index(
        "ix_knowledge_packs_project_id",
        "knowledge_packs",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_packs_status",
        "knowledge_packs",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_packs_created_by",
        "knowledge_packs",
        ["created_by"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_packs_name",
        "knowledge_packs",
        ["name"],
        unique=False,
    )

    op.create_table(
        "knowledge_pack_sections",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("knowledge_pack_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("section_key", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column(
            "content",
            sa.Text(),
            server_default=sa.text("''"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
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
            ["knowledge_pack_id"],
            ["knowledge_packs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "knowledge_pack_id",
            "section_key",
            name="uq_knowledge_pack_sections_pack_key",
        ),
    )
    op.create_index(
        "ix_knowledge_pack_sections_pack_id",
        "knowledge_pack_sections",
        ["knowledge_pack_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_pack_sections_section_key",
        "knowledge_pack_sections",
        ["section_key"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_pack_sections_position",
        "knowledge_pack_sections",
        ["knowledge_pack_id", "position"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_knowledge_pack_sections_position",
        table_name="knowledge_pack_sections",
    )
    op.drop_index(
        "ix_knowledge_pack_sections_section_key",
        table_name="knowledge_pack_sections",
    )
    op.drop_index(
        "ix_knowledge_pack_sections_pack_id",
        table_name="knowledge_pack_sections",
    )
    op.drop_table("knowledge_pack_sections")

    op.drop_index("ix_knowledge_packs_name", table_name="knowledge_packs")
    op.drop_index("ix_knowledge_packs_created_by", table_name="knowledge_packs")
    op.drop_index("ix_knowledge_packs_status", table_name="knowledge_packs")
    op.drop_index("ix_knowledge_packs_project_id", table_name="knowledge_packs")
    op.drop_table("knowledge_packs")
