"""add_script_quality_review_idempotency

Revision ID: b4e59a27c8d1
Revises: a3d48f16b7c0
Create Date: 2026-08-02 14:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b4e59a27c8d1"
down_revision: Union[str, Sequence[str], None] = "a3d48f16b7c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_ai_jobs_script_purpose_idempotency",
        "ai_jobs",
        ["requested_by", "script_id", "purpose", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text(
            "idempotency_key IS NOT NULL AND script_id IS NOT NULL "
            "AND purpose IS NOT NULL"
        ),
    )


def downgrade() -> None:
    op.drop_index("uq_ai_jobs_script_purpose_idempotency", table_name="ai_jobs")
