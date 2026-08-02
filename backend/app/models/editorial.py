"""Editorial topic ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.editorial.constants import (
    DEFAULT_PRODUCTION_WAVE,
    DEFAULT_TOPIC_DIFFICULTY,
    DEFAULT_TOPIC_PRIORITY,
    DEFAULT_TOPIC_STATUS,
    DEFAULT_TOPIC_VIRAL,
)

if TYPE_CHECKING:
    from app.models.project import Project


class EditorialTopic(Base):
    """Evergreen YouTube Shorts idea in the Editorial Library."""

    __tablename__ = "editorial_topics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    slug: Mapped[str] = mapped_column(String(180), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=DEFAULT_TOPIC_STATUS,
        server_default=text(f"'{DEFAULT_TOPIC_STATUS}'"),
        index=True,
    )
    difficulty: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=DEFAULT_TOPIC_DIFFICULTY,
        server_default=text(f"'{DEFAULT_TOPIC_DIFFICULTY}'"),
        index=True,
    )
    evergreen_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=70,
        server_default=text("70"),
    )
    curiosity_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=70,
        server_default=text("70"),
    )
    viral_potential: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=DEFAULT_TOPIC_VIRAL,
        server_default=text(f"'{DEFAULT_TOPIC_VIRAL}'"),
    )
    estimated_duration_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=45,
        server_default=text("45"),
    )
    target_audience: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    linked_project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    published_video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    priority: Mapped[str] = mapped_column(
        String(1),
        nullable=False,
        default=DEFAULT_TOPIC_PRIORITY,
        server_default=text(f"'{DEFAULT_TOPIC_PRIORITY}'"),
        index=True,
    )
    production_wave: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=DEFAULT_PRODUCTION_WAVE,
        server_default=text(str(DEFAULT_PRODUCTION_WAVE)),
        index=True,
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

    linked_project: Mapped[Project | None] = relationship(
        "Project",
        foreign_keys=[linked_project_id],
    )
