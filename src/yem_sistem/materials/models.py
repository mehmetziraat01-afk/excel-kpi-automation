"""Material master data models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from yem_sistem.db.base import Base
from yem_sistem.db.types import QUANTITY_TYPE


class Material(Base):
    """Raw material definition used across inventory and production."""

    __tablename__ = "materials"
    __table_args__ = (UniqueConstraint("code", name="uq_materials_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="kg")
    min_stock_level: Mapped[Decimal] = mapped_column(QUANTITY_TYPE, nullable=False, default=Decimal("0.000"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    stock_movements = relationship("StockMovement", back_populates="material")
    batch_items = relationship("BatchItem", back_populates="material")
    monthly_prices = relationship("MonthlyPrice", back_populates="material")
