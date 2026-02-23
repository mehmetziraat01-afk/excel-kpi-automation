"""Services for suspicious production batch fixing flow."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from yem_sistem.audit_logs.models import AuditLog
from yem_sistem.batch_items.models import BatchItem
from yem_sistem.production_batches.models import BatchStatus, ProductionBatch
from yem_sistem.stock_movements.models import MovementReason, MovementType, StockMovement
from yem_sistem.stock_movements.service import NegativeStockError, StockService


class BatchFixValidationError(ValueError):
    """Raised when fix input violates business rules."""


class BatchFixAuthorizationError(PermissionError):
    """Raised when actor role is not allowed to fix suspicious batches."""


class ProductionBatchService:
    """Application service for suspicious batch listing and correction."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.stock_service = StockService(session)

    def list_suspicious_batches(self, limit: int = 100) -> list[ProductionBatch]:
        stmt = (
            select(ProductionBatch)
            .where(ProductionBatch.status == BatchStatus.SUSPICIOUS)
            .order_by(ProductionBatch.date.desc(), ProductionBatch.id.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def get_zero_loaded_items(self, batch_id: int) -> tuple[ProductionBatch, list[BatchItem]]:
        batch = self.session.get(ProductionBatch, batch_id)
        if batch is None:
            raise BatchFixValidationError("Batch not found")

        items_stmt = select(BatchItem).where(
            BatchItem.production_batch_id == batch_id,
            BatchItem.is_zero_loaded.is_(True),
        )
        items = list(self.session.scalars(items_stmt).all())
        return batch, items

    def fix_item(
        self,
        *,
        batch_id: int,
        batch_item_id: int,
        corrected_weight: Decimal,
        correction_note: str,
        actor_role: str,
    ) -> BatchItem:
        role = (actor_role or "").upper()
        if role != "ADMIN":
            raise BatchFixAuthorizationError("Only ADMIN can fix suspicious batches.")

        note = (correction_note or "").strip()
        if len(note) < 15:
            raise BatchFixValidationError("correction_note is required and must be at least 15 characters")
        if corrected_weight <= Decimal("0.000"):
            raise BatchFixValidationError("corrected_weight must be greater than 0")

        batch = self.session.get(ProductionBatch, batch_id)
        if batch is None:
            raise BatchFixValidationError("Batch not found")

        item = self.session.get(BatchItem, batch_item_id)
        if item is None or item.production_batch_id != batch_id:
            raise BatchFixValidationError("Batch item not found in given batch")
        if not item.is_zero_loaded:
            raise BatchFixValidationError("Only zero-loaded items can be fixed")

        movement = StockMovement(
            material_id=item.material_id,
            movement_type=MovementType.OUT_CORRECTION,
            reason=MovementReason.ADJUSTMENT,
            quantity=corrected_weight,
            movement_at=batch.created_at,
            reference_type="DTM_BATCH_FIX",
            reference_id=batch.id,
            note=note,
        )

        try:
            self.stock_service.add_movement(movement)
        except NegativeStockError as exc:
            raise BatchFixValidationError(str(exc)) from exc

        item.corrected_weight = corrected_weight
        item.correction_note = note
        item.corrected_by_user_id = 0
        from datetime import datetime, timezone

        item.corrected_at = datetime.now(timezone.utc)

        self.session.add(
            AuditLog(
                entity_name="batch_item_fix",
                entity_id=str(item.id),
                action="FIX",
                actor=role,
                payload=(
                    f"batch_id={batch.id} batch_item_id={item.id} material_id={item.material_id} "
                    f"corrected_weight={corrected_weight} note={note}"
                ),
            )
        )

        remaining_zero_unfixed_stmt = select(BatchItem.id).where(
            BatchItem.production_batch_id == batch_id,
            BatchItem.is_zero_loaded.is_(True),
            BatchItem.corrected_weight.is_(None),
        )
        remaining = self.session.execute(remaining_zero_unfixed_stmt).first()
        if remaining is None:
            batch.status = BatchStatus.FIXED

        self.session.commit()
        return item
