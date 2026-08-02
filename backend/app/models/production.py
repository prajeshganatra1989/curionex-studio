"""Production Mode settings model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProductionSettings(Base):
    """Singleton-style production goals (one row expected)."""

    __tablename__ = "production_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    approved_script_target: Mapped[int] = mapped_column(
        Integer, nullable=False, default=120, server_default=text("120")
    )
    daily_approved_script_target: Mapped[int] = mapped_column(
        Integer, nullable=False, default=2, server_default=text("2")
    )
    weekly_approved_script_target: Mapped[int] = mapped_column(
        Integer, nullable=False, default=14, server_default=text("14")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
