"""ContentWorkflow ORM model — orchestration only, not a content source of truth."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.workflows.constants import DEFAULT_WORKFLOW_STAGE, DEFAULT_WORKFLOW_STATUS

if TYPE_CHECKING:
    from app.models.content_version import ContentVersion
    from app.models.script import Script


class ContentWorkflow(Base):
    """Lifecycle coordinator for a Script workspace.

    Does not store document content. Coordinates ScriptDocuments → ContentVersion
    → Approval.
    """

    __tablename__ = "content_workflows"
    __table_args__ = (
        UniqueConstraint("script_id", name="uq_content_workflows_script_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    script_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scripts.id", ondelete="CASCADE"),
        nullable=False,
    )
    current_stage: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=DEFAULT_WORKFLOW_STAGE,
        server_default=text(f"'{DEFAULT_WORKFLOW_STAGE}'"),
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=DEFAULT_WORKFLOW_STATUS,
        server_default=text(f"'{DEFAULT_WORKFLOW_STATUS}'"),
    )
    active_content_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    script: Mapped[Script] = relationship()
    active_content_version: Mapped[ContentVersion | None] = relationship(
        foreign_keys=[active_content_version_id]
    )
