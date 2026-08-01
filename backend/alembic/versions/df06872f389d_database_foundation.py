"""Database foundation migration.

Revision ID: df06872f389d
Revises:
Create Date: 2026-08-01 20:56:33.787181

Establishes the Alembic revision chain. No application tables are created
in this milestone — business models arrive in later milestones.
"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "df06872f389d"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op: schema foundation only; tables arrive with future models."""


def downgrade() -> None:
    """No-op: nothing to reverse for the empty foundation revision."""
