"""Analysis service and role checks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from yem_sistem.acceptance.models import Acceptance
from yem_sistem.analysis.models import AnalysisType, MaterialAnalysisResult, Tozluluk, YabanciMadde


class AnalysisValidationError(ValueError):
    pass


class AnalysisAuthorizationError(PermissionError):
    pass


@dataclass(slots=True)
class InternalAnalysisInput:
    acceptance_id: int
    entered_by_role: str
    entered_by_user: str | None = None
    yabanci_madde: YabanciMadde | None = None
    tozluluk: Tozluluk | None = None
    aciklama: str | None = None
    kontrol_eden: str | None = None
    sartoris_nem: Decimal | None = None
    hektometre: Decimal | None = None
    aflatoksin_ppb: Decimal | None = None
    zearalenone: Decimal | None = None


@dataclass(slots=True)
class ExternalAnalysisInput:
    acceptance_id: int
    entered_by_role: str
    entered_by_user: str | None = None
    yabanci_madde: YabanciMadde | None = None
    tozluluk: Tozluluk | None = None
    aciklama: str | None = None
    kontrol_eden: str | None = None
    aflatoksin_ppb: Decimal | None = None
    zearalenone: Decimal | None = None
    dry_matter_percent: Decimal | None = None
    crude_protein_percent: Decimal | None = None
    starch_percent: Decimal | None = None
    ndf_percent: Decimal | None = None
    adf_percent: Decimal | None = None
    ash_percent: Decimal | None = None
    fat_percent: Decimal | None = None
    other_myco: str | None = None
    lab_name: str | None = None
    report_no: str | None = None
    sample_no: str | None = None


class AnalysisService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_internal(self, payload: InternalAnalysisInput) -> MaterialAnalysisResult:
        role = (payload.entered_by_role or "").upper()
        if role not in {"ACCEPTANCE", "ADMIN"}:
            raise AnalysisAuthorizationError("Only ACCEPTANCE or ADMIN can enter INTERNAL analysis")

        acceptance = self.session.get(Acceptance, payload.acceptance_id)
        if acceptance is None:
            raise AnalysisValidationError("acceptance not found")

        row = MaterialAnalysisResult(
            acceptance_id=acceptance.id,
            date=acceptance.accepted_at.date(),
            material_id=acceptance.material_id,
            plate=acceptance.plate,
            company=acceptance.company,
            analysis_type=AnalysisType.INTERNAL,
            entered_by_role=role,
            entered_by_user=payload.entered_by_user,
            yabanci_madde=payload.yabanci_madde,
            tozluluk=payload.tozluluk,
            aciklama=payload.aciklama,
            kontrol_eden=payload.kontrol_eden,
            sartoris_nem=payload.sartoris_nem,
            hektometre=payload.hektometre,
            aflatoksin_ppb=payload.aflatoksin_ppb,
            zearalenone=payload.zearalenone,
        )
        self.session.add(row)
        return row

    def create_external(self, payload: ExternalAnalysisInput) -> MaterialAnalysisResult:
        role = (payload.entered_by_role or "").upper()
        if role != "ADMIN":
            raise AnalysisAuthorizationError("Only ADMIN can enter EXTERNAL analysis")

        acceptance = self.session.get(Acceptance, payload.acceptance_id)
        if acceptance is None:
            raise AnalysisValidationError("acceptance not found")

        row = MaterialAnalysisResult(
            acceptance_id=acceptance.id,
            date=acceptance.accepted_at.date(),
            material_id=acceptance.material_id,
            plate=acceptance.plate,
            company=acceptance.company,
            analysis_type=AnalysisType.EXTERNAL,
            entered_by_role=role,
            entered_by_user=payload.entered_by_user,
            yabanci_madde=payload.yabanci_madde,
            tozluluk=payload.tozluluk,
            aciklama=payload.aciklama,
            kontrol_eden=payload.kontrol_eden,
            aflatoksin_ppb=payload.aflatoksin_ppb,
            zearalenone=payload.zearalenone,
            dry_matter_percent=payload.dry_matter_percent,
            crude_protein_percent=payload.crude_protein_percent,
            starch_percent=payload.starch_percent,
            ndf_percent=payload.ndf_percent,
            adf_percent=payload.adf_percent,
            ash_percent=payload.ash_percent,
            fat_percent=payload.fat_percent,
            other_myco=payload.other_myco,
            lab_name=payload.lab_name,
            report_no=payload.report_no,
            sample_no=payload.sample_no,
        )
        self.session.add(row)
        self.session.commit()
        return row

    def list_filtered(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        material_id: int | None,
        analysis_type: AnalysisType | None,
        aflatoksin_min: Decimal | None,
        yabanci_madde: YabanciMadde | None,
    ) -> list[tuple[MaterialAnalysisResult, str]]:
        from yem_sistem.materials.models import Material

        stmt = select(MaterialAnalysisResult, Material.name).join(Material, Material.id == MaterialAnalysisResult.material_id)
        filters = []
        if date_from is not None:
            filters.append(MaterialAnalysisResult.date >= date_from)
        if date_to is not None:
            filters.append(MaterialAnalysisResult.date <= date_to)
        if material_id is not None:
            filters.append(MaterialAnalysisResult.material_id == material_id)
        if analysis_type is not None:
            filters.append(MaterialAnalysisResult.analysis_type == analysis_type)
        if aflatoksin_min is not None:
            filters.append(MaterialAnalysisResult.aflatoksin_ppb >= aflatoksin_min)
        if yabanci_madde is not None:
            filters.append(MaterialAnalysisResult.yabanci_madde == yabanci_madde)
        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(MaterialAnalysisResult.date.desc(), MaterialAnalysisResult.entered_at.desc()).limit(500)
        return list(self.session.execute(stmt).all())

    @staticmethod
    def has_any_internal_data(payload: InternalAnalysisInput) -> bool:
        return any(
            value not in (None, "")
            for value in [
                payload.yabanci_madde,
                payload.tozluluk,
                payload.aciklama,
                payload.kontrol_eden,
                payload.sartoris_nem,
                payload.hektometre,
                payload.aflatoksin_ppb,
                payload.zearalenone,
            ]
        )
