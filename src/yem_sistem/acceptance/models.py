"""Acceptance (material IN) domain models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from yem_sistem.db.base import Base
from yem_sistem.db.types import QUANTITY_TYPE


class Acceptance(Base):
    """Material acceptance records that produce IN stock movements."""

    __tablename__ = "acceptance"
    __table_args__ = (
        UniqueConstraint(
            "accepted_at",
            "plate",
            "material_id",
            "quantity",
            name="uq_acceptance_duplicate",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    company: Mapped[str | None] = mapped_column(String(150), nullable=True)
    plate: Mapped[str] = mapped_column(String(30), nullable=False)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(QUANTITY_TYPE, nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
