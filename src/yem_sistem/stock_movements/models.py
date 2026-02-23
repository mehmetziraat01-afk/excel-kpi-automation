"""Inventory movement models (IN/OUT)."""

from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from yem_sistem.db.base import Base
from yem_sistem.db.types import QUANTITY_TYPE


class MovementType(str, enum.Enum):
    """Physical direction/category of stock movement."""

    IN = "IN"
    OUT_PRODUCTION = "OUT_PRODUCTION"
    OUT_CORRECTION = "OUT_CORRECTION"
    ADJUSTMENT = "ADJUSTMENT"


class MovementReason(str, enum.Enum):
    """Business reasons for inventory transactions."""

    MATERIAL_ACCEPTANCE = "MATERIAL_ACCEPTANCE"  # IN
    DTM_CONSUMPTION = "DTM_CONSUMPTION"  # OUT_PRODUCTION
    ADJUSTMENT = "ADJUSTMENT"


class StockMovement(Base):
    """Tracks all inventory entries and exits for materials."""

    __tablename__ = "stock_movements"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_stock_movements_quantity_positive"),
        Index("ix_stock_movements_material_movement_at", "material_id", "movement_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False)
    movement_type: Mapped[MovementType] = mapped_column(Enum(MovementType, name="movement_type"), nullable=False)
    reason: Mapped[MovementReason] = mapped_column(
        Enum(MovementReason, name="movement_reason"),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(QUANTITY_TYPE, nullable=False)
    movement_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reference_type: Mapped[str] = mapped_column(String(30), nullable=False)
    reference_id: Mapped[int | None] = mapped_column(nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    material = relationship("Material", back_populates="stock_movements")
