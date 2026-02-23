"""Analysis UI routes."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from yem_sistem.analysis.models import AnalysisType, Tozluluk, YabanciMadde
from yem_sistem.analysis.service import (
    AnalysisAuthorizationError,
    AnalysisService,
    AnalysisValidationError,
    ExternalAnalysisInput,
)
from yem_sistem.db.session import get_session

router = APIRouter(tags=["analysis"])
templates = Jinja2Templates(directory="src/yem_sistem/web/templates")


@router.get("/analysis/external/new", response_class=HTMLResponse)
def external_analysis_new(
    request: Request,
    acceptance_id: int | None = Query(default=None),
    x_role: str = Header(default="", alias="X-Role"),
) -> HTMLResponse:
    if (x_role or "").upper() != "ADMIN":
        raise HTTPException(status_code=403, detail="Only ADMIN can access external analysis entry")
    return templates.TemplateResponse(
        request=request,
        name="analysis_external_new.html",
        context={"acceptance_id": acceptance_id},
    )


@router.post("/analysis/external")
def create_external_analysis(
    acceptance_id: int = Form(...),
    dry_matter_percent: str | None = Form(default=None),
    crude_protein_percent: str | None = Form(default=None),
    starch_percent: str | None = Form(default=None),
    ndf_percent: str | None = Form(default=None),
    adf_percent: str | None = Form(default=None),
    ash_percent: str | None = Form(default=None),
    fat_percent: str | None = Form(default=None),
    aflatoksin_ppb: str | None = Form(default=None),
    zearalenone: str | None = Form(default=None),
    other_myco: str | None = Form(default=None),
    lab_name: str | None = Form(default=None),
    report_no: str | None = Form(default=None),
    sample_no: str | None = Form(default=None),
    yabanci_madde: str | None = Form(default=None),
    tozluluk: str | None = Form(default=None),
    kontrol_eden: str | None = Form(default=None),
    aciklama: str | None = Form(default=None),
    x_role: str = Header(default="", alias="X-Role"),
    session: Session = Depends(get_session),
) -> dict:
    svc = AnalysisService(session)
    try:
        row = svc.create_external(
            ExternalAnalysisInput(
                acceptance_id=acceptance_id,
                entered_by_role=x_role,
                dry_matter_percent=_opt_decimal(dry_matter_percent),
                crude_protein_percent=_opt_decimal(crude_protein_percent),
                starch_percent=_opt_decimal(starch_percent),
                ndf_percent=_opt_decimal(ndf_percent),
                adf_percent=_opt_decimal(adf_percent),
                ash_percent=_opt_decimal(ash_percent),
                fat_percent=_opt_decimal(fat_percent),
                aflatoksin_ppb=_opt_decimal(aflatoksin_ppb),
                zearalenone=_opt_decimal(zearalenone),
                other_myco=other_myco,
                lab_name=lab_name,
                report_no=report_no,
                sample_no=sample_no,
                yabanci_madde=YabanciMadde(yabanci_madde) if yabanci_madde else None,
                tozluluk=Tozluluk(tozluluk) if tozluluk else None,
                kontrol_eden=kontrol_eden,
                aciklama=aciklama,
            )
        )
    except (AnalysisAuthorizationError, AnalysisValidationError) as exc:
        raise HTTPException(status_code=400 if isinstance(exc, AnalysisValidationError) else 403, detail=str(exc)) from exc

    return {"status": "created", "id": row.id}


@router.get("/analysis", response_class=HTMLResponse)
def analysis_list(
    request: Request,
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    material_id: int | None = Query(default=None),
    analysis_type: str | None = Query(default=None),
    aflatoksin_min: str | None = Query(default=None),
    yabanci_madde: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> HTMLResponse:
    svc = AnalysisService(session)

    rows = svc.list_filtered(
        date_from=date.fromisoformat(date_from) if date_from else None,
        date_to=date.fromisoformat(date_to) if date_to else None,
        material_id=material_id,
        analysis_type=AnalysisType(analysis_type) if analysis_type else None,
        aflatoksin_min=_opt_decimal(aflatoksin_min),
        yabanci_madde=YabanciMadde(yabanci_madde) if yabanci_madde else None,
    )

    return templates.TemplateResponse(
        request=request,
        name="analysis_list.html",
        context={
            "rows": rows,
            "date_from": date_from or "",
            "date_to": date_to or "",
            "material_id": material_id or "",
            "analysis_type": analysis_type or "",
            "aflatoksin_min": aflatoksin_min or "",
            "yabanci_madde": yabanci_madde or "",
        },
    )


def _opt_decimal(v: str | None) -> Decimal | None:
    if v is None or str(v).strip() == "":
        return None
    return Decimal(str(v))
