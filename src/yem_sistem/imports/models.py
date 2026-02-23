"""Import tracking models for external file integrations."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from yem_sistem.db.base import Base


class ImportStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ImportJob(Base):
    """Tracks ingestion jobs and their processing outcomes."""

    __tablename__ = "imports"
    __table_args__ = (
        UniqueConstraint("source_name", "file_hash", name="uq_imports_source_hash"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(String(120), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[ImportStatus] = mapped_column(Enum(ImportStatus, name="import_status"), nullable=False, default=ImportStatus.PENDING)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
