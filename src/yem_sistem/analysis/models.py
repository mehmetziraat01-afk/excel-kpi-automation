"""Raw material analysis result models."""

from __future__ import annotations

import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from yem_sistem.db.base import Base


class AnalysisType(str, enum.Enum):
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"


class YabanciMadde(str, enum.Enum):
    VAR = "VAR"
    YOK = "YOK"


class Tozluluk(str, enum.Enum):
    AZ = "AZ"
    COK = "COK"


class MaterialAnalysisResult(Base):
    __tablename__ = "material_analysis_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    acceptance_id: Mapped[int | None] = mapped_column(ForeignKey("acceptance.id", ondelete="SET NULL"), nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False)
    plate: Mapped[str | None] = mapped_column(String(30), nullable=True)
    company: Mapped[str | None] = mapped_column(String(150), nullable=True)
    analysis_type: Mapped[AnalysisType] = mapped_column(Enum(AnalysisType, name="analysis_type"), nullable=False)
    entered_by_role: Mapped[str] = mapped_column(String(30), nullable=False)
    entered_by_user: Mapped[str | None] = mapped_column(String(120), nullable=True)
    entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    yabanci_madde: Mapped[YabanciMadde | None] = mapped_column(Enum(YabanciMadde, name="yabanci_madde"), nullable=True)
    tozluluk: Mapped[Tozluluk | None] = mapped_column(Enum(Tozluluk, name="tozluluk"), nullable=True)
    aciklama: Mapped[str | None] = mapped_column(Text, nullable=True)
    kontrol_eden: Mapped[str | None] = mapped_column(String(120), nullable=True)

    sartoris_nem: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    hektometre: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    aflatoksin_ppb: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    zearalenone: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)

    dry_matter_percent: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    crude_protein_percent: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    starch_percent: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    ndf_percent: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    adf_percent: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    ash_percent: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    fat_percent: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    other_myco: Mapped[str | None] = mapped_column(Text, nullable=True)
    lab_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    report_no: Mapped[str | None] = mapped_column(String(80), nullable=True)
    sample_no: Mapped[str | None] = mapped_column(String(80), nullable=True)
