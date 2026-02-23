"""Acceptance HTTP routes."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from yem_sistem.acceptance.service import (
    AcceptanceAuthorizationError,
    AcceptanceCreateInput,
    AcceptanceService,
    AcceptanceValidationError,
    parse_datetime,
)
from yem_sistem.analysis.models import Tozluluk, YabanciMadde
from yem_sistem.analysis.service import InternalAnalysisInput
from yem_sistem.db.session import get_session

router = APIRouter(tags=["acceptance"])
templates = Jinja2Templates(directory="src/yem_sistem/web/templates")


@router.post("/acceptance")
def create_acceptance(
    date: str = Form(...),
    plate: str = Form(...),
    material_id: int = Form(...),
    quantity: str = Form(...),
    company: str | None = Form(default=None),
    note: str | None = Form(default=None),
    yabanci_madde: str | None = Form(default=None),
    tozluluk: str | None = Form(default=None),
    aciklama: str | None = Form(default=None),
    kontrol_eden: str | None = Form(default=None),
    sartoris_nem: str | None = Form(default=None),
    hektometre: str | None = Form(default=None),
    aflatoksin_ppb: str | None = Form(default=None),
    zearalenone: str | None = Form(default=None),
    x_role: str = Header(default="", alias="X-Role"),
    session: Session = Depends(get_session),
) -> dict:
    service = AcceptanceService(session)
    try:
        internal = InternalAnalysisInput(
            acceptance_id=0,
            entered_by_role=x_role,
            yabanci_madde=YabanciMadde(yabanci_madde) if yabanci_madde else None,
            tozluluk=Tozluluk(tozluluk) if tozluluk else None,
            aciklama=aciklama,
            kontrol_eden=kontrol_eden,
            sartoris_nem=_opt_decimal(sartoris_nem),
            hektometre=_opt_decimal(hektometre),
            aflatoksin_ppb=_opt_decimal(aflatoksin_ppb),
            zearalenone=_opt_decimal(zearalenone),
        )
        acceptance = service.create(
            AcceptanceCreateInput(
                accepted_at=parse_datetime(date),
                company=company,
                plate=plate,
                material_id=material_id,
                quantity=Decimal(quantity),
                note=note,
            ),
            actor_role=x_role,
            internal_analysis=internal,
        )
    except AcceptanceAuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except AcceptanceValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"id": acceptance.id, "status": "created"}


@router.get("/acceptance/new", response_class=HTMLResponse)
def acceptance_new_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="acceptance_new.html", context={})


@router.get("/acceptance", response_class=HTMLResponse)
def acceptance_list(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    service = AcceptanceService(session)
    rows = service.list_latest(limit=50)
    return templates.TemplateResponse(
        request=request,
        name="acceptance_list.html",
        context={"rows": rows},
    )


def _opt_decimal(v: str | None) -> Decimal | None:
    if v is None or str(v).strip() == "":
        return None
    return Decimal(str(v))
