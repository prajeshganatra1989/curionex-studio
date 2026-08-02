"""add editorial priority and production wave

Revision ID: e8b92d15f3a0
Revises: d7a81c04e2f9
Create Date: 2026-08-02 17:10:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e8b92d15f3a0"
down_revision: Union[str, Sequence[str], None] = "d7a81c04e2f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "editorial_topics",
        sa.Column(
            "priority",
            sa.String(length=1),
            nullable=False,
            server_default="B",
        ),
    )
    op.add_column(
        "editorial_topics",
        sa.Column(
            "production_wave",
            sa.Integer(),
            nullable=False,
            server_default="4",
        ),
    )
    op.create_index(
        "ix_editorial_topics_priority",
        "editorial_topics",
        ["priority"],
        unique=False,
    )
    op.create_index(
        "ix_editorial_topics_production_wave",
        "editorial_topics",
        ["production_wave"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_editorial_topics_production_wave", table_name="editorial_topics")
    op.drop_index("ix_editorial_topics_priority", table_name="editorial_topics")
    op.drop_column("editorial_topics", "production_wave")
    op.drop_column("editorial_topics", "priority")
