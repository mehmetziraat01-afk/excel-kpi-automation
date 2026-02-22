"""Monthly pricing records for accounting exports."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from yem_sistem.db.base import Base
from yem_sistem.db.types import PRICE_TYPE


class MonthlyPrice(Base):
    """Defines month-based unit price for each material."""

    __tablename__ = "monthly_prices"
    __table_args__ = (UniqueConstraint("material_id", "price_month", name="uq_monthly_prices_material_month"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False)
    price_month: Mapped[date] = mapped_column(Date, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(PRICE_TYPE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    material = relationship("Material", back_populates="monthly_prices")
