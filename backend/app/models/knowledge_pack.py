"""Knowledge Pack and section ORM models."""

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
from app.knowledge_packs.constants import DEFAULT_KNOWLEDGE_PACK_STATUS

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class KnowledgePack(Base):
    """Structured research/context layer for a project.

    ``created_by`` is the creator. There is no separate owner column — project
    membership and global RBAC remain the authorization sources.
    """

    __tablename__ = "knowledge_packs"

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
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=DEFAULT_KNOWLEDGE_PACK_STATUS,
        server_default=text(f"'{DEFAULT_KNOWLEDGE_PACK_STATUS}'"),
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
    creator: Mapped[User] = relationship(foreign_keys=[created_by])
    sections: Mapped[list[KnowledgePackSection]] = relationship(
        back_populates="knowledge_pack",
        cascade="all, delete-orphan",
        order_by="KnowledgePackSection.position",
    )


class KnowledgePackSection(Base):
    """One semantic section row within a Knowledge Pack."""

    __tablename__ = "knowledge_pack_sections"
    __table_args__ = (
        UniqueConstraint(
            "knowledge_pack_id",
            "section_key",
            name="uq_knowledge_pack_sections_pack_key",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    knowledge_pack_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_packs.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_key: Mapped[str] = mapped_column(String(64), nullable=False)
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

    knowledge_pack: Mapped[KnowledgePack] = relationship(back_populates="sections")
