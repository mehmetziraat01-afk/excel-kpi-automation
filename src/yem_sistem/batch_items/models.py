"""Production batch material consumption line models."""

from __future__ import annotations

from datetime import datetime, time
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from yem_sistem.db.base import Base
from yem_sistem.db.types import ERROR_PERCENT_TYPE, QUANTITY_TYPE


class BatchItem(Base):
    """Material quantities consumed in a production batch."""

    __tablename__ = "batch_items"
    __table_args__ = (
        UniqueConstraint("id_batch", "material_id", "start_time", name="uq_batch_items_idbatch_material_start"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    production_batch_id: Mapped[int] = mapped_column(ForeignKey("production_batches.id", ondelete="CASCADE"), nullable=False)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False)

    id_batch: Mapped[str] = mapped_column(String(80), nullable=False)
    start_time: Mapped[time | None] = mapped_column(nullable=True)

    target_weight: Mapped[Decimal] = mapped_column(QUANTITY_TYPE, nullable=False)
    loaded_weight: Mapped[Decimal] = mapped_column(QUANTITY_TYPE, nullable=False)
    error_percent: Mapped[Decimal | None] = mapped_column(ERROR_PERCENT_TYPE, nullable=True)
    is_zero_loaded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    corrected_weight: Mapped[Decimal | None] = mapped_column(QUANTITY_TYPE, nullable=True)
    correction_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_by_user_id: Mapped[int | None] = mapped_column(nullable=True)
    corrected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    production_batch = relationship("ProductionBatch", back_populates="items")
    material = relationship("Material", back_populates="batch_items")
