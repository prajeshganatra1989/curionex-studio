"""add_script_workspace_tables

Revision ID: b8f26c51a3e5
Revises: a7e15b40f2d4
Create Date: 2026-08-02 00:50:00.000000

Script workspace foundation for M2H: scripts and script_documents.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b8f26c51a3e5"
down_revision: Union[str, Sequence[str], None] = "a7e15b40f2d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scripts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("knowledge_pack_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("script_code", sa.String(length=48), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=sa.text("'draft'"),
            nullable=False,
        ),
        sa.Column("content_version_id", postgresql.UUID(as_uuid=True), nullable=True),
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
            ["knowledge_pack_id"],
            ["knowledge_packs.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["content_version_id"],
            ["content_versions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("script_code", name="uq_scripts_script_code"),
    )
    op.create_index("ix_scripts_project_id", "scripts", ["project_id"], unique=False)
    op.create_index("ix_scripts_status", "scripts", ["status"], unique=False)
    op.create_index(
        "ix_scripts_knowledge_pack_id",
        "scripts",
        ["knowledge_pack_id"],
        unique=False,
    )
    op.create_index("ix_scripts_created_by", "scripts", ["created_by"], unique=False)
    op.create_index("ix_scripts_title", "scripts", ["title"], unique=False)
    op.create_index(
        "ix_scripts_content_version_id",
        "scripts",
        ["content_version_id"],
        unique=False,
    )

    op.create_table(
        "script_documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("script_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_type", sa.String(length=64), nullable=False),
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
            ["script_id"],
            ["scripts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "script_id",
            "document_type",
            name="uq_script_documents_script_type",
        ),
    )
    op.create_index(
        "ix_script_documents_script_id",
        "script_documents",
        ["script_id"],
        unique=False,
    )
    op.create_index(
        "ix_script_documents_document_type",
        "script_documents",
        ["document_type"],
        unique=False,
    )
    op.create_index(
        "ix_script_documents_position",
        "script_documents",
        ["script_id", "position"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_script_documents_position", table_name="script_documents")
    op.drop_index("ix_script_documents_document_type", table_name="script_documents")
    op.drop_index("ix_script_documents_script_id", table_name="script_documents")
    op.drop_table("script_documents")

    op.drop_index("ix_scripts_content_version_id", table_name="scripts")
    op.drop_index("ix_scripts_title", table_name="scripts")
    op.drop_index("ix_scripts_created_by", table_name="scripts")
    op.drop_index("ix_scripts_knowledge_pack_id", table_name="scripts")
    op.drop_index("ix_scripts_status", table_name="scripts")
    op.drop_index("ix_scripts_project_id", table_name="scripts")
    op.drop_table("scripts")
