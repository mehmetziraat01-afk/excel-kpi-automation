"""DTM production batch models."""

from __future__ import annotations

import enum
from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, Enum, Integer, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from yem_sistem.db.base import Base


class BatchStatus(str, enum.Enum):
    """Operational lifecycle status for a production batch."""

    OK = "OK"
    SUSPICIOUS = "SUSPICIOUS"
    FIXED = "FIXED"


class ProductionBatch(Base):
    """Represents a DTM production event."""

    __tablename__ = "production_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_batch: Mapped[str] = mapped_column(String(80), nullable=False)
    batch_name: Mapped[str] = mapped_column(String(150), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    feeder: Mapped[str | None] = mapped_column(String(120), nullable=True)
    recipe_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    recipe_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    status: Mapped[BatchStatus] = mapped_column(Enum(BatchStatus, name="batch_status"), nullable=False, default=BatchStatus.OK)
    suspicious_count_zero: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    suspicious_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    items = relationship("BatchItem", back_populates="production_batch", cascade="all, delete-orphan")
