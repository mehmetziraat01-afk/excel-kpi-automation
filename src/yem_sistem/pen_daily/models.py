"""Daily pen-level feeding records."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from yem_sistem.db.base import Base
from yem_sistem.db.types import QUANTITY_TYPE


class PenDaily(Base):
    """Daily consumption summary by pen and material."""

    __tablename__ = "pen_daily"
    __table_args__ = (UniqueConstraint("record_date", "pen_code", "material_id", name="uq_pen_daily_date_pen_material"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    pen_code: Mapped[str] = mapped_column(String(40), nullable=False)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False)
    consumed_quantity: Mapped[Decimal] = mapped_column(QUANTITY_TYPE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
