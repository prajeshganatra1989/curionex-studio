"""Content Standard ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.editorial.content_standard_constants import (
    CONTENT_STANDARD_STATUS_DRAFT,
)


class ContentStandard(Base):
    """Versioned Curionex editorial source of truth."""

    __tablename__ = "content_standards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=CONTENT_STANDARD_STATUS_DRAFT,
        server_default=text(f"'{CONTENT_STANDARD_STATUS_DRAFT}'"),
        index=True,
    )
    mission: Mapped[str] = mapped_column(Text, nullable=False)
    target_audience: Mapped[str] = mapped_column(Text, nullable=False)
    brand_voice: Mapped[str] = mapped_column(Text, nullable=False)
    editorial_principles: Mapped[str] = mapped_column(Text, nullable=False)
    hook_rules: Mapped[str] = mapped_column(Text, nullable=False)
    story_structure: Mapped[str] = mapped_column(Text, nullable=False)
    fact_policy: Mapped[str] = mapped_column(Text, nullable=False)
    citation_policy: Mapped[str] = mapped_column(Text, nullable=False)
    tone_guidelines: Mapped[str] = mapped_column(Text, nullable=False)
    language_rules: Mapped[str] = mapped_column(Text, nullable=False)
    forbidden_patterns: Mapped[str] = mapped_column(Text, nullable=False)
    approved_cta_patterns: Mapped[str] = mapped_column(Text, nullable=False)
    quality_checklist: Mapped[str] = mapped_column(Text, nullable=False)
    default_duration_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60, server_default=text("60")
    )
    default_target_words: Mapped[int] = mapped_column(
        Integer, nullable=False, default=160, server_default=text("160")
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
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
