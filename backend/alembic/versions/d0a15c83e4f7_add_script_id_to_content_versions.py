"""add_script_id_to_content_versions

Revision ID: d0a15c83e4f7
Revises: c9g37d62b4f6
Create Date: 2026-08-02 11:30:00.000000

Adds nullable script_id FK on content_versions for script-scoped versioning.
Existing rows remain script_id = NULL (no title-prefix backfill).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d0a15c83e4f7"
down_revision: Union[str, Sequence[str], None] = "c9g37d62b4f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "content_versions",
        sa.Column("script_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_content_versions_script_id_scripts",
        "content_versions",
        "scripts",
        ["script_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_content_versions_script_id",
        "content_versions",
        ["script_id"],
        unique=False,
    )
    op.create_index(
        "ix_content_versions_script_version",
        "content_versions",
        ["script_id", "version_number"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_content_versions_script_version", table_name="content_versions")
    op.drop_index("ix_content_versions_script_id", table_name="content_versions")
    op.drop_constraint(
        "fk_content_versions_script_id_scripts",
        "content_versions",
        type_="foreignkey",
    )
    op.drop_column("content_versions", "script_id")
