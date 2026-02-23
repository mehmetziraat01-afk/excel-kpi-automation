"""Corporate dashboard routes."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from yem_sistem.db.session import get_session
from yem_sistem.analysis.models import MaterialAnalysisResult
from yem_sistem.materials.models import Material
from yem_sistem.production_batches.models import BatchStatus, ProductionBatch
from yem_sistem.stock_movements.models import MovementType, StockMovement

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="src/yem_sistem/web/templates")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    today = date.today()

    signed_quantity = case(
        (StockMovement.movement_type == MovementType.IN, StockMovement.quantity),
        (StockMovement.movement_type == MovementType.OUT_PRODUCTION, -StockMovement.quantity),
        (StockMovement.movement_type == MovementType.OUT_CORRECTION, -StockMovement.quantity),
        (StockMovement.movement_type == MovementType.ADJUSTMENT, StockMovement.quantity),
        else_=Decimal("0.000"),
    )

    stock_rows = session.execute(
        select(
            Material.name.label("material_name"),
            func.coalesce(func.sum(signed_quantity), Decimal("0.000")).label("current_stock_kg"),
        )
        .select_from(Material)
        .outerjoin(StockMovement, StockMovement.material_id == Material.id)
        .group_by(Material.id, Material.name)
        .order_by(Material.name.asc())
    ).all()

    total_stock = sum((row.current_stock_kg for row in stock_rows), start=Decimal("0.000"))

    today_in = session.execute(
        select(func.coalesce(func.sum(StockMovement.quantity), Decimal("0.000"))).where(
            StockMovement.movement_type == MovementType.IN,
            func.date(StockMovement.movement_at) == today,
        )
    ).scalar_one()

    today_out_production = session.execute(
        select(func.coalesce(func.sum(StockMovement.quantity), Decimal("0.000"))).where(
            StockMovement.movement_type == MovementType.OUT_PRODUCTION,
            func.date(StockMovement.movement_at) == today,
        )
    ).scalar_one()

    today_out_correction = session.execute(
        select(func.coalesce(func.sum(StockMovement.quantity), Decimal("0.000"))).where(
            StockMovement.movement_type == MovementType.OUT_CORRECTION,
            func.date(StockMovement.movement_at) == today,
        )
    ).scalar_one()

    suspicious_batches = session.execute(
        select(func.count(ProductionBatch.id)).where(ProductionBatch.status == BatchStatus.SUSPICIOUS)
    ).scalar_one()

    movement_summary = session.execute(
        select(
            StockMovement.movement_type.label("movement_type"),
            func.coalesce(func.sum(StockMovement.quantity), Decimal("0.000")).label("total_kg"),
        )
        .where(func.date(StockMovement.movement_at) == today)
        .group_by(StockMovement.movement_type)
        .order_by(StockMovement.movement_type.asc())
    ).all()


    analysis_rows = session.execute(
        select(MaterialAnalysisResult, Material.name)
        .join(Material, Material.id == MaterialAnalysisResult.material_id)
        .order_by(MaterialAnalysisResult.date.desc(), MaterialAnalysisResult.entered_at.desc())
        .limit(100)
    ).all()

    alerts: list[dict[str, str]] = []
    for analysis, material_name in analysis_rows:
        if analysis.aflatoksin_ppb is not None and analysis.aflatoksin_ppb >= Decimal("20"):
            alerts.append(
                {
                    "date": str(analysis.date),
                    "material": material_name,
                    "type": analysis.analysis_type.value,
                    "reason": "Aflatoksin",
                    "value": str(analysis.aflatoksin_ppb),
                    "severity": "RED",
                }
            )
        if analysis.sartoris_nem is not None and analysis.sartoris_nem >= Decimal("15"):
            alerts.append(
                {
                    "date": str(analysis.date),
                    "material": material_name,
                    "type": analysis.analysis_type.value,
                    "reason": "Sartoris Nem",
                    "value": str(analysis.sartoris_nem),
                    "severity": "YELLOW",
                }
            )
        if analysis.yabanci_madde is not None and analysis.yabanci_madde.value == "VAR":
            alerts.append(
                {
                    "date": str(analysis.date),
                    "material": material_name,
                    "type": analysis.analysis_type.value,
                    "reason": "Yabancı Madde",
                    "value": "VAR",
                    "severity": "YELLOW",
                }
            )
        if analysis.tozluluk is not None and analysis.tozluluk.value == "COK":
            alerts.append(
                {
                    "date": str(analysis.date),
                    "material": material_name,
                    "type": analysis.analysis_type.value,
                    "reason": "Tozluluk",
                    "value": "COK",
                    "severity": "YELLOW",
                }
            )
        if len(alerts) >= 10:
            break

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "today": today,
            "total_stock": total_stock,
            "today_in": today_in,
            "today_out_production": today_out_production,
            "today_out_correction": today_out_correction,
            "suspicious_batches": suspicious_batches,
            "stock_rows": stock_rows,
            "movement_summary": movement_summary,
            "alerts": alerts[:10],
        },
    )
