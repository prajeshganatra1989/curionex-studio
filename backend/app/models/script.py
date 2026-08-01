"""Script and ScriptDocument ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.scripts.constants import DEFAULT_SCRIPT_STATUS

if TYPE_CHECKING:
    from app.models.content_version import ContentVersion
    from app.models.knowledge_pack import KnowledgePack
    from app.models.project import Project
    from app.models.user import User


class Script(Base):
    """Project script workspace container.

    Discovery Brief, Story Spine, and Master Script live in ``script_documents``.
    ``content_version_id`` is an optional pointer to the canonical ContentVersion
    layer (M2G) — not a second versioning system.
    """

    __tablename__ = "scripts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    knowledge_pack_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_packs.id", ondelete="SET NULL"),
        nullable=True,
    )
    script_code: Mapped[str] = mapped_column(String(48), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=DEFAULT_SCRIPT_STATUS,
        server_default=text(f"'{DEFAULT_SCRIPT_STATUS}'"),
    )
    content_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
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

    project: Mapped[Project] = relationship()
    knowledge_pack: Mapped[KnowledgePack | None] = relationship()
    content_version: Mapped[ContentVersion | None] = relationship()
    creator: Mapped[User] = relationship(foreign_keys=[created_by])
    documents: Mapped[list[ScriptDocument]] = relationship(
        back_populates="script",
        cascade="all, delete-orphan",
        order_by="ScriptDocument.position",
    )


class ScriptDocument(Base):
    """Editable workspace document (Discovery Brief / Story Spine / Master Script)."""

    __tablename__ = "script_documents"
    __table_args__ = (
        UniqueConstraint(
            "script_id",
            "document_type",
            name="uq_script_documents_script_type",
        ),
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
    document_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        server_default=text("''"),
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
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

    script: Mapped[Script] = relationship(back_populates="documents")
