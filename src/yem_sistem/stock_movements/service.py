"""Stock movement service with negative stock protection."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import Session

from yem_sistem.stock_movements.models import MovementType, StockMovement


class NegativeStockError(ValueError):
    """Raised when an OUT movement would cause stock to go below zero."""


class StockService:
    """Application service for stock movement operations."""

    OUT_TYPES = {MovementType.OUT_PRODUCTION, MovementType.OUT_CORRECTION}

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_current_stock(self, material_id: int) -> Decimal:
        """Calculate current stock from persisted IN/OUT movements."""
        incoming = case((StockMovement.movement_type == MovementType.IN, StockMovement.quantity), else_=Decimal("0.000"))
        outgoing = case((StockMovement.movement_type.in_(self.OUT_TYPES), StockMovement.quantity), else_=Decimal("0.000"))

        stmt: Select[tuple[Decimal | None]] = select(
            (func.coalesce(func.sum(incoming), Decimal("0.000")) - func.coalesce(func.sum(outgoing), Decimal("0.000")))
        ).where(StockMovement.material_id == material_id)

        result = self.session.execute(stmt).scalar_one()
        return Decimal(result)

    def add_movement(self, movement: StockMovement) -> StockMovement:
        """Persist movement after validating negative stock for OUT transactions."""
        if movement.movement_type in self.OUT_TYPES:
            current_stock = self.get_current_stock(movement.material_id)
            projected_stock = current_stock - movement.quantity
            if projected_stock < Decimal("0.000"):
                raise NegativeStockError(
                    f"Negative stock blocked for material_id={movement.material_id}: "
                    f"current={current_stock}, out={movement.quantity}, projected={projected_stock}"
                )

        self.session.add(movement)
        return movement
