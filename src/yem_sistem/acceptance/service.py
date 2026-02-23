"""Acceptance application service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from yem_sistem.acceptance.models import Acceptance
from yem_sistem.analysis.service import AnalysisService, InternalAnalysisInput
from yem_sistem.audit_logs.models import AuditLog
from yem_sistem.stock_movements.models import MovementReason, MovementType, StockMovement
from yem_sistem.stock_movements.service import StockService


class AcceptanceValidationError(ValueError):
    """Raised when acceptance input violates business rules."""


class AcceptanceAuthorizationError(PermissionError):
    """Raised when actor role is not allowed to create acceptance."""


@dataclass(slots=True)
class AcceptanceCreateInput:
    accepted_at: datetime
    plate: str
    material_id: int
    quantity: Decimal
    company: str | None = None
    note: str | None = None


class AcceptanceService:
    ALLOWED_CREATE_ROLES = {"ACCEPTANCE", "ADMIN"}

    def __init__(self, session: Session) -> None:
        self.session = session
        self.stock_service = StockService(session)
        self.analysis_service = AnalysisService(session)

    def create(self, payload: AcceptanceCreateInput, actor_role: str, internal_analysis: InternalAnalysisInput | None = None) -> Acceptance:
        role = (actor_role or "").upper()
        if role not in self.ALLOWED_CREATE_ROLES:
            raise AcceptanceAuthorizationError("Only ACCEPTANCE and ADMIN can create acceptance.")

        if payload.quantity <= Decimal("0.000"):
            raise AcceptanceValidationError("quantity must be greater than 0")

        duplicate_stmt = select(Acceptance.id).where(
            Acceptance.accepted_at == payload.accepted_at,
            Acceptance.plate == payload.plate,
            Acceptance.material_id == payload.material_id,
            Acceptance.quantity == payload.quantity,
        )
        if self.session.execute(duplicate_stmt).first() is not None:
            raise AcceptanceValidationError("duplicate acceptance detected")

        acceptance = Acceptance(
            accepted_at=payload.accepted_at,
            company=payload.company,
            plate=payload.plate,
            material_id=payload.material_id,
            quantity=payload.quantity,
            note=payload.note,
        )

        movement = StockMovement(
            material_id=payload.material_id,
            movement_type=MovementType.IN,
            reason=MovementReason.MATERIAL_ACCEPTANCE,
            quantity=payload.quantity,
            movement_at=payload.accepted_at,
            reference_type="acceptance",
            note=payload.note,
        )

        self.session.add(acceptance)
        self.session.flush()

        movement.reference_id = acceptance.id
        self.stock_service.add_movement(movement)

        if internal_analysis is not None:
            internal_analysis.acceptance_id = acceptance.id
            internal_analysis.entered_by_role = role
            if self.analysis_service.has_any_internal_data(internal_analysis):
                self.analysis_service.create_internal(internal_analysis)

        self.session.add(
            AuditLog(
                entity_name="acceptance",
                entity_id=str(acceptance.id),
                action="INSERT",
                actor=role,
                payload=(
                    f"accepted_at={payload.accepted_at.isoformat()} plate={payload.plate} "
                    f"material_id={payload.material_id} quantity={payload.quantity}"
                ),
            )
        )
        self.session.commit()
        return acceptance

    def list_latest(self, limit: int = 50) -> list[Acceptance]:
        stmt = select(Acceptance).order_by(desc(Acceptance.accepted_at), desc(Acceptance.id)).limit(limit)
        return list(self.session.scalars(stmt).all())


def parse_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
