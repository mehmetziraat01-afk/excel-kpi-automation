"""Suspicious production batch UI/API routes."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from yem_sistem.db.session import get_session
from yem_sistem.production_batches.service import (
    BatchFixAuthorizationError,
    BatchFixValidationError,
    ProductionBatchService,
)

router = APIRouter(tags=["batches"])
templates = Jinja2Templates(directory="src/yem_sistem/web/templates")


@router.get("/batches/suspicious", response_class=HTMLResponse)
def suspicious_batches_page(
    request: Request,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    service = ProductionBatchService(session)
    batches = service.list_suspicious_batches(limit=100)
    return templates.TemplateResponse(
        request=request,
        name="suspicious_batches.html",
        context={"batches": batches},
    )


@router.get("/batches/{batch_id}/fix", response_class=HTMLResponse)
def fix_batch_page(
    request: Request,
    batch_id: int,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    service = ProductionBatchService(session)
    try:
        batch, items = service.get_zero_loaded_items(batch_id)
    except BatchFixValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return templates.TemplateResponse(
        request=request,
        name="batch_fix.html",
        context={"batch": batch, "items": items},
    )


@router.post("/batches/{batch_id}/fix-item")
def fix_batch_item(
    batch_id: int,
    batch_item_id: int = Form(...),
    corrected_weight: str = Form(...),
    correction_note: str = Form(...),
    x_role: str = Header(default="", alias="X-Role"),
    session: Session = Depends(get_session),
) -> dict:
    service = ProductionBatchService(session)
    try:
        item = service.fix_item(
            batch_id=batch_id,
            batch_item_id=batch_item_id,
            corrected_weight=Decimal(corrected_weight),
            correction_note=correction_note,
            actor_role=x_role,
        )
        return {"status": "fixed", "batch_item_id": item.id}
    except BatchFixAuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except BatchFixValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
